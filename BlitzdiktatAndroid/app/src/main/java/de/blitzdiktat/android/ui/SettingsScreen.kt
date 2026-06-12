// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.ui

import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.InputChip
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.blitzdiktat.android.data.AppSettings
import de.blitzdiktat.android.data.VocabularyStore
import de.blitzdiktat.android.workflows.WorkflowType

/** Sprachen der Geräte-Spracherkennung (BCP-47-Tag → Anzeigename). */
private val LANGUAGES = listOf(
    "de-DE" to "Deutsch",
    "en-US" to "Englisch (US)",
    "en-GB" to "Englisch (UK)",
    "fr-FR" to "Französisch",
    "es-ES" to "Spanisch",
    "it-IT" to "Italienisch",
    "nl-NL" to "Niederländisch",
    "pl-PL" to "Polnisch",
    "tr-TR" to "Türkisch",
)

@Composable
fun SettingsScreen() {
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text("Einstellungen", fontWeight = FontWeight.Bold, fontSize = 16.sp)

        ApiKeySection(context)
        HorizontalDivider(Modifier.padding(vertical = 4.dp))
        LanguageSection(context)
        ToneSection(context)
        EmojiDensitySection(context)
        HorizontalDivider(Modifier.padding(vertical = 4.dp))
        ModelSection(context)
        HorizontalDivider(Modifier.padding(vertical = 4.dp))
        VocabularySection(context)
        HorizontalDivider(Modifier.padding(vertical = 4.dp))

        Text("Workflows anpassen", fontWeight = FontWeight.Bold, fontSize = 16.sp)
        Text(
            "Eigener Name und (außer bei \"${WorkflowType.EMOJI_TEXT.displayName}\") eigener " +
                "System-Prompt je Workflow. Leere Felder = eingebauter Standard.",
            fontSize = 12.sp,
            color = Color.Gray,
        )
        listOf(
            WorkflowType.TEXT_IMPROVER,
            WorkflowType.DAMPF_ABLASSEN,
            WorkflowType.EMOJI_TEXT,
            WorkflowType.PROTOKOLL,
        ).forEach { type ->
            WorkflowCustomCard(context, type)
        }
        Spacer(Modifier.height(24.dp))
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun VocabularySection(context: Context) {
    var input by remember { mutableStateOf("") }
    var customTerms by remember { mutableStateOf(AppSettings.customTerms(context)) }
    var learnedTerms by remember {
        mutableStateOf(VocabularyStore.learnedTerms(VocabularyStore.file(context)))
    }

    fun addCustomTerm() {
        val term = input.trim()
        if (term.isEmpty()) return
        customTerms = (customTerms + term).distinctBy { it.lowercase() }
        AppSettings.setCustomTerms(context, customTerms)
        input = ""
    }

    Text("Vokabular", fontWeight = FontWeight.Bold, fontSize = 16.sp)
    Text(
        "Namen und Fachbegriffe, die oft falsch erkannt werden — hier in korrekter " +
            "Schreibweise eintragen. Sie fließen in ${AppSettings.displayName(context, WorkflowType.TEXT_IMPROVER)} " +
            "und ${AppSettings.displayName(context, WorkflowType.PROTOKOLL)} ein. " +
            "Antippen entfernt einen Begriff.",
        fontSize = 12.sp,
        color = Color.Gray,
    )

    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        OutlinedTextField(
            value = input,
            onValueChange = { input = it },
            label = { Text("Begriff hinzufügen") },
            placeholder = { Text("z. B. Karstens, Blitzdiktat") },
            modifier = Modifier.weight(1f),
            singleLine = true,
        )
        Button(onClick = { addCustomTerm() }, enabled = input.isNotBlank()) {
            Text("+")
        }
    }

    if (customTerms.isNotEmpty()) {
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            customTerms.forEach { term ->
                InputChip(
                    selected = false,
                    onClick = {
                        customTerms = customTerms.filterNot { it == term }
                        AppSettings.setCustomTerms(context, customTerms)
                    },
                    label = { Text("$term ✕") },
                )
            }
        }
    }

    if (learnedTerms.isNotEmpty()) {
        Text(
            "Automatisch gelernt (${learnedTerms.size})",
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium,
        )
        Text(
            "Aus früheren Ergebnissen extrahiert (max. ${VocabularyStore.MAX_TERMS} Begriffe).",
            fontSize = 12.sp,
            color = Color.Gray,
        )
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            learnedTerms.forEach { term ->
                InputChip(
                    selected = false,
                    onClick = {
                        VocabularyStore.removeTerm(VocabularyStore.file(context), term)
                        learnedTerms = VocabularyStore.learnedTerms(VocabularyStore.file(context))
                    },
                    label = { Text("$term ✕") },
                )
            }
        }
        OutlinedButton(onClick = {
            VocabularyStore.clear(VocabularyStore.file(context))
            learnedTerms = emptyList()
            Toast.makeText(context, "Gelerntes Vokabular geleert.", Toast.LENGTH_SHORT).show()
        }) { Text("Gelerntes Vokabular leeren") }
    } else {
        Text(
            "Noch nichts automatisch gelernt. Nach jedem Workflow mit OpenAI-Key werden " +
                "Eigennamen im Hintergrund extrahiert und hier ergänzt.",
            fontSize = 12.sp,
            color = Color.Gray,
        )
    }
}

