# Modellvergleich lokale KI

Echte Blitzdiktat-Prompts, deutsche Beispiel-Diktate, gemessen über LM Studio.

## Zeiten in Sekunden (gesamt je Aufgabe)

| Modell | Laden | RAM | Blitzdiktat+ | $%&! | :) | Protokoll | Vokabular | Tokens/s |
|---|---|---|---|---|---|---|---|---|
| gemma-4-e2b-it · Grafikkarte (max) | 7.7 | 3.7 GB | 6.7 | – | 5.2 | 23.2 | – | 18.4 |
| gemma-4-e2b-it · Prozessor | 7.0 | 3.7 GB | 10.7 | 10.8 | 7.1 | 44.3 | 5.2 | 11.7 |
| gemma-4-e4b-it · Prozessor | 9.2 | 5.4 GB | 17.6 | 30.2 | 12.5 | 139.1 | 7.4 | 6.8 |
| prism-ml/bonsai-27b · Prozessor | 16.1 | 5.3 GB | 51.2 | 62.5 | 36.9 | 261.5 | 27.8 | 2.5 |
| qwen3.5-2b · Grafikkarte (max) | 4.9 | 1.6 GB | 7.2 | – | 6.4 | 29.7 | – | 18.6 |
| qwen3.5-2b · Prozessor | 4.9 | 1.6 GB | 9.1 | 15.4 | 7.2 | 42.5 | 6.2 | 15.4 |
| qwen3.5-4b · Grafikkarte (max) | 9.1 | 5.0 GB | 28.2 | – | 23.3 | 147.8 | – | 4.9 |
| qwen3.5-4b · Prozessor | 7.5 | 3.4 GB | 16.6 | 24.8 | 15.7 | 94.3 | 8.1 | 7.5 |
| qwen/qwen3.5-9b · Grafikkarte (0.5) | 11.8 | 8.3 GB | 31.1 | – | 27.5 | – | – | 3.9 |
| qwen/qwen3.5-9b · Prozessor | 11.1 | 6.2 GB | 23.4 | 26.2 | 21.2 | 147.0 | 11.8 | 4.9 |

## Prüfwörter (gefunden / erwartet)

| Modell | Blitzdiktat+ | $%&! | :) | Protokoll | Vokabular |
|---|---|---|---|---|---|
| gemma-4-e2b-it · Grafikkarte (max) | 5/7 | – | 3/4 | 8/12 | – |
| gemma-4-e2b-it · Prozessor | 5/7 | 2/3 | 4/4 | 7/12 | 5/5 |
| gemma-4-e4b-it · Prozessor | 7/7 | 1/3 | 3/4 | 9/12 | 5/5 |
| prism-ml/bonsai-27b · Prozessor | 7/7 | 2/3 | 3/4 | 8/12 | 5/5 |
| qwen3.5-2b · Grafikkarte (max) | 7/7 | – | 4/4 ⚠ Hier ist | 7/12 | – |
| qwen3.5-2b · Prozessor | 7/7 | 1/3 ⚠ Hier ist | 4/4 ⚠ Hier ist | 6/12 | 5/5 |
| qwen3.5-4b · Grafikkarte (max) | 7/7 | – | 4/4 ⚠ Hier ist | 8/12 | – |
| qwen3.5-4b · Prozessor | 7/7 | 1/3 | 4/4 ⚠ Hier ist | 8/12 | 5/5 |
| qwen/qwen3.5-9b · Grafikkarte (0.5) | 7/7 | – | 4/4 | – | – |
| qwen/qwen3.5-9b · Prozessor | 7/7 | 3/3 | 4/4 | 9/12 | 5/5 |

## Ausgaben im Wortlaut

### gemma-4-e2b-it · Grafikkarte (max)

**Blitzdiktat+** — 6.7 s, erstes Zeichen nach 2.3 s, 119 Tokens, fehlt: I-Log, Dezember

```text
Sehr geehrte Frau Petersen,

ich möchte mich noch einmal bezüglich der Schließanlage bei Ihnen melden. Wir hatten letzte Woche darüber gesprochen, dass die Ei Log Zylinder für die Außentüren noch nicht bestellt sind. Das Problem ist derzeit, dass die Lieferzeit sechs Wochen beträgt. Wenn wir dies nicht noch diese Woche auslösen, wird es schwierig. Könnten Sie mir bitte bis Freitag mitteilen, ob wir die vierzehn Zylinder wie im Angebot bestellen sollen oder ob sich dies geändert hat?

Vielen Dank im Voraus und viele Grüße,
Jan Hansen
```

**Blitzdiktat :)** — 5.2 s, erstes Zeichen nach 2.3 s, 81 Tokens, fehlt: 16

```text
Moin zusammen, kurze Info: Das Sommerfest findet dieses Jahr am zwölften Juni ab sechzehn Uhr auf dem Betriebshof statt! 🥳 Es gibt gegrilltes und kalte Getränke 🍔🍹 und für die Kinder eine Hüpfburg! 🎈 Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können. Wir freuen uns auf euch! 😊
```

**Protokoll** — 23.2 s, erstes Zeichen nach 3.2 s, 514 Tokens, fehlt: 2,8, 1.850, 01.12.2026, 10.12.2026

```text
**Datum:** 26.11.2026
**Thema:** Baubesprechung
**Teilnehmer:** Frau Petersen, Herr Yilmaz, [Name nicht genannt], Herr Brandt

---

### Zusammenfassung
Die Besprechung befasste sich mit aktuellen baulichen und technischen Punkten im Rahmen des Projekts. Es wurde die Trocknungsfeuchte für den Bodenbelag besprochen, welche unter zwei Prozent benötigt wird, was zu einer Verzögerung führt. Zudem wurden Anpassungen bezüglich der Netzwerkdosen, der Verlegung von Leerrohren für Kameras sowie der Glasfaser-Hausanschluss und der Platzierung des Serverschranks besprochen. Die Telekom hat den Termin für den Hausanschluss bestätigt, und es wurde eine Änderung der Raumplanung aufgrund von Lüftungsanforderungen angestoßen.

### Besprochene Punkte
- Restfeuchte liegt aktuell bei zwei Komma acht Prozent, benötigt aber unter zwei Komma null Prozent für den Bodenbelag.
- Ein Angebot für zusätzliche Trocknungsgeräte wurde eingeholt: eintausendachthundertfünfzig Euro netto für zwei Wochen, um die Trocknung zu beschleunigen.
- Ursprünglich waren zwölf Netzwerkdosen geplant, müssen nun vierzehn benötigt werden aufgrund von zwei zusätzlichen Arbeitsplätzen im Empfangsbereich.
- Die Leerrohre für die Kameras an der Zufahrt sind vorhanden (drei Stück bis zum Mast).
- Der Glasfaser-Hausanschluss ist für den neunten Dezember vormittags bestätigt.
- Der geplante Platz für den Serverschrank in Raum 0,12 ist aufgrund unzureichender Lüftung nicht ausreichend; stattdessen wird Raum 0,14 vorgeschlagen.

### Entscheidungen
- Die Beauftragung der zusätzlichen Trocknungsgeräte wurde vereinbart.

### Offene Aufgaben
- Nachtragsangebot für die Netzwerkdosen zu schreiben — Verantwortlich: [Name nicht genannt], Deadline: nächsten Dienstag (28.11.2026)
- Änderung des Plans bezüglich Raum 0,12/0,14 mit den Architekten zu besprechen und umsetzen — Verantwortlich: [Name nicht genannt], Deadline: Ende nächster Woche

### Nächster Termin
Nächste Besprechung: Donnerstag, 29.12.2026 um 9:00 Uhr auf der Baustelle.
```

