plugins {
    // Seit AGP 9 ist Kotlin im Android-Plugin eingebaut (KGP 2.2.10) —
    // org.jetbrains.kotlin.android entfällt. Nur der Compose-Compiler
    // bleibt als Plugin nötig; seine Version muss zur eingebauten
    // Kotlin-Version passen.
    id("com.android.application") version "9.3.0" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.10" apply false
}
