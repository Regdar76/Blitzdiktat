// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import de.blitzdiktat.android.ui.HistoryScreen
import de.blitzdiktat.android.ui.SettingsScreen
import de.blitzdiktat.android.ui.StartScreen
import de.blitzdiktat.android.workflows.WorkflowType

class MainActivity : ComponentActivity() {

    private val viewModel: AppViewModel by viewModels()
    private var pendingWorkflow: WorkflowType? = null

    private val micPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        val wf = pendingWorkflow
        pendingWorkflow = null
        if (granted && wf != null) {
            viewModel.toggle(wf)
        } else if (!granted) {
            Toast.makeText(this, "Ohne Mikrofon-Berechtigung geht es nicht.", Toast.LENGTH_LONG).show()
        }
    }

    private val openTextDocument = registerForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        val text = runCatching {
            contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
        }.getOrNull()
        if (text.isNullOrBlank()) {
            Toast.makeText(this, "Datei ist leer oder konnte nicht gelesen werden.", Toast.LENGTH_LONG).show()
        } else {
            viewModel.importTextForProtokoll(text)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                MainScreen(
                    viewModel = viewModel,
                    onWorkflowClick = { startWithPermission(it) },
                    onImportClick = { openTextDocument.launch(arrayOf("text/*")) },
                )
            }
        }
    }

    private fun startWithPermission(type: WorkflowType) {
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.RECORD_AUDIO,
        ) == PackageManager.PERMISSION_GRANTED
        if (granted) {
            viewModel.toggle(type)
        } else {
            pendingWorkflow = type
            micPermission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainScreen(
    viewModel: AppViewModel,
    onWorkflowClick: (WorkflowType) -> Unit,
    onImportClick: () -> Unit,
) {
    var tab by rememberSaveable { mutableIntStateOf(0) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("⚡ Blitzdiktat", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF1E293B),
                    titleContentColor = Color.White,
                ),
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = tab == 0,
                    onClick = { tab = 0 },
                    icon = { Text("⚡", fontSize = 18.sp) },
                    label = { Text("Start") },
                )
                NavigationBarItem(
                    selected = tab == 1,
                    onClick = { tab = 1 },
                    icon = { Text("🗂️", fontSize = 18.sp) },
                    label = { Text("Verlauf") },
                )
                NavigationBarItem(
                    selected = tab == 2,
                    onClick = { tab = 2 },
                    icon = { Text("⚙️", fontSize = 18.sp) },
                    label = { Text("Einstellungen") },
                )
            }
        },
    ) { padding ->
        Box(
            Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            when (tab) {
                0 -> StartScreen(viewModel, onWorkflowClick, onImportClick)
                1 -> HistoryScreen(viewModel)
                else -> SettingsScreen()
            }
        }
    }
}
