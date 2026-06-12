// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.pdf

import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import java.io.File
import java.io.FileOutputStream

/**
 * Rendert den Protokoll-Markdown-Text als PDF — das Android-Pendant zu
 * save_protocol_as_pdf() in transcript_store.py (dort mit ReportLab).
 *
 * Unterstützt: ##/### Überschriften, --- Trennlinien, - Aufzählungen
 * und **fett** im Fließtext. Mehr erzeugt der Protokoll-Prompt nicht.
 */
object ProtocolPdf {

    private const val PAGE_WIDTH = 595 // A4 in PDF-Punkten
    private const val PAGE_HEIGHT = 842
    private const val MARGIN = 57f // ≈ 2 cm

    fun write(text: String, outFile: File) {
        val doc = PdfDocument()
        val writer = PageWriter(doc)

        for (raw in text.split("\n")) {
            val line = raw.trim()
            when {
                line.isEmpty() -> writer.space(5f)
                line.startsWith("## ") -> writer.heading(line.removePrefix("## ").trim(), 15f)
                line.startsWith("### ") -> writer.heading(line.removePrefix("### ").trim(), 12f)
                line == "---" -> writer.rule()
                line.startsWith("- ") -> writer.text(line.removePrefix("- ").trim(), bullet = true)
                else -> writer.text(line)
            }
        }

        writer.finish()
        FileOutputStream(outFile).use { doc.writeTo(it) }
        doc.close()
    }

    private data class Run(val text: String, val bold: Boolean)

    /** Zerlegt eine Zeile an **…**-Markern in normale und fette Abschnitte. */
    private fun parseRuns(line: String): List<Run> =
        line.split("**").mapIndexedNotNull { i, part ->
            if (part.isEmpty()) null else Run(part, i % 2 == 1)
        }

    private class PageWriter(private val doc: PdfDocument) {
        private var pageNumber = 0
        private var page = newPage()
        private var y = MARGIN

        private fun newPage(): PdfDocument.Page {
            pageNumber += 1
            return doc.startPage(
                PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageNumber).create(),
            )
        }

        private fun paint(size: Float, bold: Boolean) = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = size
            color = Color.parseColor("#111827")
            typeface = Typeface.create(
                Typeface.SANS_SERIF,
                if (bold) Typeface.BOLD else Typeface.NORMAL,
            )
        }

        /** Seitenumbruch, falls *height* nicht mehr auf die Seite passt. */
        private fun ensure(height: Float) {
            if (y + height > PAGE_HEIGHT - MARGIN) {
                doc.finishPage(page)
                page = newPage()
                y = MARGIN
            }
        }

        fun space(points: Float) {
            y += points
        }

        fun heading(text: String, size: Float) {
            y += if (size >= 14f) 4f else 8f
            draw(listOf(Run(text, true)), size, spaceAfter = 4f)
        }

        fun rule() {
            ensure(10f)
            val linePaint = Paint().apply {
                color = Color.parseColor("#D1D5DB")
                strokeWidth = 0.5f
            }
            page.canvas.drawLine(MARGIN, y + 5f, PAGE_WIDTH - MARGIN, y + 5f, linePaint)
            y += 10f
        }

        fun text(line: String, bullet: Boolean = false) {
            draw(parseRuns(line), 10f, indent = if (bullet) 14f else 0f, bullet = bullet)
        }

        /** Zeichnet Runs mit Zeilenumbruch; fette und normale Wörter gemischt. */
        private fun draw(
            runs: List<Run>,
            size: Float,
            indent: Float = 0f,
            bullet: Boolean = false,
            spaceAfter: Float = 3f,
        ) {
            val normalPaint = paint(size, bold = false)
            val boldPaint = paint(size, bold = true)
            val lineHeight = size * 1.4f
            val maxWidth = PAGE_WIDTH - 2 * MARGIN - indent

            data class Word(val text: String, val bold: Boolean)

            val words = runs.flatMap { run ->
                run.text.split(" ").filter { it.isNotBlank() }.map { Word(it, run.bold) }
            }
            if (words.isEmpty()) {
                y += lineHeight
                return
            }

            var first = true
            var i = 0
            while (i < words.size) {
                var lineWidth = 0f
                val lineWords = mutableListOf<Word>()
                while (i < words.size) {
                    val word = words[i]
                    val wordPaint = if (word.bold) boldPaint else normalPaint
                    val wordText = if (lineWords.isEmpty()) word.text else " " + word.text
                    val width = wordPaint.measureText(wordText)
                    if (lineWords.isNotEmpty() && lineWidth + width > maxWidth) break
                    lineWidth += width
                    lineWords.add(word)
                    i++
                }

                ensure(lineHeight)
                val baseline = y + size
                if (first && bullet) {
                    page.canvas.drawText("•", MARGIN + 2f, baseline, normalPaint)
                }
                var x = MARGIN + indent
                lineWords.forEachIndexed { idx, word ->
                    val wordPaint = if (word.bold) boldPaint else normalPaint
                    val wordText = if (idx == 0) word.text else " " + word.text
                    page.canvas.drawText(wordText, x, baseline, wordPaint)
                    x += wordPaint.measureText(wordText)
                }
                y += lineHeight
                first = false
            }
            y += spaceAfter
        }

        fun finish() {
            doc.finishPage(page)
        }
    }
}
