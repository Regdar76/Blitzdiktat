// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.workflows

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WorkflowTypeTest {

    @Test
    fun onlyPlainDictationWorksWithoutApiKey() {
        assertFalse(WorkflowType.TRANSCRIPTION.needsApiKey)
        WorkflowType.entries.filter { it != WorkflowType.TRANSCRIPTION }.forEach {
            assertTrue("${it.name} braucht einen API-Key", it.needsApiKey)
        }
    }

    @Test
    fun mirrorsTheFiveWindowsWorkflows() {
        assertEquals(5, WorkflowType.entries.size)
        assertEquals("Blitzdiktat", WorkflowType.TRANSCRIPTION.displayName)
        assertEquals("Blitzdiktat Protokoll", WorkflowType.PROTOKOLL.displayName)
    }
}