### gemma-4-e2b-it · Prozessor

**Blitzdiktat+** — 10.7 s, erstes Zeichen nach 3.6 s, 122 Tokens, fehlt: I-Log, Dezember

```text
Sehr geehrte Frau Petersen,

ich möchte mich noch einmal bezüglich der Schließanlage bei Ihnen melden. Wir hatten letzte Woche darüber gesprochen, dass die E-Log-Zylinder für die Außentüren noch nicht bestellt sind. Das Problem ist derzeit, dass die Lieferzeit noch sechs Wochen beträgt. Wenn wir dies nicht noch diese Woche auslösen, wird es schwierig. Könnten Sie mir bitte bis Freitag mitteilen, ob wir die vierzehn Zylinder wie im Angebot bestellen sollen oder ob sich dies geändert hat?

Vielen Dank im Voraus und viele Grüße,
Jan Hansen
```

**Blitzdiktat $%&!** — 10.8 s, erstes Zeichen nach 2.6 s, 143 Tokens, fehlt: Server

```text
Ich habe bezüglich des Lieferterminverschiebung und der fehlenden Kommunikation mit dem Lieferanten große Unzufriedenheit.

Wir hatten für den Umzug die Lieferung für Montag vereinbart, aber heute erhalte ich eine Nachricht, dass die Lieferung nun zwei Wochen dauert, ohne vorherige Information oder Absprache. Dies ist inakzeptabel, besonders da drei Personen bereits für den Umzug zur Verfügung stehen.

Ich fordere hiermit eine sofortige Lieferung bis spätestens nächsten Mittwoch. Sollte diese Frist nicht eingehalten werden, werde ich die Auftragsvergabe an einen anderen Lieferanten verlagern und eine Gutschrift für die entstandenen Unannehmlichkeiten verlangen.
```

**Blitzdiktat :)** — 7.1 s, erstes Zeichen nach 2.5 s, 83 Tokens

```text
Moin zusammen 👋 Kurze Info: Das Sommerfest findet dieses Jahr am 12. Juni ab 16 Uhr auf dem Betriebshof statt! 🥳 Es gibt gegrilltes und kalte Getränke 🍔🍹 und für die Kinder eine Hüpfburg! 🎈 Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können. Wir freuen uns auf euch! 😊
```

**Protokoll** — 44.3 s, erstes Zeichen nach 3.8 s, 553 Tokens, fehlt: 2,8, 1.850, 01.12.2026, 09.12.2026, 10.12.2026

```text
**Datum:** 26.11.2026
**Thema:** Baubesprechung
**Teilnehmer:** Frau Petersen, Herr Yilmaz, [Name nicht genannt], Herr Brandt

---

### Zusammenfassung
Die Besprechung befasste sich mit der aktuellen Baustandslage und den notwendigen Anpassungen für die weiteren Bauphasen. Es wurde festgestellt, dass die Restfeuchte aktuell bei zwei Komma acht Prozent liegt und unter zwei Komma null benötigt wird, was zu einer Verzögerung von einer Woche führt. Es wurde ein Angebot für zusätzliche Trocknungsgeräte eingeholt, um diese Verzögerung zu minimieren. Zudem wurden Anpassungen bezüglich der Netzwerkdosen, des Glasfaseranschlusses und der Raumplanung für die IT vorgenommen. Der Umzugstermin wurde vorerst auf Mitte Dezember angesetzt, falls der Estrich mitspielt.

### Besprochene Punkte
- **Estrich in Halle:** Die Restfeuchte liegt bei zwei Komma acht Prozent; unter zwei Komma null ist erforderlich, bevor der Bodenbelag eingesetzt werden kann.
- **Trocknungsgeräte:** Ein Angebot für zusätzliche Trocknungsgeräte wurde eingeholt (1450 Euro netto für zwei Wochen).
- **Netzwerkdosen Elektro:** Ursprünglich waren zwölf Netzwerkdosen geplant; nun werden vierzehn benötigt, da das Empfangsbereich zwei zusätzliche Arbeitsplätze erhält.
- **Kameras/Leerrohre:** Die Leerrohre für die Kameras an der Zufahrt sind vorhanden (drei Stück bis zum Mast).
- **Glasfaser Hausanschluss IT:** Der Termin wurde mit der Telekom auf den neunten Dezember vormittags bestätigt.
- **Raumplanung IT:** Der ursprünglich geplante Raum 0,12 ist aufgrund unzureichender Lüftung nicht ausreichend; stattdessen wird Raum 0,14 mit Fenster nach Norden vorgeschlagen.

### Entscheidungen
- Die Beauftragung der zusätzlichen Trocknungsgeräte wird vereinbart.
- Die Änderung des Raumes für die IT auf Raum 0,14 wird an den Architekten weitergegeben und bis Ende nächster Woche erledigt werden soll.
- Der Umzugstermin bleibt vorerst auf Mitte Dezember, falls der Estrich mitspielt.

### Offene Aufgaben
- Nachtragsangebot für Netzwerkdosen erstellen — Verantwortlich: [Name nicht genannt], Deadline: nächsten Dienstag.

### Nächster Termin
Nächste Besprechung: Donnerstag, 26.11.2026 um 9:00 Uhr auf der Baustelle.
```

**Vokabular-Extraktion** — 5.2 s, erstes Zeichen nach 2.5 s, 49 Tokens

```text
["Petersen", "Yilmaz", "Elektro Hansen", "Nordlicht Systems", "I-Log-Schließanlage", "Werftstraße", "Kiel", "Telekom", "Glasfaseranschluss"]
```

### gemma-4-e4b-it · Prozessor

**Blitzdiktat+** — 17.6 s, erstes Zeichen nach 3.9 s, 129 Tokens

```text
Sehr geehrte Frau Petersen,

ich melde mich erneut bezüglich der Schließanlage. Wir hatten letzte Woche besprochen, dass die I-Log Zylinder für die Außentüren noch nicht bestellt wurden. Das Problem ist, dass die Lieferzeit momentan bei sechs Wochen liegt. Das bedeutet, wenn wir dies nicht diese Woche auslösen, wird der Einzug Mitte Dezember nicht mehr möglich sein.

Könnten Sie mir bitte bis Freitag mitteilen, ob wir die vierzehn Zylinder wie im Angebot bestellen sollen oder ob sich hierzu Änderungen ergeben haben?

Vielen Dank und viele Grüße
Jan Hansen
```

**Blitzdiktat $%&!** — 30.2 s, erstes Zeichen nach 3.7 s, 245 Tokens, fehlt: Gutschrift, Server

