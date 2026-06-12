// Copyright (c) 2026 Thorben Meier. MIT License.
package de.blitzdiktat.android.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.core.content.FileProvider
import java.io.File

fun copyToClipboard(context: Context, text: String) {
    val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    cm.setPrimaryClip(ClipData.newPlainText("Blitzdiktat", text))
    Toast.makeText(context, "Kopiert.", Toast.LENGTH_SHORT).show()
}

fun shareText(context: Context, text: String) {
    val send = Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_TEXT, text)
    }
    context.startActivity(Intent.createChooser(send, "Teilen mit …"))
}

/** Teilt eine Datei (z. B. Protokoll-PDF) über den FileProvider der App. */
fun shareFile(context: Context, file: File, mimeType: String) {
    val uri = FileProvider.getUriForFile(
        context,
        context.packageName + ".fileprovider",
        file,
    )
    val send = Intent(Intent.ACTION_SEND).apply {
        type = mimeType
        putExtra(Intent.EXTRA_STREAM, uri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(send, "Teilen mit …"))
}
