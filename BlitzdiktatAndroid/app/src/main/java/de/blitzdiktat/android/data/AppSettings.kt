// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.data

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import de.blitzdiktat.android.workflows.WorkflowType

/**
 * App-Einstellungen. Der OpenAI-Key liegt in EncryptedSharedPreferences
 * (AES, Schlüssel im Android Keystore) — das Pendant zum Windows
 * Credential Manager der Desktop-App.
 */
object AppSettings {

    const val DEFAULT_MODEL_FAST = "gpt-4o-mini"
    const val DEFAULT_MODEL_QUALITY = "gpt-4o"
    const val DEFAULT_DICTATION_LANGUAGE = "de-DE"

    private const val PREFS = "blitzdiktat_secure"
    private const val KEY_API = "openai_api_key"
    private const val KEY_MODEL_FAST = "openai_model_fast"
    private const val KEY_MODEL_QUALITY = "openai_model_quality"
    private const val KEY_TONE = "tone"
    private const val KEY_EMOJI_DENSITY = "emoji_density"
    private const val KEY_DICTATION_LANGUAGE = "dictation_language"
    private const val KEY_PREFIX_CUSTOM_NAME = "custom_name_"
    private const val KEY_PREFIX_CUSTOM_PROMPT = "custom_prompt_"
    private const val KEY_CUSTOM_TERMS = "custom_terms"

    @Volatile
    private var prefs: SharedPreferences? = null

    private fun prefs(context: Context): SharedPreferences {
        prefs?.let { return it }
        synchronized(this) {
            prefs?.let { return it }
            val masterKey = MasterKey.Builder(context.applicationContext)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()
            val created = EncryptedSharedPreferences.create(
                context.applicationContext,
                PREFS,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
            prefs = created
            return created
        }
    }

    fun apiKey(context: Context): String =
        prefs(context).getString(KEY_API, "")?.trim().orEmpty()

    fun setApiKey(context: Context, key: String) =
        prefs(context).edit().putString(KEY_API, key.trim()).apply()

    fun isConfigured(context: Context): Boolean = apiKey(context).isNotEmpty()

    /** Gespeicherter Override ohne Default-Fallback (für die Einstellungs-UI). */
    fun modelFastOverride(context: Context): String =
        prefs(context).getString(KEY_MODEL_FAST, "")?.trim().orEmpty()

    fun modelQualityOverride(context: Context): String =
        prefs(context).getString(KEY_MODEL_QUALITY, "")?.trim().orEmpty()

    fun modelFast(context: Context): String =
        modelFastOverride(context).ifEmpty { DEFAULT_MODEL_FAST }

    fun modelQuality(context: Context): String =
        modelQualityOverride(context).ifEmpty { DEFAULT_MODEL_QUALITY }

    fun setModels(context: Context, fast: String, quality: String) =
        prefs(context).edit()
            .putString(KEY_MODEL_FAST, fast.trim())
            .putString(KEY_MODEL_QUALITY, quality.trim())
            .apply()

    /** formal | neutral | casual */
    fun tone(context: Context): String =
        prefs(context).getString(KEY_TONE, "neutral") ?: "neutral"

    fun setTone(context: Context, tone: String) =
        prefs(context).edit().putString(KEY_TONE, tone).apply()

    /** wenig | mittel | viel */
    fun emojiDensity(context: Context): String =
        prefs(context).getString(KEY_EMOJI_DENSITY, "mittel") ?: "mittel"

    fun setEmojiDensity(context: Context, density: String) =
        prefs(context).edit().putString(KEY_EMOJI_DENSITY, density).apply()

    /** BCP-47-Tag für die Spracherkennung, z. B. "de-DE". */
    fun dictationLanguage(context: Context): String =
        prefs(context).getString(KEY_DICTATION_LANGUAGE, "")?.trim().orEmpty()
            .ifEmpty { DEFAULT_DICTATION_LANGUAGE }

    fun setDictationLanguage(context: Context, language: String) =
        prefs(context).edit().putString(KEY_DICTATION_LANGUAGE, language.trim()).apply()

    /**
     * Manuell gepflegte Eigennamen/Fachbegriffe — das Pendant zu
     * custom_terms der Windows-App. Zeilenweise gespeichert.
     */
    fun customTerms(context: Context): List<String> =
        prefs(context).getString(KEY_CUSTOM_TERMS, "")
            ?.split('\n')
            ?.map { it.trim() }
            ?.filter { it.isNotEmpty() }
            ?: emptyList()

    fun setCustomTerms(context: Context, terms: List<String>) =
        prefs(context).edit()
            .putString(KEY_CUSTOM_TERMS, terms.map { it.trim() }.filter { it.isNotEmpty() }.joinToString("\n"))
            .apply()

    // ── Workflow-Anpassung (eigene Namen und System-Prompts, wie Windows) ──

    fun customName(context: Context, type: WorkflowType): String =
        prefs(context).getString(KEY_PREFIX_CUSTOM_NAME + type.name, "")?.trim().orEmpty()

    fun setCustomName(context: Context, type: WorkflowType, name: String) =
        prefs(context).edit().putString(KEY_PREFIX_CUSTOM_NAME + type.name, name.trim()).apply()

    /** Anzeigename: eigener Name falls gesetzt, sonst der eingebaute. */
    fun displayName(context: Context, type: WorkflowType): String =
        customName(context, type).ifEmpty { type.displayName }

    fun customPrompt(context: Context, type: WorkflowType): String =
        prefs(context).getString(KEY_PREFIX_CUSTOM_PROMPT + type.name, "")?.trim().orEmpty()

    fun setCustomPrompt(context: Context, type: WorkflowType, prompt: String) =
        prefs(context).edit().putString(KEY_PREFIX_CUSTOM_PROMPT + type.name, prompt.trim()).apply()

    fun maskedKey(context: Context): String {
        val key = apiKey(context)
        return when {
            key.isEmpty() -> ""
            key.length > 8 -> key.take(4) + " ••••••••"
            else -> "••••••••"
        }
    }
}