@Composable
private fun ApiKeySection(context: Context) {
    var apiKey by remember { mutableStateOf("") }
    var savedHint by remember { mutableStateOf(AppSettings.maskedKey(context)) }

    OutlinedTextField(
        value = apiKey,
        onValueChange = { apiKey = it },
        label = {
            Text(if (savedHint.isEmpty()) "OpenAI API Key (optional)" else "OpenAI API Key ($savedHint)")
        },
        visualTransformation = PasswordVisualTransformation(),
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
    )
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(
            onClick = {
                AppSettings.setApiKey(context, apiKey)
                savedHint = AppSettings.maskedKey(context)
                apiKey = ""
                Toast.makeText(context, "Key gespeichert (verschlüsselt).", Toast.LENGTH_SHORT).show()
            },
            enabled = apiKey.isNotBlank(),
        ) { Text("Key speichern") }
        if (savedHint.isNotEmpty()) {
            OutlinedButton(onClick = {
                AppSettings.setApiKey(context, "")
                savedHint = ""
                Toast.makeText(context, "Key gelöscht.", Toast.LENGTH_SHORT).show()
            }) { Text("Löschen") }
        }
    }
    Text(
        "Ohne Key funktioniert das reine Blitzdiktat (lokal auf dem Gerät). " +
            "Die anderen Workflows benötigen einen OpenAI-Key.",
        fontSize = 12.sp,
        color = Color.Gray,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun LanguageSection(context: Context) {
    var expanded by remember { mutableStateOf(false) }
    var language by remember { mutableStateOf(AppSettings.dictationLanguage(context)) }
    val label = LANGUAGES.firstOrNull { it.first == language }?.second ?: language

    Text("Diktiersprache", fontSize = 13.sp, fontWeight = FontWeight.Medium)
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = label,
            onValueChange = {},
            readOnly = true,
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            LANGUAGES.forEach { (tag, name) ->
                DropdownMenuItem(
                    text = { Text(name) },
                    onClick = {
                        language = tag
                        AppSettings.setDictationLanguage(context, tag)
                        expanded = false
                    },
                )
            }
        }
    }
    Text(
        "Sprache der Spracherkennung in App und Tastatur. Für Offline-Erkennung muss " +
            "das Sprachpaket auf dem Gerät installiert sein.",
        fontSize = 12.sp,
        color = Color.Gray,
    )
}

