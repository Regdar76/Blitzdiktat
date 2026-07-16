# Blitzdiktat — R8-Regeln für den Release-Build.
#
# Die App nutzt kaum Reflection: JSON läuft über das eingebaute org.json,
# OkHttp bringt eigene Consumer-Rules mit, Compose ist R8-kompatibel.
# Zusätzliche Keep-Regeln nur hier ergänzen, wenn ein konkreter
# Release-Crash sie erfordert.

# Zeilennummern für lesbare Stacktraces behalten
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Tink (via androidx.security:security-crypto) referenziert ErrorProne-
# Annotationen, die nur zur Compile-Zeit existieren — sicher zu ignorieren.
-dontwarn com.google.errorprone.annotations.CanIgnoreReturnValue
-dontwarn com.google.errorprone.annotations.CheckReturnValue
-dontwarn com.google.errorprone.annotations.Immutable
-dontwarn com.google.errorprone.annotations.RestrictedApi
