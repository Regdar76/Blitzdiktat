// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class VocabularyStoreTest {

    @Rule
    @JvmField
    val tmp = TemporaryFolder()

    private fun vocabFile(): File = File(tmp.root, "vocabulary.txt")

    @Test
    fun addAndReadRoundtrip() {
        val file = vocabFile()
        val added = VocabularyStore.addTerms(file, listOf("Karstens", "Bauprojekt Nord"))

        assertEquals(2, added)
        assertEquals(listOf("Karstens", "Bauprojekt Nord"), VocabularyStore.learnedTerms(file))
    }

    @Test
    fun dedupesCaseInsensitive() {
        val file = vocabFile()
        VocabularyStore.addTerms(file, listOf("Karstens"))
        val added = VocabularyStore.addTerms(file, listOf("KARSTENS", "karstens", "Meier"))

        assertEquals(1, added)
        assertEquals(listOf("Karstens", "Meier"), VocabularyStore.learnedTerms(file))
    }

    @Test
    fun ignoresBlankTerms() {
        val file = vocabFile()
        val added = VocabularyStore.addTerms(file, listOf("  ", "", "Meier "))

        assertEquals(1, added)
        assertEquals(listOf("Meier"), VocabularyStore.learnedTerms(file))
    }

    @Test
    fun capsAtMaxTermsKeepingNewest() {
        val file = vocabFile()
        VocabularyStore.addTerms(file, (1..VocabularyStore.MAX_TERMS).map { "Begriff$it" })
        VocabularyStore.addTerms(file, listOf("Neuester"))

        val terms = VocabularyStore.learnedTerms(file)
        assertEquals(VocabularyStore.MAX_TERMS, terms.size)
        assertEquals("Neuester", terms.last())
        assertTrue("Ältester Begriff muss verdrängt sein", "Begriff1" !in terms)
    }

    @Test
    fun removeTermIsCaseInsensitive() {
        val file = vocabFile()
        VocabularyStore.addTerms(file, listOf("Karstens", "Meier"))
        VocabularyStore.removeTerm(file, "karstens")

        assertEquals(listOf("Meier"), VocabularyStore.learnedTerms(file))
    }

    @Test
    fun clearEmptiesTheStore() {
        val file = vocabFile()
        VocabularyStore.addTerms(file, listOf("Karstens"))
        VocabularyStore.clear(file)

        assertTrue(VocabularyStore.learnedTerms(file).isEmpty())
    }

    @Test
    fun missingFileYieldsEmptyList() {
        assertTrue(VocabularyStore.learnedTerms(vocabFile()).isEmpty())
    }
}
