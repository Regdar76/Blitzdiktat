// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.llm

import android.content.Context
import de.blitzdiktat.android.data.AppSettings
import de.blitzdiktat.android.data.VocabularyStore
import de.blitzdiktat.android.workflows.WorkflowType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class LlmException(message: String) : Exception(message)

/** OpenAI Chat Completions — Pendant zu llm_service.py der Windows-App. */
object OpenAiClient {

    private const val ENDPOINT = "https://api.openai.com/v1/chat/completions"
    private val JSON_TYPE = "application/json; charset=utf-8".toMediaType()

    private val http = OkHttpClient.Builder()
        .callTimeout(60, TimeUnit.SECONDS)
        .connectTimeout(15, TimeUnit.SECONDS)
        .build()

    /** Führt den LLM-Schritt eines Workflows aus (TRANSCRIPTION hat keinen). */
    suspend fun runWorkflow(context: Context, type: WorkflowType, text: String): String {
        return when (type) {
            WorkflowType.TRANSCRIPTION -> text
            WorkflowType.TEXT_IMPROVER -> complete(
                context,
                systemPrompt(context, type) { Prompts.improvement(AppSettings.tone(context)) } +
                    Prompts.vocabularyHint(allTerms(context)),
                text,
                AppSettings.modelFast(context), 0.3,
            )
            WorkflowType.DAMPF_ABLASSEN -> complete(
                context, systemPrompt(context, type) { Prompts.DAMPF_ABLASSEN }, text,
                AppSettings.modelQuality(context), 0.4,
            )
            WorkflowType.EMOJI_TEXT -> complete(
                context, Prompts.emoji(AppSettings.emojiDensity(context)), text,
                AppSettings.modelFast(context), 0.3,
            )
            WorkflowType.PROTOKOLL -> {
                // Aufnahmedatum mitgeben, damit das Modell das Datumsfeld füllen und
                // relative Zeitangaben in konkrete Termine umrechnen kann.
                val fmt = java.text.SimpleDateFormat("EEEE, dd.MM.yyyy", java.util.Locale.GERMAN)
                val dated = "Aufnahmedatum: ${fmt.format(java.util.Date())}\n\n$text"
                // Windows gibt das Vokabular der Whisper-Transkription mit; die
                // Geräte-Erkennung von Android kann das nicht — daher hier im Prompt.
                complete(
                    context,
                    systemPrompt(context, type) { Prompts.PROTOKOLL } +
                        Prompts.vocabularyHint(allTerms(context)),
                    dated,
                    AppSettings.modelQuality(context), 0.2,
                )
            }
        }
    }

    /**
     * Extrahiert Eigennamen/Fachbegriffe aus einem Ergebnis (Hintergrund-Lernen) —
     * Pendant zu llm_service.extract_terms() der Windows-App.
     */
    suspend fun extractTerms(context: Context, text: String): List<String> = try {
        val raw = complete(context, EXTRACT_TERMS_PROMPT, text, AppSettings.modelFast(context), 0.0)
        val arr = JSONArray(raw)
        (0 until arr.length()).mapNotNull { i ->
            (arr.opt(i) as? String)?.trim()?.ifEmpty { null }
        }
    } catch (e: Exception) {
        emptyList()
    }

    private const val EXTRACT_TERMS_PROMPT =
        "Extrahiere alle Eigennamen, Firmennamen, Produktnamen, Ortsnamen und Fachbegriffe " +
            "aus dem folgenden Text. Gib NUR eine JSON-Liste von Strings zurück, z. B. " +
            "[\"OpenAI\", \"München\", \"Bauprojekt Nord\"]. " +
            "Keine Erklärungen. Wenn keine relevanten Begriffe vorhanden sind, gib [] zurück."

    /** Manuelle + gelernte Begriffe, dedupliziert (manuelle zuerst, wie Windows). */
    private fun allTerms(context: Context): List<String> =
        (AppSettings.customTerms(context) + VocabularyStore.learnedTerms(VocabularyStore.file(context)))
            .distinctBy { it.lowercase() }

    /** Eigener System-Prompt aus den Einstellungen, sonst der eingebaute (wie Windows). */
    private inline fun systemPrompt(
        context: Context,
        type: WorkflowType,
        default: () -> String,
    ): String = AppSettings.customPrompt(context, type).ifEmpty(default)

    private suspend fun complete(
        context: Context,
        systemPrompt: String,
        userText: String,
        model: String,
        temperature: Double,
    ): String = withContext(Dispatchers.IO) {
        val apiKey = AppSettings.apiKey(context)
        if (apiKey.isEmpty()) {
            throw LlmException("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")
        }

        val body = JSONObject()
            .put("model", model)
            .put("temperature", temperature)
            .put(
                "messages",
                JSONArray()
                    .put(JSONObject().put("role", "system").put("content", systemPrompt))
                    .put(JSONObject().put("role", "user").put("content", userText)),
            )

        val request = Request.Builder()
            .url(ENDPOINT)
            .header("Authorization", "Bearer $apiKey")
            .post(body.toString().toRequestBody(JSON_TYPE))
            .build()

        val response = try {
            http.newCall(request).execute()
        } catch (e: Exception) {
            throw LlmException("Keine Verbindung zu OpenAI: ${e.message}")
        }

        response.use { resp ->
            val payload = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) {
                val detail = runCatching {
                    JSONObject(payload).getJSONObject("error").getString("message")
                }.getOrDefault(payload.take(200))
                throw LlmException(
                    when (resp.code) {
                        401 -> "API Key ungültig. Bitte in den Einstellungen prüfen."
                        429 -> "Rate-Limit oder Kontingent erschöpft. Bitte später erneut versuchen."
                        else -> "OpenAI-Fehler (${resp.code}): $detail"
                    },
                )
            }
            val content = runCatching {
                JSONObject(payload)
                    .getJSONArray("choices").getJSONObject(0)
                    .getJSONObject("message").getString("content")
            }.getOrNull()?.trim()
            if (content.isNullOrEmpty()) {
                throw LlmException("Keine Antwort erhalten. Bitte nochmal versuchen.")
            }
            content
        }
    }
}
