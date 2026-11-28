# Copyright (c) 2026 Thorben Meier. MIT License.
"""Deutsche Beispiel-Diktate für den Modellvergleich.

Die Texte sind so geschrieben, wie Whisper sie liefert: ohne saubere
Interpunktion, mit Füllwörtern und Verhörern. Alle Namen und Vorgänge sind
frei erfunden. Jede Probe nennt Prüfwörter, die im Ergebnis stehen müssen
(`muss`) bzw. nicht stehen dürfen (`darf_nicht`).
"""

AUFNAHMEDATUM = "Donnerstag, 26.11.2026"

VERBESSERN = (
    "ähm hallo frau petersen also ich wollte mich nochmal melden wegen der schließanlage "
    "wir hatten ja letzte woche drüber gesprochen dass die ei log zylinder für die außentüren "
    "noch nicht bestellt sind und ähm das problem ist halt dass die lieferzeit im moment so bei "
    "sechs wochen liegt das heißt wenn wir das nicht diese woche noch auslösen dann wird das nix "
    "mehr mit dem einzug mitte dezember könnten sie mir bitte bis freitag bescheid geben ob wir "
    "die vierzehn zylinder so bestellen sollen wie im angebot oder ob sich da noch was geändert "
    "hat danke schon mal und viele grüße jan hansen"
)

DAMPF = (
    "also ich fass es nicht das ist jetzt das dritte mal dass der lieferant den termin verschiebt "
    "ohne uns bescheid zu sagen die haben uns für montag die server zugesagt und heute am "
    "donnerstag krieg ich ne lapidare mail dass es noch zwei wochen dauert das ist eine absolute "
    "frechheit die halten uns doch für blöd ich hab hier drei leute rumsitzen die den umzug machen "
    "sollten und die kann ich jetzt nach hause schicken wenn die das nicht bis nächsten mittwoch "
    "liefern dann können die ihren auftrag vergessen und ich will eine gutschrift für den ganzen "
    "ärger sonst sehen die von uns keinen cent mehr"
)

EMOJI = (
    "moin zusammen kurze info das sommerfest findet dieses jahr am zwölften juni ab sechzehn uhr "
    "auf dem betriebshof statt es gibt gegrilltes und kalte getränke und für die kinder eine "
    "hüpfburg bitte tragt euch bis ende mai in die liste ein damit wir planen können wir freuen "
    "uns auf euch"
)

PROTOKOLL = (
    "so dann fangen wir mal an guten morgen zusammen frau petersen von der bauleitung herr yilmaz "
    "vom elektro und ich für die it sind da herr brandt vom tiefbau hat abgesagt erster punkt "
    "estrich in halle zwei frau petersen wie sieht es aus ja leider nicht gut die restfeuchte "
    "liegt aktuell bei zwei komma acht prozent wir brauchen unter zwei komma null bevor der "
    "bodenbelag rein kann das heißt wir verlieren da eine woche ich habe ein angebot für "
    "zusätzliche trocknungsgeräte eingeholt das wären eintausendachthundertfünfzig euro netto "
    "für zwei wochen dann würden wir die woche wieder reinholen okay das machen wir das beauftragen "
    "wir so einverstanden dann beauftrage ich das heute noch zweiter punkt elektro herr yilmaz ja "
    "also im büro im erdgeschoss waren ursprünglich zwölf netzwerkdosen geplant nach der letzten "
    "begehung brauchen wir vierzehn weil der empfang zwei zusätzliche arbeitsplätze bekommt das "
    "ist kein großer aufwand aber ich muss ein nachtragsangebot schreiben das schicke ich bis "
    "nächsten dienstag gut und die leerrohre für die kameras an der zufahrt sind die drin die "
    "sind drin ja drei stück bis zum mast dritter punkt it also der glasfaser hausanschluss die "
    "telekom hat den termin bestätigt das ist der neunte dezember vormittags da muss jemand vor "
    "ort sein das übernehme ich dann zum serverschrank der war in raum null punkt eins zwei "
    "geplant da ist aber die lüftung nicht ausreichend wir haben uns das angeschaut und nehmen "
    "stattdessen raum null punkt eins vier der ist größer und hat ein fenster nach norden frau "
    "petersen können sie das im plan ändern lassen ja das gebe ich an den architekten weiter "
    "sollte bis ende nächster woche erledigt sein gut dann noch der umzugstermin der bleibt "
    "vorerst bei mitte dezember wenn der estrich mitspielt sonst reden wir beim nächsten mal "
    "drüber gibt es noch was nein dann machen wir die nächste besprechung in zwei wochen wieder "
    "donnerstag neun uhr hier auf der baustelle danke euch"
)