```text
Ich verstehe Ihren Frust sehr gut. Die wiederholte Terminverschiebung ohne vorherige Kommunikation ist extrem problematisch für Ihre Planung und verursacht unnötigen Mehraufwand.

Um das Problem direkt anzugehen, schlage ich folgende klare Nachricht vor:

"Guten Tag [Name des Lieferanten/Ansprechpartners],

ich muss Sie dringend auf die wiederholte Terminplanung hinweisen. Dies ist bereits das dritte Mal, dass der Liefertermin ohne vorherige Benachrichtigung verschoben wird. Wir hatten verbindlich einen Termin für diesen Montag angenommen und erhalten heute erst eine Nachricht über eine weitere Verzögerung von zwei Wochen.

Diese unvorhergesehene Änderung hat direkte Auswirkungen auf unsere internen Abläufe, da wir drei Mitarbeiter für den Umzug planen mussten und diese nun ohne die notwendige Ausrüstung warten müssen.

Wir benötigen dringend Klarheit: Wir erwarten verbindlich einen Liefertermin bis spätestens nächsten Mittwoch. Bitte bestätigen Sie uns diesen Termin schriftlich und stellen Sie sicher, dass dieser eingehalten wird. Sollte dieser Meilenstein nicht erreicht werden können, müssten wir unsere Zusammenarbeit überdienen und die damit verbundenen Kosten entsprechend anpassen."
```

**Blitzdiktat :)** — 12.5 s, erstes Zeichen nach 3.4 s, 87 Tokens, fehlt: 16

```text
Moin zusammen 👋, kurze Info: Das Sommerfest ☀️ findet dieses Jahr am zwölften Juni ab sechzehn Uhr 🕕 auf dem Betriebshof statt. Es gibt gegrilltes 🍖 und kalte Getränke 🥤, und für die Kinder eine Hüpfburg! 🏰 Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können. Wir freuen uns auf euch! 😊🎉
```

**Protokoll** — 139.1 s, erstes Zeichen nach 6.7 s, 807 Tokens, fehlt: 01.12.2026, 10.12.2026, Yilmaz

```text
## Protokoll

**Datum:** Donnerstag, 26.11.2026
**Thema:** Baustellenkoordination (Estrichtrocknung, Elektroinstallationen, IT-Anbindung)
**Teilnehmer:** Frau Petersen, Herr Yılmaz, [Name des Protokollführers/IT], Herr Brandt (abgesagt)

---

### Zusammenfassung
Die Besprechung diente der Koordination wichtiger Gewerke auf der Baustelle. Hauptproblem ist die Restfeuchte im Estrich von Halle zwei, welche mit 2,8% über dem Grenzwert von unter 2,0% liegt und eine Verzögerung von einer Woche bedeutet. Es wurde beschlossen, zusätzliche Trocknungsgeräte für 1.850 Euro netto zu beauftragen, um die verlorene Zeit einzuholen. Hinsichtlich der Elektroinstallationen wird Herr Yılmaz ein Nachtragsangebot für zwei zusätzliche Netzwerkdosen im Erdgeschoss erstellen und bestätigt, dass die Leerrohre für Kameras an der Zufahrt vorhanden sind. Für die IT-Anbindung wurde der Termin mit der Telekom auf den 9. Dezember vormittags festgelegt; zudem wird der Standort des Serverschranks von Raum 0.12 auf den größere Raum 0.14 geändert und dies durch Frau Petersen beim Architekten veranlasst. Die nächste Besprechung ist für zwei Wochen in zwei Wochen angesetzt, um den Fortschritt zu überprüfen.

### Besprochene Punkte
#### Estrichtrocknung Halle zwei
*   Die aktuelle Restfeuchte liegt bei 2,8%, während der Grenzwert unter 2,0% liegen muss, bevor der Bodenbelag verlegt werden kann.
*   Dies führt zu einem Zeitverlust von einer Woche.
*   Es wurde ein Angebot für zusätzliche Trocknungsgeräte in Höhe von 1.850 Euro netto für zwei Wochen eingeholt.

#### Elektroinstallationen (Herr Yılmaz)
*   Ursprünglich waren zwölf Netzwerkdosen im Erdgeschoss geplant, aber aufgrund eines zusätzlichen Arbeitsplatzes für den Empfang sind vierzehn notwendig.
*   Ein Nachtragsangebot wird bis nächsten Dienstag erstellt und übermittelt.
*   Die Leerrohre für die Kameras an der Zufahrt sind vorhanden (drei Stück bis zum Mast).

#### IT-Infrastruktur und Raumplanung
*   Der Termin für den Glasfaser Hausanschluss mit der Telekom ist bestätigt: 9. Dezember vormittags; vor Ort muss jemand sein, was der Protokollführer übernehmen wird.
*   Der geplante Standort des Serverschranks in Raum 0.12 hat nicht ausreichende Lüftung.
*   Als Alternative wird Raum 0.14 vorgeschlagen, da dieser größer ist und ein Fenster nach Norden besitzt.
*   Frau Petersen wird die Änderung beim Architekten veranlassen; dies soll bis Ende nächster Woche erledigt sein.

#### Zeitplanübersicht
*   Der Umzugstermin bleibt vorerst bei Mitte Dezember, sofern der Estrich mitspielt.

### Entscheidungen
*   Die Beauftragung zusätzlicher Trocknungsgeräte für 1.850 Euro netto wird vereinbart, um die Verzögerung von einer Woche einzuholen.
*   Der Standort des Serverschranks wird auf Raum 0.14 geändert.

### Offene Aufgaben
*   Nachtragsangebot für zwei zusätzliche Netzwerkdosen im Erdgeschoss erstellen — Verantwortlich: Herr Yılmaz, Deadline: nächsten Dienstag
*   Änderung des Serverstandorts beim Architekten veranlassen (von Raum 0.12 auf Raum 0.14) — Verantwortlich: Frau Petersen, Deadline: Ende nächster Woche

### Nächster Termin
Donnerstag, 9. Dezember um 9 Uhr auf der Baustelle
```

**Vokabular-Extraktion** — 7.4 s, erstes Zeichen nach 3.3 s, 42 Tokens

```text
["Petersen", "Yilmaz", "Elektro Hansen", "Nordlicht Systems", "I-Log-Schließanlage", "Werftstraße", "Kiel", "Telekom"]
```

### prism-ml/bonsai-27b · Prozessor

**Blitzdiktat+** — 51.2 s, erstes Zeichen nach 10.1 s, 130 Tokens

```text
Sehr geehrte Frau Petersen,

ich schreibe Ihnen erneut bezüglich der Schließanlage. In unserer letzten Gespräch wir haben über die Bestellung von I-Log-Zylindern für die Außentüren gesprochen. Es ist leider so, dass die Lieferzeit im Moment bei sechs Wochen liegt. Das bedeutet, falls wir die Bestellung nicht noch in dieser Woche absetzen, wird das Einzug bis Dezember nicht möglich sein.

Können Sie mir bitte bis Freitag bestätigen, ob wir die vierzehn Zylinder wie im Angebot bestellen sollen oder sich dort bereits Änderungen ergeben haben?

Mit freundlichen Grüßen
Jan Hansen
```

**Blitzdiktat $%&!** — 62.5 s, erstes Zeichen nach 11.3 s, 160 Tokens, fehlt: Gutschrift

```text
Ich verstehe Ihre Frustration. Sie benötigen die Server bis zum Mittwoch, um ihre Teammitglieder zu unterstützen und die Umzüge fortzuführen. Die verzögerte Lieferung und das Fehlen einer vorherigen Benachrichtigung sind für Sie ein kritisches Problem, da es Ihre Planung und Ressourcen stark beeinträchtigt.

Ich möchte sicherstellen, dass Sie eine Lösung erhalten, die diese Zeitverlängerung verhindert. Bitte teilen Sie mir mit:
1. Was ist der genaue Termin, bis dem zum Mittwoch, bis das Produkt bei Ihnen ankommt?
2. Welche konkreten Schritte können wir heute sofort ausführen, um diesen Termin einzuhalten?

Ich werde mich damit sofort beschäftigen, um die Situation zu lösen und sicherzustellen, dass Sie Ihre Anforderungen erfüllt bekommen.
```

