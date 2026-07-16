// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.data

import android.content.Context
import java.io.File

/**
 * Persistentes, automatisch gelerntes Vokabular — das Pendant zu
 * vocabulary_service.py der Windows-App: case-insensitive dedupliziert,
 * maximal [MAX_TERMS] Einträge (die ältesten fliegen zuerst raus).
 *
 * Gespeichert als eine Zeile pro Begriff in filesDir/vocabulary.txt.
 * Die Kernfunktionen arbeiten auf einer Datei statt auf dem Context,
 * damit sie in JVM-Unit-Tests laufen.
 */
object VocabularyStore {

    const val MAX_TERMS = 150

    fun file(context: Context): File = File(context.filesDir, "vocabulary.txt")

    fun learnedTerms(file: File): List<String> {
        if (!file.exists()) return emptyList()
        return runCatching {
            file.readLines().map { it.trim() }.filter { it.isNotEmpty() }
        }.getOrDefault(emptyList())
    }

    /**
     * Fügt neue Begriffe hinzu (dedupliziert, gekappt). Gibt die Anzahl neuer Begriffe zurück.
     *
     * @Synchronized: IME-Service und ViewModel lernen parallel auf
     * Dispatchers.IO — ohne Lock verlor das Read-Modify-Write Begriffe
     * (Lost Update).
     */
    @Synchronized
    fun addTerms(file: File, terms: List<String>): Int {
        if (terms.isEmpty()) return 0
        val existing = learnedTerms(file)
        val seen = existing.map { it.lowercase() }.toMutableSet()
        val newTerms = terms
            .mapNotNull { it.trim().ifEmpty { null } }
            .filter { seen.add(it.lowercase()) }
        if (newTerms.isEmpty()) return 0

        var merged = existing + newTerms
        if (merged.size > MAX_TERMS) merged = merged.takeLast(MAX_TERMS)
        write(file, merged)
        return newTerms.size
    }

    @Synchronized
    fun removeTerm(file: File, term: String) {
        write(file, learnedTerms(file).filterNot { it.equals(term, ignoreCase = true) })
    }

    @Synchronized
    fun clear(file: File) {
        write(file, emptyList())
    }

    private fun write(file: File, terms: List<String>) {
        runCatching { file.writeText(terms.joinToString("\n")) }
    }
}