VOKABULAR = (
    "Frau Petersen von der Bauleitung hat mit Herrn Yilmaz von Elektro Hansen und der Firma "
    "Nordlicht Systems über die I-Log-Schließanlage im Neubau an der Werftstraße in Kiel "
    "gesprochen. Die Telekom schaltet den Glasfaseranschluss am 9. Dezember."
)

# ---------------------------------------------------------------------------
# Runde 2: mehrere Proben je Aufgabe. `gesprochen` ist der Text, wie ihn ein
# Mensch sagt. sprechen.py lässt ihn von der Windows-Sprachausgabe vorlesen und
# vom Whisper-Modell der App transkribieren (→ transkripte.json). Damit bekommt
# das Sprachmodell genau die Art Text, die es in der App auch bekäme.
# ---------------------------------------------------------------------------

DAMPF_PROBEN = [
    dict(
        id="lieferant",
        gesprochen=(
            "Also ich fass es nicht. Das ist jetzt das dritte Mal, dass der Lieferant den Termin "
            "verschiebt, ohne uns Bescheid zu sagen. Die haben uns für Montag die Server zugesagt, "
            "und heute, am Donnerstag, krieg ich eine lapidare Mail, dass es noch zwei Wochen "
            "dauert. Das ist eine absolute Frechheit! Die halten uns doch für blöd. Ich hab hier "
            "drei Leute rumsitzen, die den Umzug machen sollten, und die kann ich jetzt nach Hause "
            "schicken. Wenn die das nicht bis nächsten Mittwoch liefern, dann können die ihren "
            "Auftrag vergessen. Und ich will eine Gutschrift für den ganzen Ärger, sonst sehen die "
            "von uns keinen Cent mehr."
        ),
        muss=[["Mittwoch"], ["Gutschrift"], ["Server"], ["dritte", "dreimal", "drei Mal", "3."],
              ["zwei Wochen", "2 Wochen"]],
        darf_nicht=["Frechheit", "blöd", "keinen Cent", "[", "verstehe Ihren", "Hier ist",
                    "entlassen", "Mehl", "Ehrge"],
    ),
    dict(
        id="ticket",
        gesprochen=(
            "Mensch, ich krieg echt die Krise. Der Kollege Brandt aus dem Vertrieb hat schon wieder "
            "ein Ticket aufgemacht, mit dringend, geht nix, und dann steht da nichts drin. Kein "
            "Gerät, keine Fehlermeldung, gar nichts. Das ist jetzt das fünfte Mal diesen Monat. Ich "
            "bin doch nicht sein persönlicher Hellseher! Ich renn dann jedes Mal hinterher und ruf "
            "an, und dann ist er nicht erreichbar. So ein Chaot. Der soll gefälligst das Formular "
            "ausfüllen wie alle anderen auch, mit Gerätename und Screenshot, sonst mach ich das "
            "Ticket einfach zu. Und er soll eine Rückrufnummer reinschreiben."
        ),
        muss=[["Formular"], ["Screenshot"], ["Gerätename", "Gerätenamen", "Namen des Geräts"],
              ["Rückrufnummer", "Telefonnummer"], ["fünfte", "fünfmal", "fünf Mal", "5."],
              ["schließen", "geschlossen", "nicht bearbeit"]],
        darf_nicht=["Hellseher", "Chaot", "Kaut", "gefälligst", "[", "verstehe Ihren", "Hier ist"],
    ),
    dict(
        id="heizung",
        gesprochen=(
            "Jetzt reicht es mir aber wirklich. Die Heizung im Büro im zweiten Stock ist seit "
            "Montag kalt, wir sitzen hier bei 16 Grad mit Jacke am Schreibtisch. Ich habe der "
            "Hausverwaltung zweimal gemailt und einmal angerufen, und jedes Mal heißt es, der "
            "Techniker kommt morgen. Der kommt aber nie! Das ist doch ein Saftladen. Wenn bis "
            "Freitag keiner da war, dann bestelle ich selber einen Heizungsbauer und schicke denen "
            "die Rechnung, und die Miete kürze ich auch. Ich will einen festen Termin mit Uhrzeit, "
            "und zwar schriftlich."
        ),
        muss=[["16"], ["Montag"], ["Freitag"], ["Rechnung", "Kosten"], ["Miet"],
              ["schriftlich"], ["Uhrzeit"]],
        darf_nicht=["Saftladen", "gemählt", "[", "verstehe Ihren", "Hier ist"],
    ),
    # Gegenprobe: erst geschrieben, nachdem die lokalen Prompts feststanden.
    dict(
        id="abrechnung",
        gesprochen=(
            "Das darf doch nicht wahr sein. Die Buchhaltung hat mir zum zweiten Mal die "
            "Reisekostenabrechnung zurückgeschickt, diesmal weil angeblich ein Beleg fehlt. Der "
            "Beleg war aber dran, ich habe das Foto selbst hochgeladen! Ich warte seit sechs "
            "Wochen auf 412 Euro. Die sollen sich das mal richtig angucken, statt alles einfach "
            "abzulehnen, diese Erbsenzähler. Ich will das Geld bis Ende der Woche auf dem Konto "
            "haben, und ich will wissen, wer das bearbeitet, damit ich nicht jedes Mal von vorne "
            "anfange."
        ),
        muss=[["zweiten", "zweimal", "zwei Mal", "erneut"], ["412"], ["sechs Wochen", "6 Wochen"],
              ["Beleg"], ["Ende der Woche", "Ende dieser Woche", "Freitag"],
              ["bearbeite", "zuständig", "Ansprechpartner", "Ansprechperson"]],
        darf_nicht=["Erbsenzähler", "[", "verstehe Ihren", "Hier ist"],
    ),
]

