// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.data

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Speichert Workflow-Ergebnisse lokal als .txt-Dateien und bereinigt alte
 * Einträge — das Pendant zu transcript_store.py der Windows-App.
 *
 * Die Kernfunktionen arbeiten auf einem Verzeichnis statt auf dem Context,
 * damit sie in JVM-Unit-Tests ohne Android-Laufzeit laufen.
 */
object TranscriptStore {

    const val MAX_AGE_DAYS = 14
    private const val FOLDER = "Transkriptionen"
    private const val HEADER_SEPARATOR = "----------------------------------------"

    data class Entry(
        val file: File,
        val workflowName: String,
        val savedAt: Date,
        val text: String,
        /** Zugehörige PDF (nur Protokoll), falls vorhanden. */
        val pdf: File?,
    )

    fun dir(context: Context): File =
        File(context.filesDir, FOLDER).apply { mkdirs() }

    /**
     * Speichert *text* mit Datums-/Workflow-Kopfzeile als .txt-Datei.
     * Gibt die geschriebene Datei zurück.
     */
    fun saveTranscript(dir: File, text: String, workflowName: String, now: Date = Date()): File {
        val ts = SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.US).format(now)
        var file = File(dir, "blitzdiktat_$ts.txt")
        var suffix = 1
        while (file.exists()) {
            file = File(dir, "blitzdiktat_$ts-${suffix++}.txt")
        }

        val header = buildString {
            append("Datum: ")
            append(SimpleDateFormat("dd.MM.yyyy HH:mm:ss", Locale.GERMAN).format(now))
            append('\n')
            if (workflowName.isNotBlank()) append("Workflow: $workflowName\n")
            append(HEADER_SEPARATOR)
            append("\n\n")
        }
        file.writeText(header + text)
        return file
    }

    /** Alle gespeicherten Einträge, neueste zuerst. */
    fun list(dir: File): List<Entry> =
        (dir.listFiles() ?: emptyArray())
            .filter { it.isFile && it.name.endsWith(".txt") }
            .mapNotNull { parse(it) }
            .sortedByDescending { it.savedAt }

    /** Löscht .txt-/.pdf-Dateien, die älter als MAX_AGE_DAYS sind. Gibt die Anzahl zurück. */
    fun cleanup(dir: File, now: Long = System.currentTimeMillis()): Int {
        val cutoff = now - MAX_AGE_DAYS * 86_400_000L
        var removed = 0
        (dir.listFiles() ?: emptyArray())
            .filter { it.isFile && (it.name.endsWith(".txt") || it.name.endsWith(".pdf")) }
            .forEach { file ->
                if (file.lastModified() < cutoff && file.delete()) removed++
            }
        return removed
    }

    /** Löscht einen Eintrag samt zugehöriger PDF. */
    fun delete(entry: Entry) {
        entry.file.delete()
        entry.pdf?.delete()
    }

    private fun parse(file: File): Entry? {
        val content = runCatching { file.readText() }.getOrNull() ?: return null
        var workflowName = ""
        var body = content

        val sepIndex = content.indexOf(HEADER_SEPARATOR)
        if (sepIndex >= 0) {
            content.substring(0, sepIndex).lines().forEach { line ->
                if (line.startsWith("Workflow: ")) {
                    workflowName = line.removePrefix("Workflow: ").trim()
                }
            }
            body = content.substring(sepIndex + HEADER_SEPARATOR.length).trimStart('\n')
        }

        val pdf = File(file.parentFile, file.nameWithoutExtension + ".pdf")
            .takeIf { it.exists() }

        return Entry(
            file = file,
            workflowName = workflowName,
            savedAt = Date(file.lastModified()),
            text = body,
            pdf = pdf,
        )
    }
}
