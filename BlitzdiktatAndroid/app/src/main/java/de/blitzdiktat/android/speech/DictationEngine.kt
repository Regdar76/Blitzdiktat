// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.speech

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Diktat über die Spracherkennung von Android (SpeechRecognizer).
 *
 * Erst wird offline erkannt (EXTRA_PREFER_OFFLINE) — privat, ohne API-Key.
 * Liefert die Offline-Erkennung jedoch kein Ergebnis (z. B. weil auf dem Gerät
 * kein deutsches Offline-Sprachpaket installiert ist — häufig bei Xiaomi/MIUI),
 * wird automatisch einmal online nachversucht, statt nur "Keine Aufnahme
 * erkannt" zu melden. Im Online-Fallback verlässt das Audio das Gerät (Google).
 *
 * continuous = true (Protokoll-Modus): nach jedem finalen Ergebnis wird die
 * Erkennung automatisch neu gestartet, bis stop() aufgerufen wird — so lassen
 * sich längere Besprechungen am Stück aufnehmen.
 */
class DictationEngine(private val context: Context) {

    interface Listener {
        fun onPartial(text: String)
        /** Ein finales Segment. accumulated = alles bisher Erkannte. */
        fun onSegment(segment: String, accumulated: String)
        /** Erkennung komplett beendet (nach stop() oder Fehler). */
        fun onFinished(accumulated: String)
        fun onError(message: String)
        fun onRms(rms: Float)
    }

    private var recognizer: SpeechRecognizer? = null
    private var listener: Listener? = null
    private var continuous = false
    private var stopping = false
    private var language = "de-DE"
    // Erst offline versuchen; nach einem ergebnislosen Offline-Versuch wird auf
    // false geschaltet und online nachversucht.
    private var preferOffline = true
    private val segments = mutableListOf<String>()

    val isActive: Boolean get() = recognizer != null

    fun start(listener: Listener, continuous: Boolean = false, language: String = "de-DE") {
        if (recognizer != null) return
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            listener.onError("Keine Spracherkennung auf diesem Gerät verfügbar.")
            return
        }
        this.listener = listener
        this.continuous = continuous
        this.stopping = false
        this.language = language
        this.preferOffline = true
        segments.clear()

        val rec = SpeechRecognizer.createSpeechRecognizer(context)
        recognizer = rec
        rec.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {}
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {
                this@DictationEngine.listener?.onRms(rmsdB)
            }

            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}

            override fun onError(error: Int) {
                // Fehlercodes, die "offline nicht möglich / nichts erkannt" bedeuten.
                val noResult = error == SpeechRecognizer.ERROR_NO_MATCH ||
                    error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT ||
                    error == SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE ||
                    error == SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED
                when {
                    // Offline lieferte (noch) nichts → einmalig online nachversuchen.
                    // Greift bei fehlendem Offline-Sprachpaket (häufig auf MIUI).
                    !stopping && preferOffline && noResult && segments.isEmpty() -> {
                        preferOffline = false
                        restart()
                    }

                    // Stille/kein Treffer: im Protokoll-Modus einfach weiterlauschen
                    !stopping && continuous &&
                        (error == SpeechRecognizer.ERROR_NO_MATCH ||
                            error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) -> restart()

                    error == SpeechRecognizer.ERROR_NO_MATCH ||
                        error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> finish()

                    error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> {
                        this@DictationEngine.listener?.onError("Mikrofon-Berechtigung fehlt.")
                        cleanup()
                    }

                    else -> {
                        if (!stopping) {
                            this@DictationEngine.listener?.onError("Spracherkennung fehlgeschlagen (Code $error).")
                        }
                        finish()
                    }
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val text = partialResults
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                if (!text.isNullOrBlank()) {
                    this@DictationEngine.listener?.onPartial(text)
                }
            }

            override fun onResults(results: Bundle?) {
                val text = results
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                    ?.trim()
                if (!text.isNullOrEmpty()) {
                    segments.add(text)
                    this@DictationEngine.listener?.onSegment(text, accumulated())
                } else if (!stopping && preferOffline && segments.isEmpty()) {
                    // Offline lieferte ein leeres Ergebnis → einmalig online nachversuchen.
                    preferOffline = false
                    restart()
                    return
                }
                if (continuous && !stopping) restart() else finish()
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
        rec.startListening(buildIntent())
    }

    /** Beendet die Aufnahme; das letzte Segment wird noch verarbeitet. */
    fun stop() {
        stopping = true
        recognizer?.stopListening()
    }

    /** Bricht sofort ab, ohne Ergebnis. */
    fun cancel() {
        stopping = true
        cleanup()
    }

    private fun accumulated(): String = segments.joinToString(" ").trim()

    private fun restart() {
        recognizer?.startListening(buildIntent())
    }

    private fun finish() {
        val result = accumulated()
        cleanup()
        listener?.onFinished(result)
    }

    private fun cleanup() {
        recognizer?.destroy()
        recognizer = null
    }

    private fun buildIntent(): Intent =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            // Erst offline (privat); nach ergebnislosem Offline-Versuch online.
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, preferOffline)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
            // Großzügige Stille-Timeouts, damit der Recognizer bei kurzen
            // Denkpausen nicht sofort abschließt. Es sind Best-Effort-Hinweise
            // (Google deckelt sie oft) — der eigentliche „nur manuell stoppen"-
            // Effekt kommt aus dem continuous-Neustart in onResults/onError.
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 6000)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 8000)
            putExtra(
                RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS,
                8000,
            )
        }
}