PROTOKOLL_PROBEN = [
    dict(
        id="bau",
        datum="2026-11-26",  # Donnerstag
        gesprochen=(
            "So, dann fangen wir mal an. Guten Morgen zusammen. Frau Petersen von der Bauleitung, "
            "Herr Yilmaz vom Elektro und ich für die IT sind da. Herr Brandt vom Tiefbau hat "
            "abgesagt. Erster Punkt: Estrich in Halle 2. Frau Petersen, wie sieht es aus? Ja, "
            "leider nicht gut. Die Restfeuchte liegt aktuell bei 2,8 Prozent, wir brauchen unter "
            "2,0, bevor der Bodenbelag rein kann. Das heißt, wir verlieren da eine Woche. Ich habe "
            "ein Angebot für zusätzliche Trocknungsgeräte eingeholt, das wären 1850 Euro netto für "
            "zwei Wochen. Dann würden wir die Woche wieder reinholen. Okay, das machen wir, das "
            "beauftragen wir so. Einverstanden, dann beauftrage ich das heute noch. Zweiter Punkt: "
            "Elektro. Herr Yilmaz? Ja, also im Büro im Erdgeschoss waren ursprünglich 12 "
            "Netzwerkdosen geplant. Nach der letzten Begehung brauchen wir 14, weil der Empfang "
            "zwei zusätzliche Arbeitsplätze bekommt. Das ist kein großer Aufwand, aber ich muss ein "
            "Nachtragsangebot schreiben. Das schicke ich bis nächsten Dienstag. Gut. Und die "
            "Leerrohre für die Kameras an der Zufahrt, sind die drin? Die sind drin, ja, drei Stück "
            "bis zum Mast. Dritter Punkt: IT. Also der Glasfaser-Hausanschluss. Die Telekom hat den "
            "Termin bestätigt, das ist der 9. Dezember vormittags. Da muss jemand vor Ort sein, das "
            "übernehme ich. Dann zum Serverschrank. Der war in Raum 0.12 geplant, da ist aber die "
            "Lüftung nicht ausreichend. Wir haben uns das angeschaut und nehmen stattdessen Raum "
            "0.14, der ist größer und hat ein Fenster nach Norden. Frau Petersen, können Sie das im "
            "Plan ändern lassen? Ja, das gebe ich an den Architekten weiter, sollte bis Ende "
            "nächster Woche erledigt sein. Gut. Dann noch der Umzugstermin, der bleibt vorerst bei "
            "Mitte Dezember, wenn der Estrich mitspielt. Sonst reden wir beim nächsten Mal drüber. "
            "Gibt es noch was? Nein. Dann machen wir die nächste Besprechung in zwei Wochen, wieder "
            "Donnerstag, 9 Uhr, hier auf der Baustelle. Danke euch."
        ),
        muss=[["2,8"], ["1.850", "1850"], ["14"], ["0.14", "0,14"],
              ["01.12.2026"], ["04.12.2026"], ["09.12.2026"], ["10.12.2026"],
              ["9 Uhr", "09:00", "9:00"],
              ["Petersen"], ["Jelmasch", "Yilmaz"], ["### Entscheidungen"],
              ["### Offene Aufgaben"], ["### Nächster Termin"]],
        reparatur=[["Erdgeschoss"], ["Leerrohr"]],
        darf_nicht=["[", "```", "Hier ist", "####", "\n* "],
    ),
    dict(
        id="it",
        datum="2027-02-02",  # Dienstag
        gesprochen=(
            "Okay, dann legen wir los. Heute dabei sind Frau Lorenz, Herr Aydin und ich. Erstes "
            "Thema: die Umstellung auf Windows 11. Herr Aydin, wie ist der Stand? Von den 86 "
            "Rechnern sind 61 umgestellt, es fehlen also noch 25. Davon sind 9 Geräte zu alt, die "
            "erfüllen die Anforderungen nicht und müssen ersetzt werden. Was kosten die? Ich habe "
            "ein Angebot, 9 Notebooks zu je 1140 Euro netto, also 10260 Euro. Gut, das bestellen "
            "wir, ich gebe das frei. Herr Aydin, bitte bestellen Sie die Geräte bis Freitag. Die "
            "restlichen 16 Rechner stellen wir bis Ende Februar um. Zweites Thema: Datensicherung. "
            "Frau Lorenz? Die Sicherung auf das NAS läuft seit letzter Woche wieder stabil. Der "
            "Fehler lag an einer vollen Festplatte, wir haben jetzt 40 Terabyte statt 24. Was noch "
            "fehlt, ist der Rücksicherungstest. Den mache ich übermorgen. Drittes Thema: die neue "
            "Telefonanlage. Der Anbieter hat den Umschalttermin verschoben, von nächstem Montag auf "
            "den 22. Februar. Das ist ärgerlich, aber wir können nichts machen. Ich informiere "
            "morgen die Abteilungsleiter. Sonst noch was? Nein. Dann sehen wir uns in drei Wochen "
            "wieder, gleicher Tag, gleiche Zeit, 14 Uhr."
        ),
        muss=[["25"], ["1.140", "1140"], ["10.260", "10260"], ["16"],
              ["05.02.2027"], ["28.02.2027"], ["04.02.2027"], ["08.02.2027"], ["03.02.2027"],
              ["23.02.2027"], ["14 Uhr", "14:00"], ["Lorenz"], ["Aydin"],
              ["### Entscheidungen"], ["### Offene Aufgaben"], ["### Nächster Termin"]],
        reparatur=[["61"], ["22.02.2027"], ["Terabyte", " TB"]],
        darf_nicht=["[", "```", "Hier ist", "####", "\n* "],
    ),
    dict(
        id="lager",
        datum="2026-12-18",  # Freitag
        gesprochen=(
            "Kurze Abstimmung zum Jahresabschluss im Lager. Die Inventur ist für den 29. Dezember "
            "angesetzt, Beginn 7 Uhr. Wir zählen dieses Jahr mit den neuen Handscannern. Davon "
            "haben wir 12 Stück, 3 sind noch in der Reparatur und sollen nächste Woche Mittwoch "
            "zurückkommen. Falls nicht, zählen zwei Teams wie bisher mit Listen. Das Hochregal in "
            "Halle 3 wird am Montag gesperrt, weil dort die Regalprüfung stattfindet. Der Prüfer "
            "braucht etwa vier Stunden. Bitte bis heute Abend alle Paletten aus Gang 7 umlagern. "
            "Die Zählergebnisse müssen bis zum 8. Januar in der Buchhaltung sein. Offen ist noch, "
            "wer die Nachzählung bei Differenzen über 500 Euro macht, das klären wir nach den "
            "Feiertagen."
        ),
        # Keine Namen, kein Folgetermin genannt → beide Angaben müssen fehlen.
        muss=[["29.12.2026"], ["7 Uhr", "07:00", "7:00"], ["12 ", "zwölf"],
              ["21.12.2026"], ["18.12.2026"], ["08.01.2027"], ["500"], ["Gang 7"],
              ["### Offene Aufgaben"]],
        reparatur=[["23.12.2026"]],
        darf_nicht=["[", "```", "Hier ist", "####", "\n* ", "**Teilnehmer", "### Nächster Termin"],
    ),
    # Gegenprobe: erst geschrieben, nachdem die lokalen Prompts feststanden.
    dict(
        id="messe",
        datum="2027-04-14",  # Mittwoch
        gesprochen=(
            "Guten Tag zusammen, kurze Runde zum Messeauftritt. Anwesend sind Frau Schubert, Herr "
            "Nowak und Frau Demir. Die Messe ist vom 8. bis 10. Juni in Hannover. Der Stand hat 24 "
            "Quadratmeter und kostet 7900 Euro, das sind 600 Euro mehr als letztes Jahr. Frau "
            "Schubert, wie weit sind die Prospekte? Der Entwurf ist fertig, die Druckerei braucht "
            "die Daten bis übernächste Woche Freitag, sonst wird es knapp. Gut. Herr Nowak, Sie "
            "geben den Entwurf bitte bis Montag frei. Dann die Hotelzimmer. Frau Demir hat fünf "
            "Zimmer reserviert, die Reservierung muss bis Ende April bestätigt werden. Das mache "
            "ich morgen. Wir haben außerdem beschlossen, dieses Jahr kein Gewinnspiel zu machen, "
            "der Aufwand war letztes Mal zu groß. Standpersonal: Wir brauchen noch zwei Leute für "
            "den Donnerstag, Herr Nowak fragt im Vertrieb nach. Nächstes Treffen in vier Wochen, "
            "wieder Mittwoch um 10 Uhr."
        ),
        muss=[["24"], ["7.900", "7900"], ["600"], ["30.04.2027"], ["19.04.2027"],
              ["15.04.2027"], ["12.05.2027"], ["10 Uhr", "10:00"], ["Schubert"], ["Nowak"],
              ["Demir"], ["Gewinnspiel"], ["### Entscheidungen"], ["### Offene Aufgaben"],
              ["### Nächster Termin"]],
        darf_nicht=["[", "```", "Hier ist", "####", "\n* "],
    ),
]

