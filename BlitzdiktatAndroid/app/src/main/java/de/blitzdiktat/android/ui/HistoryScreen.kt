// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.blitzdiktat.android.AppViewModel
import de.blitzdiktat.android.data.TranscriptStore
import java.text.SimpleDateFormat
import java.util.Locale

@Composable
fun HistoryScreen(viewModel: AppViewModel) {
    val entries by viewModel.history.collectAsState()
    LaunchedEffect(Unit) { viewModel.refreshHistory() }

    if (entries.isEmpty()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text("Noch keine gespeicherten Ergebnisse.", color = Color.Gray)
            Text(
                "Jedes Workflow-Ergebnis wird hier automatisch abgelegt " +
                    "und nach ${TranscriptStore.MAX_AGE_DAYS} Tagen gelöscht.",
                fontSize = 12.sp,
                color = Color.Gray,
            )
        }
        return
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("Verlauf (${entries.size})", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                Text(
                    "Einträge werden nach ${TranscriptStore.MAX_AGE_DAYS} Tagen automatisch gelöscht.",
                    fontSize = 12.sp,
                    color = Color.Gray,
                )
            }
        }
        items(entries, key = { it.file.absolutePath }) { entry ->
            HistoryCard(entry = entry, onDelete = { viewModel.deleteEntry(entry) })
        }
    }
}

@Composable
private fun HistoryCard(entry: TranscriptStore.Entry, onDelete: () -> Unit) {
    val context = LocalContext.current
    var expanded by remember { mutableStateOf(false) }
    val dateText = remember(entry.savedAt) {
        SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.GERMAN).format(entry.savedAt)
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { expanded = !expanded },
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    entry.workflowName.ifBlank { "Blitzdiktat" },
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.sp,
                    modifier = Modifier.weight(1f),
                )
                Text(dateText, fontSize = 12.sp, color = Color.Gray)
            }
            Text(
                entry.text,
                fontSize = 13.sp,
                maxLines = if (expanded) Int.MAX_VALUE else 3,
                overflow = TextOverflow.Ellipsis,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                TextButton(onClick = { copyToClipboard(context, entry.text) }) {
                    Text("Kopieren")
                }
                TextButton(onClick = { shareText(context, entry.text) }) {
                    Text("Teilen")
                }
                entry.pdf?.let { pdf ->
                    TextButton(onClick = { shareFile(context, pdf, "application/pdf") }) {
                        Text("PDF")
                    }
                }
                TextButton(onClick = onDelete) {
                    Text("Löschen", color = Color(0xFFB91C1C))
                }
            }
        }
    }
}