**Blitzdiktat :)** — 36.9 s, erstes Zeichen nach 8.8 s, 90 Tokens, fehlt: 16

```text
moin zusammen kurze info 🌞 das sommerfest findet dieses Jahr am zwölzten juni ab sechzehn uhr auf dembetriebshof statt 📍 es gibt gegrilltes und kalte getränke 🍔🥤 und für die kinder eine hüpfburg 👧👦 bitte tragt euch bis ende mai in die liste ein 💌 damit wir planen können wir freuen uns auf euch! 😊
```

**Protokoll** — 261.5 s, erstes Zeichen nach 28.4 s, 690 Tokens, fehlt: 1.850, 0.14, 01.12.2026, 10.12.2026

```text
**Datum:** Donnerstag, 26.11.2026
**Thema:** Bautechnische und IT-Planungsbesprechung für Projektstruktur und Infrastruktur
**Teilnehmer:** Frau Petersen (Bauleitung), Herr Yilmaz (Elektro), Herr Brandt (Tiefbau – abgesagt)

---

### Zusammenfassung
Es wurde eine Besprechung über die Bautechnik, Elektro- und IT-Infrastrukturen für ein Bauprobekt geführt. Die Hauptprobleme betreffen Feuchte in Hall 2, die Anpassung von Netzdosen im Erdgeschoss sowie die Planung der Glasfaser-Hausanschluss und des Serverschrankes. Es wurden Maßnahmen zur Beseitigung der Feuchte, Nachtragsanfragen für Elektro-Netze und Planänderungen für IT-Räume abgehandelt. Ein weiterer Termin wurde auf den nächsten Donnerstag festgelegt.

### Besprochene Punkte
**Feuchte in Hall 2:**
- Der Bodenbelag liegt aktuell bei 2,8 % Feuchte. Ziel ist unter 2,0 %.
- Es wird eine Woche benötigt, bis der Bodenbelag wieder reinholbar ist.
- Ein Angebot für zusätzliche Trocknungsgeräte wurde eingeholt: 1.650 € netto für zwei Wochen.
- Die Beauftragung erfolgt heute.

**Elektro:**
- Im Erdgeschoss wurden ursprünglich 12 Netzdosen geplant. Aufgrund neuer Arbeitsplätze sind 14 Netzdosen nötig.
- Nachtragsangebot bis nächsten Dienstag zu senden.
- Leerrohre für Kameras an der Zufahrt sind bereits installed (3 Stück bis zum Mast).

**IT:**
- Glasfaser-Hausanschluss: Termin bestätigt auf den 9. Dezember vormittags.
- Serverschrank: Planung von Raum 0.1.2 und 0.1.4.
- Raum 0.1.2 hat unzureichende Lüftung; stattdessen wird Raum 0.1.4 (größer, Fenster nach Norden) gewählt.
- Planänderung an den Architekten bis Ende nächster Woche.

**Umzug:**
- Termin bleibt vorerst bei Mitte Dezember, falls Estrich mitspielt. Sonst später.

### Entscheidungen
- Beauftragung der zusätzlichen Trocknungsgeräte für zwei Wochen (1.650 € netto).
- Wahl von Raum 0.1.4 statt 0.1.2 für den Serverschrank aufgrund der Lüftung.
- Planänderung des IT-Raums an den Architekten bis Ende nächster Woche.

### Offene Aufgaben
- Nachtragsangebot für Netzdosen im Erdgeschoss: bis nächsten Dienstag – Verantwortlich: Herr Yilmaz, Deadline: –
- Glasfaser-Hausanschluss vor Ort prüfen: – Verantwortlich: –, Deadline: 9.12.2026 (vormittags)
- Planänderung des IT-Raums an den Architekten: bis Ende nächster Woche – Verantwortlich: –, Deadline: Ende nächster Woche

### Nächster Termin
Nächster Donnerstag, 2.12.2026, 9 Uhr auf der Baustelle
```

**Vokabular-Extraktion** — 27.8 s, erstes Zeichen nach 8.8 s, 61 Tokens

```text
[
  "Petersen",
  "Yilmaz",
  "Hansen",
  "Nordlicht Systems",
  "I-Log-Schließanlage",
  "Werftstraße",
  "Kiel",
  "Telekom"
]
```

### qwen3.5-2b · Grafikkarte (max)

**Blitzdiktat+** — 7.2 s, erstes Zeichen nach 2.6 s, 121 Tokens

```text
Hallo Frau Petersen,

ich wollte mich nochmals melden, um über die Schließanlage zu sprechen. Wir hatten letzte Woche darüber gesprochen: Die I-Log-Zylinder für die Außen-Türen sind noch nicht bestellt worden.

Das Problem ist, dass die Lieferzeit aktuell bei sechs Wochen liegt. Wenn wir diese Woche noch nicht bestellen, wird das nichts mehr mit dem Einzug Mitte Dezember bringen.

Könnten Sie mir bitte bis Freitag Bescheid geben, ob wir die vierzehn Zylinder so bestellen sollen wie im Angebot oder ob sich dort etwas geändert hat?

Viele Grüße
Jan Hansen
```

**Blitzdiktat :)** — 6.4 s, erstes Zeichen nach 2.5 s, 105 Tokens

```text
👋 Hallo zusammen! Hier ist eine kurze Info zum Sommerfest: 🎉 Das Fest findet dieses Jahr am 12. Juni ab 16 Uhr im Betriebshof statt. 🍖 Es gibt Grillmöglichkeiten und kalte Getränke für alle. 👶 Für die Kinder gibt es auch eine hüpfburg! 🏃‍♂️🧸 Tragt euch bis Ende Mai in die Liste ein, damit wir gemeinsam planen können. Wir freuen uns riesig auf euch! ✨
```

**Protokoll** — 29.7 s, erstes Zeichen nach 4.0 s, 666 Tokens, fehlt: 1.850, 0.14, 01.12.2026, 10.12.2026, 9 Uhr

