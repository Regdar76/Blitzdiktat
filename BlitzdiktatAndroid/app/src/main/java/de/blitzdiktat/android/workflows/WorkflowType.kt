// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.workflows

/** Spiegelt die Workflows der Windows-App (base_workflow.py). */
enum class WorkflowType(
    val displayName: String,
    val subtitle: String,
    val emoji: String,
    val needsApiKey: Boolean,
) {
    TRANSCRIPTION("Blitzdiktat", "Sprache rein. Text raus.", "🎙️", false),
    TEXT_IMPROVER("Blitzdiktat+", "Geschrieben sprechen.", "✨", true),
    DAMPF_ABLASSEN("Blitzdiktat $%&!", "Frust rein. Entspannt raus.", "🔥", true),
    EMOJI_TEXT("Blitzdiktat :)", "Text rein. Emojis dazu.", "😊", true),
    PROTOKOLL("Blitzdiktat Protokoll", "Besprechung rein. Protokoll raus.", "📋", true),
}