# Prüfwörter: jede innere Liste ist eine ODER-Gruppe (eine Schreibweise genügt).
PRUEFUNG = {
    "verbessern": {
        "muss": [["Petersen"], ["I-Log"], ["14", "vierzehn"], ["sechs Wochen", "6 Wochen"],
                 ["Freitag"], ["Dezember"], ["Hansen"]],
        "darf_nicht": ["ähm", "Hier ist", "verbesserte Text", "nix"],
    },
    "dampf": {
        "muss": [["Mittwoch"], ["Gutschrift"], ["Server"]],
        "darf_nicht": ["Frechheit", "blöd", "Hier ist", "keinen Cent"],
    },
    "emoji": {
        "muss": [["Juni"], ["16"], ["Hüpfburg"], ["Mai"]],
        "darf_nicht": ["Hier ist"],
    },
    "protokoll": {
        "muss": [["2,8"], ["1.850", "1850"], ["14", "vierzehn"], ["0.14", "0,14"],
                 ["01.12.2026", "1.12.2026", "1. Dezember"],
                 ["09.12.2026", "9.12.2026", "9. Dezember"],
                 ["10.12.2026", "10. Dezember"], ["9 Uhr", "09:00", "9:00"],
                 ["Petersen"], ["Yilmaz"], ["### Entscheidungen"], ["### Offene Aufgaben"]],
        "darf_nicht": ["[Punkt 1]", "[Datum oder –]", "```", "Hier ist"],
    },
    "vokabular": {
        "muss": [["Petersen"], ["I-Log"], ["Kiel"], ["Telekom"], ["Nordlicht Systems"]],
        "darf_nicht": [],
    },
}