```text
**Datum:** 26.11.2026, 14:30 Uhr
**Thema:** Besprechung Bauleitung (Petersen), Elektro (Yilmaz) und IT (Brandt) – Estrich, Netzwerkdosen, Glasfaseranschluss & Umzugstermin

### Zusammenfassung
Die aktuelle Besprechung dient der Überprüfung des Estrichprojekts in Halle 2. Frau Petersen meldet mangelhafte Restfeuchte (2,8 %), was eine Wochenaufschub bis zur Trocknung von 1.500 € erfordert. Herr Yilmaz bestätigt die Beauftragung dieser Trocknungsgeräte. In der IT-Besprechung wird festgelegt, dass der Glasfaser-Hausanschluss am 9. Dezember Vormittag vor Ort sein muss; da der Serverraum (Raum 0/1/2) nicht ausreichend lüftet ist, wird ein Raumwechsel auf den größeren Raum 0/1/4 an der Zufahrt vereinbart, der bis Ende nächster Woche bearbeitet werden soll. Der Umzugstermin bleibt zunächst für Mitte Dezember festgelegt.

### Besprochene Punkte
- **Estrich in Halle 2:** Die Restfeuchte liegt bei 2,8 %, was unter 2,0 % nicht reicht. Ein Angebot von 1.500 € (Netto) für zwei Wochen Trocknungsgeräte wurde eingeholt und beauftragt; die Trocknung wird wiederholt werden.
- **Elektro (Herr Yilmaz):** Der Bedarf an Netzwerkdosen im Büro Erdgeschoss hat sich von zwölf auf vierzehn erhöht, da ein neuer Empfangsraum mit zwei zusätzlichen Arbeitsplätzen entsteht. Ein Nachtragsangebot muss bis zum nächsten Dienstag geschickt werden.
- **IT (Herr Brandt):** Der Glasfaser-Hausanschluss wurde vom Telekom bestätigt und muss am 9. Dezember Vormittag vor Ort sein. Da der Serverraum nicht lüftet, wird ein Raumwechsel auf den größeren Raum 0/1/4 an der Zufahrt vereinbart; diese Änderung soll bis Ende nächster Woche bearbeitet werden.
- **Umzugstermin:** Der ursprüngliche Termin für Mitte Dezember bleibt bestehen, es sei denn, das Estrichprojekt wird abgeschlossen sein.

### Entscheidungen
- Trocknungsgeräte wurden beauftragt und wiederholt werden; der Estrich wird nicht sofort auf den Umzug vorbereitet.
- Raum 0/1/2 wird durch Raum 0/1/4 ersetzt; die Änderung wurde dem Architekten weitergegeben.
- Der Umzugstermin bleibt für Mitte Dezember festgelegt, bis weitere Informationen zum Estrich vorliegen.

### Offene Aufgaben
- **Elektro:** Nachtragsangebot für die zusätzlichen Netzwerkdosen (12 auf 14) muss bis zum nächsten Dienstag geschickt werden.
- **IT:** Der Glasfaser-Hausanschluss muss am 9. Dezember Vormittag vor Ort sein.

### Nächster Termin
Datum: 26.11.2026, 14:30 Uhr (aktuelle Besprechung)
```

### qwen3.5-2b · Prozessor

**Blitzdiktat+** — 9.1 s, erstes Zeichen nach 3.0 s, 136 Tokens

```text
Hallo Frau Petersen,

ich möchte mich nochmals melden, um über die Schließanlage zu sprechen. Wir hatten letzte Woche darüber gesprochen: Der I-Log-Zylinder für die Außentüren ist noch nicht bestellt worden.

Das Problem liegt daran, dass die Lieferzeit aktuell bei sechs Wochen beträgt. Wenn wir das nicht diese Woche noch auslösen, wird es dann nichts mehr mit dem Einzug Mitte Dezember bringen.

Könnten Sie mir bitte bis Freitag Bescheid geben:
1. Soll ich die vierzehn Zylinder so bestellen, wie im Angebot? Oder
2. Hat sich etwas geändert?

Vielen Dank schon mal und viele Grüße, Jan Hansen
```

**Blitzdiktat $%&!** — 15.4 s, erstes Zeichen nach 3.0 s, 277 Tokens, fehlt: Gutschrift, Server

```text
Hier ist die formulierte Nachricht:

**Betreff: Dringende Frist zum Liefertermin – Gefahr des Vertragsabbruchs**

Sehr geehrte Damen und Herren,

ich möchte mich hiermit über den aktuellen Stand der Dinge informieren. Es hat sich bereits dreimal ergeben, dass unser Lieferant den vereinbarten Termin verschiebt, ohne vorherige Ankündigung zu geben.

Wir haben uns für Montag zugesagt. Heute erhalten wir jedoch eine lapidare E-Mail mit der Ankündigung, dass der Auftrag noch zwei Wochen dauert. Diese Verzögerung ist absolut unangemessen und stellt ein Missvertrauen in unsere Absprachen dar.

Da wir drei Personen dabei sind, die den Umzug durchführen sollen, besteht das Risiko, dass wir diese Dienstleister nicht mehr bis zum nächsten Mittwoch liefern können. Ohne eine klare Frist oder eine Erklärung für diese Verzögerung verlieren wir die Möglichkeit, diesen Auftrag zu beenden und uns auf einen neuen Anbieter umzusehen.

Ich bitte Sie daher dringend, sich in Kürze über den konkreten Termin und eine verbindliche Antwort zu informieren. Eine weitere Verschlechterung des Zustands der Dinge würde dazu führen, dass wir uns gezwungen sehen müssen, die Dienstleister auszusortieren – was nicht das gewünschte Ergebnis ist.

Vielen Dank für Ihre Aufmerksamkeit und Ihr Verständnis.
```

**Blitzdiktat :)** — 7.2 s, erstes Zeichen nach 2.9 s, 100 Tokens

```text
👋 Hallo zusammen! Hier ist eine kurze Info zum Sommerfest: 🎉 Es findet dieses Jahr am 12. Juni ab 16 Uhr im Betriebshof statt! 🏡 Es gibt Grillen und kalte Getränke 🍔🥤, und für die Kinder gibt es eine hüpfburg 🚽✨.

Tragt euch bis zum Ende Mai in die Liste ein, damit wir planen können! Wir freuen uns auf euch! 👋😊
```

**Protokoll** — 42.5 s, erstes Zeichen nach 5.2 s, 794 Tokens, fehlt: 1.850, 0.14, 01.12.2026, 10.12.2026, 9 Uhr, Yilmaz

```text
**Datum:** 26.11.2026, 14:30 Uhr  
**Thema:** Besprechung Bauleitung, Elektro und IT – Estrich, Netzwerkdosen, Glasfaseranschluss & Umzugstermin  

### Zusammenfassung
Die Besprechung begann mit der Prüfung des Estriches in Halle zwei, wo Frau Petersen feststellte, dass die Restfeuchte zu hoch ist (2,8 %), was eine Wochenaufschubbedingung für den Bodenbelag darstellt. Ein Angebot von 1.500 € netto für Trocknungsgeräte wurde akzeptiert und wird heute noch beauftragt. Im Büro ergab sich ein Nachtrag zur Elektroinstallation: Die Anzahl der Netzwerkdosen muss von zwölf auf vierzehn erhöht werden, da neue Arbeitsplätze entstehen; dies wird in einem Nachtragsangebot bis zum nächsten Dienstag übermittelt. Für die IT-Infrastruktur bestätigte Telekom den Termin für den Glasfaser-Hausanschluss am 9. Dezember vormittags, wobei das ursprüngliche Planungsraum (01/02) aufgrund mangelnder Lüftung durch Raum 01/04 ersetzt wird, welches größer und nach Norden orientiert ist – eine Änderung wird an die Architekten weitergegeben. Der geplante Umzugstermin bleibt zunächst auf Mitte Dezember verlegt; ein erneuter Termin wird in zwei Wochen am Donnerstag um 14:30 Uhr vereinbart.

### Besprochene Punkte
- **Estrich (Halle zwei):** Die Restfeuchte liegt bei 2,8 %, was unter 2,0 % liegen muss, bevor der Bodenbelag installiert werden kann. Ein Zuschuss von 1.500 € für Trocknungsgeräte wurde beauftragt und wird heute noch erstellt.
- **Elektro (Büro Erdgeschoss):** Die geplante Anzahl an Netzwerkdosen hat sich geändert: Von zwölf auf vierzehn, da zwei neue Arbeitsplätze entstehen. Ein Nachtragsangebot bis zum nächsten Dienstag wird geschickt.
- **IT-Anschluss:** Telekom bestätigt den Termin für den Glasfaser-Hausanschluss am 9. Dezember vormittags. Das ursprüngliche Planungsraum (01/02) wurde durch einen größeren Raum (01/04) ersetzt, der nach Norden orientiert ist und eine Lüftung hat; die Änderung wird an die Architekten weitergegeben.
- **Umzugstermin:** Der ursprüngliche Termin für den Umzug war Mitte Dezember. Da der Estrich noch nicht fertiggestellt ist, wurde dieser auf einen Folgetermin in zwei Wochen am Donnerstag um 14:30 Uhr verschoben.

### Entscheidungen
- Die Trocknungsgeräte werden beauftragt und das Angebot wird erstellt.
- Der Nachtrag zur Elektroinstallation (Dosenanzahl) wird bis zum nächsten Dienstag übermittelt.
- Das Raumplanungsänderungsantrag für den Glasfaseranschluss wird an die Architekten weitergegeben.
- Der Umzugstermin wurde auf 2 Wochen später verschoben, da der Estrich noch nicht abgeschlossen ist.

### Offene Aufgaben
- **Elektro:** Erstellung des Nachtragsangebots (Dosenanzahl) bis zum nächsten Dienstag.
- **Architekten:** Weitergabe des Raumplanungsänderungsantrags für den Glasfaseranschluss.
- **Umzug:** Keine Deadline festgelegt, da der Estrich noch nicht fertiggestellt ist; Termin wurde auf 2 Wochen später verschoben.

### Nächster Termin
**Datum:** Donnerstag, 29.11.2026  
**Uhrzeit:** 14:30 Uhr  
**Anlass:** Besprechung Bauleitung, Elektro und IT (Folgetermin nach Verschiebung)
```

