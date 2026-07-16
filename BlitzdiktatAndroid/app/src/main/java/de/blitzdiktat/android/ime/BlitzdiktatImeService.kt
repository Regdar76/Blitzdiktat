// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.ime

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.inputmethodservice.InputMethodService
import android.os.Build
import android.view.Gravity
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import de.blitzdiktat.android.MainActivity
import de.blitzdiktat.android.data.AppSettings
import de.blitzdiktat.android.data.TranscriptStore
import de.blitzdiktat.android.data.VocabularyStore
import de.blitzdiktat.android.llm.LlmException
import de.blitzdiktat.android.llm.OpenAiClient
import de.blitzdiktat.android.pdf.ProtocolPdf
import de.blitzdiktat.android.speech.DictationEngine
import de.blitzdiktat.android.workflows.WorkflowType
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.io.File

/**
 * Blitzdiktat-Tastatur: Mikro gedrückt halten, sprechen, loslassen — der Text
 * landet direkt im Eingabefeld der aktiven App. Push-to-Talk, das Android-
 * Pendant zum gehaltenen globalen Hotkey der Windows-App.
 */
class BlitzdiktatImeService : InputMethodService() {

    private lateinit var engine: DictationEngine
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private var selectedWorkflow = WorkflowType.TRANSCRIPTION
    private var micButton: Button? = null
    private var statusView: TextView? = null
    private var chipViews: MutableMap<WorkflowType, TextView> = mutableMapOf()

    // Laufender LLM-Auftrag und Zähler der Eingabesitzung. Der OpenAI-Call
    // dauert Sekunden — wechselt der Nutzer währenddessen App oder Feld, darf
    // das Ergebnis nicht mehr über currentInputConnection committet werden
    // (es landet sonst im falschen Eingabefeld, schlimmstenfalls in einer
    // fremden App). Jeder Sitzungswechsel erhöht inputSession.
    private var llmJob: Job? = null
    private var inputSession = 0

    private val bgColor = Color.parseColor("#1E293B")
    private val accentRed = Color.parseColor("#DC2626")
    private val accentBlue = Color.parseColor("#3B82F6")

    override fun onCreate() {
        super.onCreate()
        engine = DictationEngine(this)
    }

    override fun onDestroy() {
        engine.cancel()
        scope.cancel()
        super.onDestroy()
    }

    override fun onStartInputView(editorInfo: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(editorInfo, restarting)
        inputSession++
    }

    override fun onFinishInputView(finishingInput: Boolean) {
        // Tastatur verschwindet bzw. Feld verliert den Fokus: Aufnahme und
        // LLM-Verarbeitung gehören zur alten Sitzung — abbrechen, damit kein
        // Ergebnis zeitversetzt in ein anderes Feld geschrieben wird.
        inputSession++
        llmJob?.cancel()
        llmJob = null
        if (engine.isActive) engine.cancel()
        micButton?.setBackgroundColor(accentBlue)
        super.onFinishInputView(finishingInput)
    }

    override fun onCreateInputView(): View {
        chipViews.clear()

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(bgColor)
            setPadding(dp(10), dp(8), dp(10), dp(10))
        }

