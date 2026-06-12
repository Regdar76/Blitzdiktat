// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.util.Date

class TranscriptStoreTest {

    @Rule
    @JvmField
    val tmp = TemporaryFolder()

    @Test
    fun saveAndListRoundtrip() {
        val dir = tmp.newFolder()
        TranscriptStore.saveTranscript(dir, "Hallo Welt.\nZweite Zeile.", "Blitzdiktat+")

        val entries = TranscriptStore.list(dir)
        assertEquals(1, entries.size)
        assertEquals("Blitzdiktat+", entries[0].workflowName)
        assertEquals("Hallo Welt.\nZweite Zeile.", entries[0].text)
    }

    @Test
    fun saveWithoutWorkflowNameOmitsHeaderLine() {
        val dir = tmp.newFolder()
        TranscriptStore.saveTranscript(dir, "Nur Text", "")

        val entries = TranscriptStore.list(dir)
        assertEquals(1, entries.size)
        assertEquals("", entries[0].workflowName)
        assertEquals("Nur Text", entries[0].text)
    }

    @Test
    fun sameTimestampGetsUniqueFilenames() {
        val dir = tmp.newFolder()
        val now = Date()
        val first = TranscriptStore.saveTranscript(dir, "eins", "X", now)
        val second = TranscriptStore.saveTranscript(dir, "zwei", "X", now)

        assertNotEquals(first.name, second.name)
        assertEquals(2, TranscriptStore.list(dir).size)
    }

    @Test
    fun cleanupDeletesOnlyOldFiles() {
        val dir = tmp.newFolder()
        val old = TranscriptStore.saveTranscript(dir, "alt", "X")
        val oldPdf = File(dir, old.nameWithoutExtension + ".pdf").apply { writeText("pdf") }
        val recent = TranscriptStore.saveTranscript(dir, "neu", "X")

        val tooOld = System.currentTimeMillis() - (TranscriptStore.MAX_AGE_DAYS + 1) * 86_400_000L
        old.setLastModified(tooOld)
        oldPdf.setLastModified(tooOld)

        val removed = TranscriptStore.cleanup(dir)

        assertEquals(2, removed)
        assertTrue(!old.exists() && !oldPdf.exists())
        assertTrue(recent.exists())
    }

    @Test
    fun listPairsPdfWithSameBasename() {
        val dir = tmp.newFolder()
        val txt = TranscriptStore.saveTranscript(dir, "Protokolltext", "Blitzdiktat Protokoll")
        val pdf = File(dir, txt.nameWithoutExtension + ".pdf").apply { writeText("pdf") }

        val entries = TranscriptStore.list(dir)
        assertEquals(1, entries.size)
        assertEquals(pdf, entries[0].pdf)
    }

    @Test
    fun deleteRemovesTxtAndPdf() {
        val dir = tmp.newFolder()
        val txt = TranscriptStore.saveTranscript(dir, "Protokolltext", "Blitzdiktat Protokoll")
        val pdf = File(dir, txt.nameWithoutExtension + ".pdf").apply { writeText("pdf") }

        TranscriptStore.delete(TranscriptStore.list(dir).single())

        assertTrue(!txt.exists() && !pdf.exists())
        assertTrue(TranscriptStore.list(dir).isEmpty())
    }
}
