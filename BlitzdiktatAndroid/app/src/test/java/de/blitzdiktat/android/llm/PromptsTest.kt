// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.llm

import org.junit.Assert.assertTrue
import org.junit.Test

class PromptsTest {

    @Test
    fun improvementUsesRequestedTone() {
        assertTrue(Prompts.improvement("formal").contains("formellen"))
        assertTrue(Prompts.improvement("casual").contains("lockeren"))
        assertTrue(Prompts.improvement("neutral").contains("neutralen"))
    }

    @Test
    fun improvementFallsBackToNeutralForUnknownTone() {
        assertTrue(Prompts.improvement("quatsch").contains("neutralen"))
        assertTrue(Prompts.improvement("").contains("neutralen"))
    }

    @Test
    fun improvementAlwaysDemandsPlainOutput() {
        listOf("formal", "neutral", "casual").forEach { tone ->
            assertTrue(Prompts.improvement(tone).contains("NUR den verbesserten Text"))
        }
    }

    @Test
    fun emojiUsesRequestedDensity() {
        assertTrue(Prompts.emoji("wenig").contains("maximal 1-2 pro Absatz"))
        assertTrue(Prompts.emoji("viel").contains("großzügig"))
        assertTrue(Prompts.emoji("mittel").contains("alle 1-2 Sätze"))
    }

    @Test
    fun emojiFallsBackToMediumForUnknownDensity() {
        assertTrue(Prompts.emoji("quatsch").contains("alle 1-2 Sätze"))
    }

    @Test
    fun protokollContainsCoreRules() {
        // Kernregeln, auf die sich OpenAiClient verlässt (Aufnahmedatum wird vorangestellt)
        assertTrue(Prompts.PROTOKOLL.contains("Aufnahmedatum"))
        assertTrue(Prompts.PROTOKOLL.contains("IMMER auf Deutsch"))
        assertTrue(Prompts.PROTOKOLL.contains("Erfinde keine Inhalte"))
        assertTrue(Prompts.PROTOKOLL.contains("## Protokoll"))
    }
}