        // ── Workflow-Chips ──────────────────────────────────────────────
        val chipRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        WorkflowType.entries.forEach { type ->
            val chip = TextView(this).apply {
                val name = AppSettings.displayName(this@BlitzdiktatImeService, type)
                text = "${type.emoji} ${name.removePrefix("Blitzdiktat").trim().ifEmpty { "Diktat" }}"
                setTextColor(Color.WHITE)
                textSize = 13f
                setPadding(dp(12), dp(6), dp(12), dp(6))
                setOnClickListener { selectWorkflow(type) }
            }
            chipViews[type] = chip
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            ).apply { rightMargin = dp(6) }
            chipRow.addView(chip, lp)
        }
        root.addView(HorizontalScrollView(this).apply {
            isHorizontalScrollBarEnabled = false
            addView(chipRow)
        })

        // ── Status ──────────────────────────────────────────────────────
        statusView = TextView(this).apply {
            text = "Bereit."
            setTextColor(Color.parseColor("#94A3B8"))
            textSize = 12f
            gravity = Gravity.CENTER
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(statusView)

        // ── Hauptzeile: ABC | Mikro | Backspace ─────────────────────────
        val mainRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }

        mainRow.addView(sideButton("ABC") {
            switchToPreviousKeyboard()
        }, sideParams())

        micButton = Button(this).apply {
            text = "🎙️"
            textSize = 26f
            setTextColor(Color.WHITE)
            setBackgroundColor(accentBlue)
            // Push-to-Talk: aufnehmen, solange der Button gehalten wird; beim
            // Loslassen stoppen (wie der gehaltene Hotkey der Windows-App).
            @Suppress("ClickableViewAccessibility")
            setOnTouchListener { v, event ->
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        startDictation()
                        true
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        v.performClick()   // Barrierefreiheit
                        stopDictation()
                        true
                    }
                    else -> false
                }
            }
        }
        val micParams = LinearLayout.LayoutParams(0, dp(64), 2f).apply {
            leftMargin = dp(8); rightMargin = dp(8)
        }
        mainRow.addView(micButton, micParams)

        mainRow.addView(sideButton("⌫") {
            currentInputConnection?.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_DEL))
            currentInputConnection?.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_DEL))
        }, sideParams())

        root.addView(mainRow)

        // ── Untere Zeile: Leerzeichen | Enter ───────────────────────────
        val bottomRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(6), 0, 0)
        }
        bottomRow.addView(sideButton("Leerzeichen") {
            currentInputConnection?.commitText(" ", 1)
        }, LinearLayout.LayoutParams(0, dp(44), 3f).apply { rightMargin = dp(8) })
        bottomRow.addView(sideButton("⏎") {
            currentInputConnection?.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
            currentInputConnection?.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
        }, LinearLayout.LayoutParams(0, dp(44), 1f))
        root.addView(bottomRow)

        selectWorkflow(selectedWorkflow)
        return root
    }

    // ──────────────────────────────────────────────────────────────────

    /** Stoppt eine laufende Aufnahme (Loslassen des Mikro-Buttons). */
    private fun stopDictation() {
        if (engine.isActive) engine.stop()
    }

    /** Startet die Aufnahme (Mikro-Button gedrückt). Läuft bis stopDictation(). */
    private fun startDictation() {
        if (engine.isActive) return
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            status("Mikrofon-Berechtigung fehlt — bitte die Blitzdiktat-App einmal öffnen.")
            startActivity(Intent(this, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            })
            return
        }
        if (selectedWorkflow.needsApiKey && !AppSettings.isConfigured(this)) {
            status("Für ${AppSettings.displayName(this, selectedWorkflow)} fehlt der API Key (in der App hinterlegen).")
            return
        }

        micButton?.setBackgroundColor(accentRed)
        status("Aufnahme läuft … (Mikro loslassen zum Stoppen)")

        engine.start(
            object : DictationEngine.Listener {
                override fun onPartial(text: String) {
                    status("… $text")
                }

                override fun onSegment(segment: String, accumulated: String) {
                    // Beim reinen Diktat sofort einfügen, Segment für Segment
                    if (selectedWorkflow == WorkflowType.TRANSCRIPTION) {
                        commit(segment + " ")
                    }
                }

                override fun onFinished(accumulated: String) {
                    micButton?.setBackgroundColor(accentBlue)
                    if (selectedWorkflow == WorkflowType.TRANSCRIPTION) {
                        if (accumulated.isBlank()) {
                            status("Keine Aufnahme erkannt.")
                        } else {
                            status("Fertig.")
                            persist(WorkflowType.TRANSCRIPTION, accumulated)
                        }
                        return
                    }
                    if (accumulated.isBlank()) {
                        status("Keine Aufnahme erkannt.")
                        return
                    }
                    runLlm(accumulated)
                }

                override fun onError(message: String) {
                    micButton?.setBackgroundColor(accentBlue)
                    status(message)
                }

                override fun onRms(rms: Float) {}
            },
            // Dauer-Modus: während der Button gehalten wird, lauscht die App
            // auch über Sprechpausen hinweg weiter; Schluss ist erst beim
            // Loslassen (stopDictation).
            continuous = true,
            language = AppSettings.dictationLanguage(this),
        )
    }

    private fun runLlm(text: String) {
        status("Wird verarbeitet …")
        val workflow = selectedWorkflow
        val session = inputSession
        llmJob = scope.launch {
            try {
                val result = OpenAiClient.runWorkflow(this@BlitzdiktatImeService, workflow, text)
                // Immer speichern — auch wenn nicht mehr committet werden darf,
                // ist das Ergebnis über den Verlauf erreichbar.
                persist(workflow, result)
                learnVocabulary(result)
                if (session == inputSession) {
                    commit(result)
                    status("Fertig.")
                } else {
                    status("Eingabefeld gewechselt — Ergebnis liegt im Verlauf.")
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: LlmException) {
                status(e.message ?: "Fehler.")
            } catch (e: Exception) {
                status("Unerwarteter Fehler: ${e.message}")
            }
        }
    }

    /** Ergebnis im Verlauf ablegen — wie in der Haupt-App (Protokolle zusätzlich als PDF). */
    private fun persist(type: WorkflowType, text: String) {
        scope.launch(Dispatchers.IO) {
            runCatching {
                val dir = TranscriptStore.dir(this@BlitzdiktatImeService)
                val txt = TranscriptStore.saveTranscript(dir, text, type.displayName)
                if (type == WorkflowType.PROTOKOLL) {
                    ProtocolPdf.write(text, File(dir, txt.nameWithoutExtension + ".pdf"))
                }
            }
        }
    }

    /** Vokabular im Hintergrund erweitern — wie in der Haupt-App. */
    private fun learnVocabulary(text: String) {
        scope.launch(Dispatchers.IO) {
            runCatching {
                val terms = OpenAiClient.extractTerms(this@BlitzdiktatImeService, text)
                if (terms.isNotEmpty()) {
                    VocabularyStore.addTerms(VocabularyStore.file(this@BlitzdiktatImeService), terms)
                }
            }
        }
    }

    private fun commit(text: String) {
        currentInputConnection?.commitText(text, 1)
    }

    private fun selectWorkflow(type: WorkflowType) {
        selectedWorkflow = type
        chipViews.forEach { (t, chip) ->
            chip.setBackgroundColor(if (t == type) accentBlue else Color.parseColor("#334155"))
            chip.setTypeface(null, if (t == type) Typeface.BOLD else Typeface.NORMAL)
        }
    }

    private fun switchToPreviousKeyboard() {
        // switchToPreviousInputMethod() existiert erst ab API 28 — auf
        // Android 8.x (minSdk 26) crasht der Aufruf mit NoSuchMethodError.
        val switched = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            switchToPreviousInputMethod()
        } else {
            false
        }
        if (!switched) {
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            imm.showInputMethodPicker()
        }
    }

    private fun status(text: String) {
        statusView?.text = text
    }

    private fun sideButton(label: String, onClick: () -> Unit): Button =
        Button(this).apply {
            text = label
            textSize = 14f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#334155"))
            setOnClickListener { onClick() }
        }

    private fun sideParams() = LinearLayout.LayoutParams(0, dp(64), 1f)

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()
}
