// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import de.blitzdiktat.android.data.AppSettings
import de.blitzdiktat.android.data.TranscriptStore
import de.blitzdiktat.android.data.VocabularyStore
import de.blitzdiktat.android.llm.LlmException
import de.blitzdiktat.android.llm.OpenAiClient
import de.blitzdiktat.android.pdf.ProtocolPdf
import de.blitzdiktat.android.speech.DictationEngine
import de.blitzdiktat.android.workflows.WorkflowType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

enum class Phase { IDLE, RECORDING, PROCESSING, DONE, ERROR }

data class UiState(
    val phase: Phase = Phase.IDLE,
    val activeWorkflow: WorkflowType? = null,
    val statusText: String = "",
    val liveText: String = "",
    val resultText: String = "",
    val errorText: String = "",
    /** Gespeicherte Protokoll-PDF des aktuellen Ergebnisses, falls vorhanden. */
    val pdfFile: File? = null,
)

class AppViewModel(app: Application) : AndroidViewModel(app) {

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    private val _history = MutableStateFlow<List<TranscriptStore.Entry>>(emptyList())
    val history: StateFlow<List<TranscriptStore.Entry>> = _history

    private val engine = DictationEngine(app)

    init {
        // Einträge älter als 14 Tage beim Start bereinigen (wie die Windows-App)
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { TranscriptStore.cleanup(TranscriptStore.dir(app)) }
            refreshHistoryNow()
        }
    }

    /** Klick auf eine Workflow-Karte: startet bzw. stoppt die Aufnahme. */
    fun toggle(type: WorkflowType) {
        val current = _state.value
        if (current.phase == Phase.RECORDING) {
            if (current.activeWorkflow == type) engine.stop() else return
            return
        }
        if (current.phase == Phase.PROCESSING) return

        val ctx = getApplication<Application>()
        if (type.needsApiKey && !AppSettings.isConfigured(ctx)) {
            _state.value = UiState(
                phase = Phase.ERROR,
                activeWorkflow = type,
                errorText = "Für ${AppSettings.displayName(ctx, type)} fehlt der OpenAI API Key. " +
                    "Bitte in den Einstellungen hinterlegen.",
            )
            return
        }

        _state.value = UiState(
            phase = Phase.RECORDING,
            activeWorkflow = type,
            statusText = "Aufnahme läuft … (zum Stoppen erneut tippen)",
        )
        engine.start(
            object : DictationEngine.Listener {
                override fun onPartial(text: String) {
                    _state.value = _state.value.copy(liveText = text)
                }

                override fun onSegment(segment: String, accumulated: String) {
                    _state.value = _state.value.copy(liveText = accumulated)
                }

                override fun onFinished(accumulated: String) {
                    if (accumulated.isBlank()) {
                        _state.value = _state.value.copy(
                            phase = Phase.ERROR,
                            errorText = "Keine Aufnahme erkannt.",
                        )
                        return
                    }
                    process(type, accumulated)
                }

                override fun onError(message: String) {
                    _state.value = _state.value.copy(phase = Phase.ERROR, errorText = message)
                }

                override fun onRms(rms: Float) {}
            },
            continuous = type == WorkflowType.PROTOKOLL,
            language = AppSettings.dictationLanguage(ctx),
        )
    }

    /** Erstellt ein Protokoll aus einer importierten Textdatei (ohne Aufnahme). */
    fun importTextForProtokoll(text: String) {
        val current = _state.value
        if (current.phase == Phase.RECORDING || current.phase == Phase.PROCESSING) return

        val ctx = getApplication<Application>()
        if (!AppSettings.isConfigured(ctx)) {
            _state.value = UiState(
                phase = Phase.ERROR,
                activeWorkflow = WorkflowType.PROTOKOLL,
                errorText = "Für das Protokoll fehlt der OpenAI API Key. " +
                    "Bitte in den Einstellungen hinterlegen.",
            )
            return
        }
        _state.value = UiState(activeWorkflow = WorkflowType.PROTOKOLL)
        process(WorkflowType.PROTOKOLL, text)
    }

    private fun process(type: WorkflowType, text: String) {
        if (type == WorkflowType.TRANSCRIPTION) {
            _state.value = _state.value.copy(
                phase = Phase.DONE, statusText = "Fertig.", resultText = text,
            )
            viewModelScope.launch(Dispatchers.IO) {
                persist(type, text)
                refreshHistoryNow()
            }
            return
        }
        _state.value = _state.value.copy(
            phase = Phase.PROCESSING,
            statusText = "Wird verarbeitet …",
            liveText = text,
        )
        viewModelScope.launch {
            try {
                val result = OpenAiClient.runWorkflow(getApplication(), type, text)
                val pdf = withContext(Dispatchers.IO) {
                    val saved = persist(type, result)
                    refreshHistoryNow()
                    saved
                }
                _state.value = _state.value.copy(
                    phase = Phase.DONE, statusText = "Fertig.", resultText = result, pdfFile = pdf,
                )
                learnVocabularyInBackground(result)
            } catch (e: LlmException) {
                _state.value = _state.value.copy(
                    phase = Phase.ERROR,
                    errorText = e.message ?: "Unbekannter Fehler",
                )
            } catch (e: Exception) {
                _state.value = _state.value.copy(
                    phase = Phase.ERROR,
                    errorText = "Unerwarteter Fehler: ${e.message}",
                )
            }
        }
    }

    /**
     * Extrahiert im Hintergrund Eigennamen/Fachbegriffe aus dem Ergebnis und
     * erweitert das gelernte Vokabular — wie die Windows-App. Läuft nur nach
     * LLM-Workflows (das reine Blitzdiktat ist auf Android immer lokal, dort
     * verlässt wie auf Windows im Lokalmodus nichts das Gerät).
     */
    private fun learnVocabularyInBackground(text: String) {
        val ctx = getApplication<Application>()
        if (!AppSettings.isConfigured(ctx)) return
        viewModelScope.launch(Dispatchers.IO) {
            runCatching {
                val terms = OpenAiClient.extractTerms(ctx, text)
                if (terms.isNotEmpty()) {
                    VocabularyStore.addTerms(VocabularyStore.file(ctx), terms)
                }
            }
        }
    }

    /** Speichert ein Ergebnis als .txt (Protokolle zusätzlich als PDF). */
    private fun persist(type: WorkflowType, text: String): File? = runCatching {
        val dir = TranscriptStore.dir(getApplication())
        val txt = TranscriptStore.saveTranscript(dir, text, type.displayName)
        if (type == WorkflowType.PROTOKOLL) {
            File(dir, txt.nameWithoutExtension + ".pdf").also { ProtocolPdf.write(text, it) }
        } else {
            null
        }
    }.getOrNull()

    fun refreshHistory() {
        viewModelScope.launch(Dispatchers.IO) { refreshHistoryNow() }
    }

    fun deleteEntry(entry: TranscriptStore.Entry) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { TranscriptStore.delete(entry) }
            refreshHistoryNow()
        }
    }

    private fun refreshHistoryNow() {
        _history.value = runCatching {
            TranscriptStore.list(TranscriptStore.dir(getApplication()))
        }.getOrDefault(emptyList())
    }

    fun reset() {
        engine.cancel()
        _state.value = UiState()
    }

    override fun onCleared() {
        engine.cancel()
    }
}