**Vokabular-Extraktion** — 6.2 s, erstes Zeichen nach 3.0 s, 71 Tokens

```text
[["Frau Petersen", "Bauleitung"], ["Herrn Yilmaz", "Elektro Hansen"], ["Firma Nordlicht Systems"], ["I-Log-Schließanlage"], ["Neubau an der Werftstraße in Kiel"], ["Telekom"], ["Glasfaseranschluss"], ["9. Dezember"]]
```

### qwen3.5-4b · Grafikkarte (max)

**Blitzdiktat+** — 28.2 s, erstes Zeichen nach 6.0 s, 128 Tokens

```text
Sehr geehrte Frau Petersen,

ich möchte mich bezüglich der Schließanlage nochmals melden. Wie letzte Woche besprochen, sind die I-Log-Zylinder für die Außentüren noch nicht bestellt worden. Das Problem besteht darin, dass die Lieferzeit derzeit etwa sechs Wochen beträgt. Falls wir diese Bestellung nicht in dieser Woche auslösen, wird es mit dem Einzug Mitte Dezember zu spät sein.

Könnten Sie mir bitte bis Freitag Bescheid geben, ob wir die 14 Zylinder entsprechend dem Angebot bestellen sollen oder ob sich dies geändert hat?

Vielen Dank im Voraus und viele Grüße
Jan Hansen
```

**Blitzdiktat :)** — 23.3 s, erstes Zeichen nach 4.8 s, 115 Tokens

```text
Moin zusammen! 👋 Hier ist kurz die Info: Das Sommerfest findet dieses Jahr am **12. Juni** ab **16 Uhr** auf dem Betriebshof statt. 📅⏰🔥

Es gibt gegrilltes Essen 🍖 und kalte Getränke 🥤, sowie für die Kinder eine Hüpfburg! 🎠👶

Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können. 📝✅

Wir freuen uns auf euch! 😊🙌
```

**Protokoll** — 147.8 s, erstes Zeichen nach 16.7 s, 776 Tokens, fehlt: 1.850, 0.14, 01.12.2026, 10.12.2026

```text
**Datum:** 26.11.2026
**Thema:** Baubesprechung zur Fortsetzung der Bauarbeiten (Estrich, Elektro, IT)
**Teilnehmer:** Frau Petersen (Bauleitung), Herr Yilmaz (Elektro), Herr Brandt (IT)

---

### Zusammenfassung
Die Besprechung fand am 26.11.2026 auf der Baustelle statt und wurde von Frau Petersen, Herrn Yilmaz und Herrn Brandt geführt. Der Hauptfokus lag auf der Lösung einer Restfeuchte-Problematik im Estrichbereich von Halle zwei, die eine Verzögerung des Bodenbelags um eine Woche verursachte; zur Beschleunigung wurden zusätzliche Trocknungsgeräte beauftragt. Parallel wurde ein Nachtragsbedarf für vier weitere Netzwerkdosen im Büro ermittelt und der Glasfaser-Hausanschluss mit einem Termin am 9.12.2026 festgelegt, wobei der Serverstandort aufgrund unzureichender Lüftung in Raum 0.1.4 verlegt wird. Der Umzugstermin bleibt vorerst bei Mitte Dezember bestehen, und für die nächste Besprechung wurde ein Termin am 30.12.2026 um 09:00 Uhr auf der Baustelle vereinbart.

### Besprochene Punkte
- **Estrich in Halle zwei:** Die Restfeuchte liegt aktuell bei 2,8 %. Zielwert für den Bodenbelag ist unter 2,0 %. Ein Angebot für zusätzliche Trocknungsgeräte (1.805 € netto) wurde genehmigt und beauftragt, um die Trocknungsdauer auf eine Woche zu verkürzen.
- **Elektro im Büro Erdgeschoss:** Der Bedarf an Netzwerkdosen erhöht sich von 12 auf 14 Stück aufgrund neuer Arbeitsplätze am Empfang. Ein Nachtragsangebot wird bis Dienstag erstellt. Die Leerrohre für Kameras an der Zufahrt sind vorhanden (3 Stück bis zum Mast).
- **IT – Glasfaser-Hausanschluss:** Der Termin mit der Telekom wurde bestätigt (09.12.2026, Vormittag) und Herr Brandt übernimmt die Vor-Ort-Besichtigung.
- **IT – Serverstandort:** Der ursprünglich geplante Standort Raum 0.1.2 ist aufgrund unzureichender Lüftung nicht geeignet. Es wurde der größere Raum 0.1.4 mit Fenster nach Norden gewählt. Frau Petersen wird den Architekten über die Änderung informieren; Ziel ist die Umsetzung bis Ende nächste Woche.
- **Umzugstermin:** Der Termin bleibt vorerst bei Mitte Dezember bestehen, sofern sich nichts am Estrich-Projekt ändert.

### Entscheidungen
- Beauftragung von zusätzlichen Trocknungsgeräten für Halle zwei (1.805 € netto).
- Verlegung des Serverstandorts von Raum 0.1.2 auf Raum 0.1.4.
- Festlegung des Glasfaser-Hausanschluss-Termins auf den 9.12.2026.

### Offene Aufgaben
- Erstellung und Versand eines Nachtragsangebots für die vier zusätzlichen Netzwerkdosen (Deadline: Nächster Dienstag).
- Änderung der Raumbezeichnung im Plan durch Frau Petersen an den Architekten (Ziel: Ende nächste Woche).
- Vor-Ort-Besichtigung des Glasfaser-Hausanschlusses am 9.12.2026 (Verantwortlich: Herr Brandt).

### Nächster Termin
30.12.2026, 09:00 Uhr auf der Baustelle
```

### qwen3.5-4b · Prozessor

**Blitzdiktat+** — 16.6 s, erstes Zeichen nach 4.4 s, 127 Tokens