@Composable
private fun ToneSection(context: Context) {
    var tone by remember { mutableStateOf(AppSettings.tone(context)) }

    Text("Ton (${AppSettings.displayName(context, WorkflowType.TEXT_IMPROVER)})", fontSize = 13.sp, fontWeight = FontWeight.Medium)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf("formal", "neutral", "casual").forEach { option ->
            FilterChip(
                selected = tone == option,
                onClick = {
                    tone = option
                    AppSettings.setTone(context, option)
                },
                label = { Text(option) },
            )
        }
    }
}

@Composable
private fun EmojiDensitySection(context: Context) {
    var density by remember { mutableStateOf(AppSettings.emojiDensity(context)) }

    Text("Emoji-Dichte (${AppSettings.displayName(context, WorkflowType.EMOJI_TEXT)})", fontSize = 13.sp, fontWeight = FontWeight.Medium)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf("wenig", "mittel", "viel").forEach { option ->
            FilterChip(
                selected = density == option,
                onClick = {
                    density = option
                    AppSettings.setEmojiDensity(context, option)
                },
                label = { Text(option) },
            )
        }
    }
}

@Composable
private fun ModelSection(context: Context) {
    var fast by remember { mutableStateOf(AppSettings.modelFastOverride(context)) }
    var quality by remember { mutableStateOf(AppSettings.modelQualityOverride(context)) }

    Text("OpenAI-Modelle", fontSize = 13.sp, fontWeight = FontWeight.Medium)
    OutlinedTextField(
        value = fast,
        onValueChange = { fast = it },
        label = { Text("Schnelles Modell") },
        placeholder = { Text(AppSettings.DEFAULT_MODEL_FAST) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
    )
    OutlinedTextField(
        value = quality,
        onValueChange = { quality = it },
        label = { Text("Qualitätsmodell") },
        placeholder = { Text(AppSettings.DEFAULT_MODEL_QUALITY) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
    )
    Button(onClick = {
        AppSettings.setModels(context, fast, quality)
        Toast.makeText(context, "Modelle gespeichert.", Toast.LENGTH_SHORT).show()
    }) { Text("Modelle speichern") }
    Text(
        "Leer = Standard (${AppSettings.DEFAULT_MODEL_FAST} / ${AppSettings.DEFAULT_MODEL_QUALITY}), wie auf Windows.",
        fontSize = 12.sp,
        color = Color.Gray,
    )
}

@Composable
private fun WorkflowCustomCard(context: Context, type: WorkflowType) {
    var expanded by remember { mutableStateOf(false) }
    var name by remember { mutableStateOf(AppSettings.customName(context, type)) }
    var prompt by remember { mutableStateOf(AppSettings.customPrompt(context, type)) }
    // Emoji-Workflow hat wie auf Windows keinen eigenen Prompt (nur die Dichte).
    val hasPrompt = type != WorkflowType.EMOJI_TEXT

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { expanded = !expanded },
            ) {
                Text(
                    "${type.emoji} ${type.displayName}",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.sp,
                    modifier = Modifier.weight(1f),
                )
                Text(if (expanded) "▲" else "▼", color = Color.Gray, fontSize = 12.sp)
            }
            if (expanded) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Eigener Name") },
                    placeholder = { Text(type.displayName) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                )
                if (hasPrompt) {
                    OutlinedTextField(
                        value = prompt,
                        onValueChange = { prompt = it },
                        label = { Text("Eigener System-Prompt") },
                        placeholder = { Text("Leer = eingebauter Standard-Prompt") },
                        modifier = Modifier.fillMaxWidth(),
                        minLines = 3,
                    )
                }
                Button(onClick = {
                    AppSettings.setCustomName(context, type, name)
                    if (hasPrompt) AppSettings.setCustomPrompt(context, type, prompt)
                    Toast.makeText(context, "Gespeichert.", Toast.LENGTH_SHORT).show()
                }) { Text("Speichern") }
            }
        }
    }
}
