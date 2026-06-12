// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.ui

import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.blitzdiktat.android.AppViewModel
import de.blitzdiktat.android.Phase
import de.blitzdiktat.android.UiState
import de.blitzdiktat.android.data.AppSettings
import de.blitzdiktat.android.workflows.WorkflowType

@Composable
fun StartScreen(
    viewModel: AppViewModel,
    onWorkflowClick: (WorkflowType) -> Unit,
    onImportClick: () -> Unit,
) {
    val state by viewModel.state.collectAsState()
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        WorkflowType.entries.forEach { type ->
            WorkflowCard(
                title = AppSettings.displayName(context, type),
                type = type,
                isActive = state.activeWorkflow == type && state.phase == Phase.RECORDING,
                enabled = state.phase == Phase.IDLE || state.phase == Phase.DONE ||
                    state.phase == Phase.ERROR ||
                    (state.phase == Phase.RECORDING && state.activeWorkflow == type),
                onClick = { onWorkflowClick(type) },
            )
        }

        OutlinedButton(
            onClick = onImportClick,
            enabled = state.phase != Phase.RECORDING && state.phase != Phase.PROCESSING,
            modifier = Modifier.fillMaxWidth(),
        ) { Text("📄 Protokoll aus Textdatei erstellen") }

        StatusSection(state = state, onReset = { viewModel.reset() })

        HorizontalDivider(Modifier.padding(vertical = 8.dp))
        KeyboardSection(context)
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun WorkflowCard(
    title: String,
    type: WorkflowType,
    isActive: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) { onClick() },
        colors = CardDefaults.cardColors(
            containerColor = if (isActive) Color(0xFFFEE2E2) else MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(type.emoji, fontSize = 26.sp)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                Text(type.subtitle, fontSize = 13.sp, color = Color.Gray)
            }
            if (isActive) {
                Spacer(
                    Modifier
                        .size(14.dp)
                        .background(Color(0xFFDC2626), CircleShape),
                )
            }
        }
    }
}

@Composable
private fun StatusSection(state: UiState, onReset: () -> Unit) {
    val context = LocalContext.current

    if (state.phase == Phase.PROCESSING) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
            Spacer(Modifier.width(10.dp))
            Text(state.statusText)
        }
    } else if (state.statusText.isNotEmpty() && state.phase == Phase.RECORDING) {
        Text(state.statusText, color = Color(0xFFDC2626), fontWeight = FontWeight.Medium)
    }

    if (state.liveText.isNotEmpty() && state.phase == Phase.RECORDING) {
        Text(state.liveText, fontSize = 14.sp, color = Color.DarkGray)
    }

    if (state.phase == Phase.ERROR) {
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFFFEF2F2)),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(Modifier.padding(12.dp)) {
                Text("Fehler", fontWeight = FontWeight.Bold, color = Color(0xFFB91C1C))
                Text(state.errorText, color = Color(0xFFB91C1C), fontSize = 14.sp)
            }
        }
    }

    if (state.phase == Phase.DONE && state.resultText.isNotEmpty()) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Ergebnis", fontWeight = FontWeight.Bold)
                Text(state.resultText, fontSize = 14.sp)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { copyToClipboard(context, state.resultText) }) {
                        Text("Kopieren")
                    }
                    OutlinedButton(onClick = { shareText(context, state.resultText) }) {
                        Text("Teilen")
                    }
                    state.pdfFile?.let { pdf ->
                        OutlinedButton(onClick = { shareFile(context, pdf, "application/pdf") }) {
                            Text("PDF")
                        }
                    }
                    OutlinedButton(onClick = onReset) { Text("Neu") }
                }
            }
        }
    }
}

@Composable
private fun KeyboardSection(context: Context) {
    Text("Tastatur", fontWeight = FontWeight.Bold, fontSize = 16.sp)
    Text(
        "Die Blitzdiktat-Tastatur diktiert direkt in jede App: Aktivieren, dann beim Schreiben " +
            "über die Tastatur-Auswahl zu Blitzdiktat wechseln und das Mikro antippen.",
        fontSize = 13.sp,
        color = Color.Gray,
    )
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = {
            context.startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        }) { Text("Tastatur aktivieren") }
        OutlinedButton(onClick = {
            val imm = context.getSystemService(Context.INPUT_METHOD_SERVICE)
                as android.view.inputmethod.InputMethodManager
            imm.showInputMethodPicker()
        }) { Text("Tastatur wechseln") }
    }
}