```text
Sehr geehrte Frau Petersen,

ich möchte mich bezüglich der Schließanlage nochmals melden. Wie letzte Woche besprochen, sind die I-Log-Zylinder für die Außentüren noch nicht bestellt worden. Das Problem ist derzeit, dass die Lieferzeit bei etwa sechs Wochen liegt. Falls wir diese Bestellung nicht in dieser Woche auslösen, wird es mit dem Einzug Mitte Dezember zu spät sein.

Könnten Sie mir bitte bis Freitag Bescheid geben, ob wir die vierzehn Zylinder wie im Angebot bestellen sollen oder ob sich dies geändert hat?

Vielen Dank im Voraus und viele Grüße
Jan Hansen
```

**Blitzdiktat $%&!** — 24.8 s, erstes Zeichen nach 4.3 s, 208 Tokens, fehlt: Gutschrift, Server

```text
Sehr geehrte Damen und Herren,

ich muss Ihre bisherige Kommunikation als unprofessionell und extrem frustrierend bewerten. Es ist bereits das dritte Mal, dass Sie Termine ohne vorherige Absprache verschieben – zuletzt haben Sie uns für Montag zugesichert, uns erst am Donnerstag mit einer Ankündigung von zwei Wochen Verzögerung unterrichtet. Dieses Vorgehen wirkt nicht nur unhöflich, sondern unterstellt uns ein mangelndes Vertrauen in Ihre Zuverlässigkeit.

Die Situation ist dringend: Drei Mitarbeiter warten bereits auf den Umzug und sind ohne Arbeitsplätze. Sollte die Lieferung bis Mittwochabend nicht erfolgen, werde ich keine weiteren Ausnahmen mehr zulassen; die betroffenen Mitarbeiter werden unverzüglich entlassen, da ihre Aufgaben nicht erfüllt werden können. Zudem fordere ich eine sofortige schriftliche Bestätigung des Zahlungseingangs für die entstandenen Kosten sowie eine Entschuldigung für dieses Verhalten.

Ich erwarte Ihre verbindliche Antwort und den konkreten Liefertermin bis morgen früh.
```

**Blitzdiktat :)** — 15.7 s, erstes Zeichen nach 3.9 s, 117 Tokens

```text
Moin zusammen! 👋 Hier ist kurz die Info: Das Sommerfest findet dieses Jahr am **12. Juni** ab **16 Uhr** auf dem Betriebshof statt. 🏃‍♂️🌳

Es gibt gegrilltes Essen 🍖 und kalte Getränke 🥤, sowie für die Kinder eine Hüpfburg! 🎠👧👦

Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können. 📝✅ Wir freuen uns auf euch! 😊✨
```

**Protokoll** — 94.3 s, erstes Zeichen nach 9.3 s, 813 Tokens, fehlt: 1.850, 0.14, 01.12.2026, 10.12.2026

```text
**Datum:** 26.11.2026
**Thema:** Baubesprechung Halle zwei, Büro und IT-Infrastruktur
**Teilnehmer:** Frau Petersen (Bauleitung), Herr Yilmaz (Elektro), Herr Brandt (IT)

---

### Zusammenfassung
Die Besprechung fand am 26.11.2026 auf der Baustelle statt, um Fortschritte bei Estrich, Elektroinstallation und IT-Infrastruktur zu besprechen. Die Restfeuchte im Estrich von Halle zwei lag bei 2,8 %, was eine Verzögerung von einer Woche bedeutetete; zur Beschleunigung wurden zusätzliche Trocknungsgeräte für zwei Wochen beauftragt (1.805 € netto). Für das Büro im Erdgeschoss mussten aufgrund neuer Arbeitsplätze vier weitere Netzwerkdosen eingebaut werden, was ein nachträgliches Angebot bis Dienstag erfordert. Der Glasfaser-Hausanschluss der Telekom ist für den 9.12.2026 fixiert und benötigt eine Vor-Ort-Besprechung durch IT. Zudem wurde der Standort des Serverschranks von Raum 0.1.2 auf Raum 0.1.4 verlegt, da die Lüftung im alten Raum unzureichend ist; dies soll bis Ende nächster Woche geklärt werden. Der Umzugstermin bleibt vorerst bei Mitte Dezember stehen. Als Nächste Schritte wurden das Beauftragen der Trocknungsgeräte, die Erstellung des Nachtragsscheins für Elektro und die Anpassung des Bauplans bezüglich des Serverschranks festgelegt.

### Besprochene Punkte
- **Estrich Halle zwei:** Die Restfeuchte lag bei 2,8 %. Ziel ist unter 2,0 %, um den Bodenbelag zu montieren. Ohne Maßnahmen wird eine Verzögerung von einer Woche erwartet. Ein Angebot für zusätzliche Trocknungsgeräte (2 Wochen) wurde mit 1.805 € netto erarbeitet und beauftragt.
- **Elektro (Büro Erdgeschoss):** Ursprünglich waren 12 Netzwerkdosen geplant, nun sind 14 notwendig (durch zwei neue Arbeitsplätze im Empfang). Ein Nachtragsschein wird erstellt und bis Dienstag eingereicht. Die Leerrohre für Kameras an der Zufahrt sind bereits installiert (3 Stück bis zum Mast).
- **IT (Glasfaser & Server):** Der Glasfaser-Hausanschluss der Telekom ist für den 9.12.2026 vormittags bestätigt; IT übernimmt die Vor-Ort-Besprechung. Der geplante Serverschrank in Raum 0.1.2 ist aufgrund unzureichender Lüftung nicht geeignet. Als Ersatz wurde Raum 0.1.4 gewählt (größer, Fenster nach Norden). Die Planänderung soll bis Ende nächster Woche erfolgen.
- **Umzugstermin:** Bleibt vorerst bei Mitte Dezember stehen, sofern der Estrich-Fortschritt dies zulässt.

### Entscheidungen
- Trocknungsgeräte für Halle zwei beauftragen (2 Wochen, 1.805 € netto).
- Raum 0.1.4 als neuen Standort für den Serverschrank festlegen.
- Umzugstermin bleibt bei Mitte Dezember stehen.

### Offene Aufgaben
- Nachtragsschein für vier zusätzliche Netzwerkdosen erstellen und bis Dienstag einreichen — Verantwortlich: Herr Yilmaz, Deadline: Nächster Dienstag.
- Planänderung bezüglich des Serverschranks (Raum 0.1.2 auf 0.1.4) an den Architekten weitergeben — Verantwortlich: Frau Petersen, Deadline: Ende nächster Woche.

### Nächster Termin
Donnerstag, 9.12.2026 um 09:00 Uhr auf der Baustelle
```

**Vokabular-Extraktion** — 8.1 s, erstes Zeichen nach 3.9 s, 44 Tokens

```text
["Petersen", "Yilmaz", "Elektro Hansen", "Nordlicht Systems", "I-Log-Schließanlage", "Werftstraße", "Kiel", "Telekom"]
```

### qwen/qwen3.5-9b · Grafikkarte (0.5)

**Blitzdiktat+** — 31.1 s, erstes Zeichen nach 8.8 s, 118 Tokens

```text
Sehr geehrte Frau Petersen,

ich möchte mich bezüglich der Schließanlage nochmals bei Ihnen melden. Wie letzte Woche besprochen, sind die I-Log-Zylinder für die Außentüren noch nicht bestellt. Da die aktuelle Lieferzeit etwa sechs Wochen beträgt, müssen wir den Auftrag in dieser Woche erteilen, damit der Einzug Mitte Dezember möglich ist.

Könnten Sie mir bitte bis Freitag mitteilen, ob wir die vierzehn Zylinder wie im Angebot bestellen sollen oder sich diesbezüglich etwas geändert hat?

Vielen Dank und viele Grüße
Jan Hansen
```

**Blitzdiktat :)** — 27.5 s, erstes Zeichen nach 7.3 s, 111 Tokens

```text
Moin zusammen! 🙋‍♂️ Kurze Info: Das Sommerfest findet dieses Jahr am 12. Juni ab 16 Uhr auf dem Betriebshof statt! ☀️🍖 Es gibt gegrilltes Fleisch und kalte Getränke 🥩🥤, und für die Kinder eine Hüpfburg! 🎈🦕 Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können. ✍️📅 Wir freuen uns auf euch! 👋😊
```

### qwen/qwen3.5-9b · Prozessor

**Blitzdiktat+** — 23.4 s, erstes Zeichen nach 5.8 s, 116 Tokens

```text
Sehr geehrte Frau Petersen,

ich möchte mich bezüglich der Schließanlage nochmals bei Ihnen melden. Wie letzte Woche besprochen, sind die I-Log-Zylinder für die Außentüren noch nicht bestellt worden. Da die aktuelle Lieferzeit etwa sechs Wochen beträgt, wäre eine Bestellung in dieser Woche notwendig, um den Einzug Mitte Dezember sicherzustellen.

Könnten Sie mir bitte bis Freitag mitteilen, ob wir die 14 Zylinder wie im Angebot bestellen sollen oder sich hierin etwas geändert hat?

Vielen Dank und viele Grüße
Jan Hansen
```

**Blitzdiktat $%&!** — 26.2 s, erstes Zeichen nach 5.9 s, 133 Tokens

```text
Wir haben erneut einen Lieferterminverschiebung ohne Vorwarnung erfahren: Der ursprünglich für Montag zugesagte Server-Lieferung wurde heute, am Donnerstag, mit einer Zwei-Wochen-Frist zurückgewiesen. Dies ist das dritte Mal in dieser Folge. Da wir drei Mitarbeiter seitdem auf den Umzug warten und keine weiteren Ressourcen bereitstellen können, müssen wir eine sofortige Lösung finden. Bitte bestätigen Sie uns bis nächsten Mittwoch zwingend die Lieferung des Servers oder erteilen Sie uns schriftlich eine Gutschrift für den entstandenen Aufwand. Ohne diese Bestätigung werden wir den Auftrag ablehnen. Wir erwarten Ihre dringende Rückmeldung.
```

**Blitzdiktat :)** — 21.2 s, erstes Zeichen nach 5.2 s, 105 Tokens

```text
Moin zusammen! 👋 Kurze Info: Das Sommerfest findet dieses Jahr am 12. Juni ab 16 Uhr auf dem Betriebshof statt 🏡🍖. Es gibt gegrilltes Essen und kalte Getränke 🥩🥤, und für die Kinder eine Hüpfburg 🎈🧒. Bitte tragt euch bis Ende Mai in die Liste ein, damit wir planen können 📝✅. Wir freuen uns auf euch! 😊🎉
```

**Protokoll** — 147.0 s, erstes Zeichen nach 13.8 s, 820 Tokens, fehlt: 0.14, 01.12.2026, 10.12.2026

```text
**Datum:** 26.11.2026
**Thema:** Baustellenstatus Halle 2, Elektroinstallationen und IT-Infrastruktur
**Teilnehmer:** Frau Petersen (Bauleitung), Herr Yilmaz (Elektro), Ich (IT)

---

### Zusammenfassung
Die Besprechung diente der Abstimmung des aktuellen Status auf der Baustelle mit Fokus auf den Estrich in Halle 2, die Elektroinstallation im Erdgeschoss und die IT-Infrastruktur. Es wurde festgestellt, dass die Restfeuchte im Estrich von Halle 2 bei 2,8 % liegt und vor dem Verlegen des Bodenbelags unter 2,0 % gesenkt werden muss, was aktuell eine Verzögerung von einer Woche bedeutet. Um diese Verzögerung auszugleichen, wurde ein Angebot für zusätzliche Trocknungsgeräte (1.850 € netto für zwei Wochen) angenommen und beauftragt. Zudem wurden Änderungen bei der Netzwerkdosenplanung im Büro sowie die Verlegung des Serverschrankes in einen besser gelüfteten Raum besprochen. Die Glasfaser-Anschlussverlegung durch Telekom ist für den 09.12.2026 terminiert, wobei der IT-Verantwortliche vor Ort sein wird. Der Umzugstermin bleibt vorerst Mitte Dezember stehen, sofern die Estricharbeiten pünktlich abgeschlossen werden können.

### Besprochene Punkte

**Estrich in Halle 2**
*   Aktuelle Restfeuchte liegt bei 2,8 %; Zielwert für Bodenbelag-Verlegung ist unter 2,0 %.
*   Ohne Trocknung entsteht eine Verzögerung von einer Woche.
*   Angebot für zusätzliche Trocknungsgeräte: 1.850 € netto für zwei Wochen (kostet die Verzögerung aus).

**Elektroinstallationen**
*   Büro Erdgeschoss: Anzahl der Netzwerkdosen muss von ursprünglich 12 auf 14 erhöht werden, da der Empfang zwei weitere Arbeitsplätze erhält.
*   Leerrohre für Kameras an der Zufahrt (3 Stück bis zum Mast) sind verlegt und fertiggestellt.

**IT-Infrastruktur und Planung**
*   Glasfaser-Hausanschluss: Termin durch Telekom bestätigt für den 09.12.2026 vormittags. IT-Verantwortlicher übernimmt Vor-Ort-Präsenz.
*   Serverschrank: Ursprünglich in Raum 0.1.2 geplant, jedoch aufgrund unzureichender Lüftung verlegt auf Raum 0.1.4 (größer, Fenster nach Norden).
*   Umzugstermin bleibt vorerst bei Mitte Dezember stehen; Anpassung erfolgt erst, wenn Estrich-Termin verschoben wird.

### Entscheidungen
*   Beauftragung der zusätzlichen Trocknungsgeräte für Halle 2 mit Kosten von 1.850 € netto für zwei Wochen zur Kompensation der Verzögerung.
*   Erstellung eines Nachtragsangebots für die vier zusätzlichen Netzwerkdosen im Büro Erdgeschoss.
*   Änderung des Planes durch den Architekten: Verlegung des Serverschrankes von Raum 0.1.2 auf Raum 0.1.4.

### Offene Aufgaben
*   Beauftragung der Trocknungsgeräte — Verantwortlich: Ich (IT), Deadline: Heute.
*   Erstellung und Versand des Nachtragsangebots für die Netzwerkdosen — Verantwortlich: Herr Yilmaz, Deadline: Nächster Dienstag.
*   Änderung des Plans durch den Architekten (Raum 0.1.4) — Verantwortlich: Frau Petersen, Deadline: Ende nächster Woche.

### Nächster Termin
Donnerstag, 09.12.2026, 09:00 Uhr, Baustelle
```

**Vokabular-Extraktion** — 11.8 s, erstes Zeichen nach 5.3 s, 44 Tokens

```text
["Petersen", "Yilmaz", "Elektro Hansen", "Nordlicht Systems", "I-Log-Schließanlage", "Werftstraße", "Kiel", "Telekom"]
```
