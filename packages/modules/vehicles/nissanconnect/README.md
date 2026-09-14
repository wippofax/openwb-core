# Nissan Leaf ZE1 / MyNISSAN EU (experimental)

Dieses Modul liest die bei Nissan gespeicherten Batteriedaten über MyNISSAN
OneID und Kamereon. Es liefert SoC, Reichweite (falls vorhanden) und den
tatsächlichen Messzeitpunkt an openWB. Anzeige, Abfrageintervalle,
Fehlerbehandlung und Ladegrenzen übernimmt die vorhandene openWB-Regelung.

## Voraussetzungen und Grenzen

- Europäisches MyNISSAN-Konto mit funktionierender Anmeldung und zugeordnetem
  Leaf ZE1. Die App-/Dienstzuordnung ist entscheidend, nicht allein das Baujahr.
- NissanConnect EV und das vorhandene Modul `leaf` verwenden eine andere API.
  Dieses Modul verändert das bisherige Leaf-Modul nicht.
- Inoffizielle, aus öffentlichen Implementierungen abgeleitete Schnittstelle.
  Nissan kann Anmeldung oder Datenformate ändern. Zusätzliche Anmeldeschritte,
  Einwilligungen oder MFA werden nicht automatisiert; gegebenenfalls in der
  offiziellen App erledigen.
- **Noch kein erfolgreicher Test mit einem echten Nissan-Konto oder einer
  Wallbox.** Ein erfolgreicher synthetischer Login-Test belegt keine aktuelle
  Herstellerkompatibilität.
- Es wird ausschließlich der Serverbestand gelesen. Kein Aufwecken, kein
  `refresh-battery-status`, kein Starten oder Stoppen des Fahrzeugladens.
  Bei alten Herstellerdaten kann auch der gelieferte SoC alt sein. Der originale
  Zeitstempel bleibt erhalten; openWB kann seine vorhandene Berechnung verwenden.
- Fehlender/ungültiger SoC oder ein fehlender, zeitzonenloser beziehungsweise
  mehr als fünf Minuten zukünftiger Messzeitpunkt erzeugen einen Fehler.
  Fehlende optionale Reichweite verhindert keinen gültigen SoC.

## Konfiguration

Das Modul hat den Typ `nissanconnect`. Die passende Einstellungsseite liegt im
Repository `openWB/openwb-ui-settings` unter
`src/components/vehicles/nissanconnect/vehicle.vue`.

| Feld | Bedeutung |
| --- | --- |
| `user_id` | E-Mail-Adresse des MyNISSAN-Kontos |
| `password` | Passwort des MyNISSAN-Kontos |
| `vin` | Optionale FIN; bei mehreren Fahrzeugen im Konto erforderlich |

Die Region ist auf Europa festgelegt. Ein einziges Fahrzeug wird automatisch
gewählt; eine mehrdeutige Auswahl oder eine unbekannte FIN erzeugt einen Fehler.

## Datenfluss und Geheimnisse

Das Modul kommuniziert bei einer späteren Ausführung direkt mit den festgelegten
Nissan-/Kamereon-HTTPS-Endpunkten. Ein Modellanbieter ist am Clientbetrieb nicht
beteiligt. Dieser Quellcode erzeugt keine Telemetrie und speichert keine
API-Antworten, Cookies oder Tokens auf Datenträgern. Tokens werden im
Clientobjekt wiederverwendet; nach Neustart oder Konfigurationsänderung erfolgt
eine neue Anmeldung.

Die allgemeinen openWB-Einstellungen und Sicherungen können konfigurierte
Zugangsdaten enthalten. Passwortmaskierung im Browser schützt diese Speicherung
nicht. Solche Konfigurationen, Sicherungen, FINs und echte API-Antworten dürfen
nicht in Git, Issues, Chatnachrichten oder Modell-Werkzeugausgaben gelangen.
`.gitignore` allein verhindert keinen Transfer an ein Cloud-Modell.

Der Transport verwendet deshalb die Python-Standardbibliothek mit
Zertifikatsprüfung, begrenzter Antwortgröße und expliziter Kontrolle von
Weiterleitungen. Der übliche `modules.common.req.get_http_session()`-Hook wird
hier bewusst nicht verwendet, weil er vollständige Antworten protokolliert.
Die Standardbibliothek vermeidet außerdem urllib3-Debug-URLs mit FIN oder
Autorisierungscode. Ausnahmen enthalten nur feste, unpersönliche Meldungen;
Originalantworten und ursprüngliche Transportausnahmen werden nicht ausgegeben.

Eine Anfrage wartet höchstens zehn Sekunden auf Socket-Operationen. Nach einem
Budget von 60 Sekunden werden keine weiteren Requests gestartet. Das ist kein
harter Gesamtzeitabbruch eines bereits laufenden Socket-Reads. Weiterleitungen
und die Wiederholung nach abgelehnter Authentifizierung sind begrenzt. HTTP 429
führt zu einer Pause von mindestens fünf Minuten; fehlgeschlagene Anmeldung
ebenso. Es gibt keine unbeschränkten Wiederholungsschleifen oder Warte-Sleeps.

## Offline prüfen

Nur synthetische Fixtures verwenden. Die Tests sperren Socket-Verbindungen,
Namensauflösung und das Starten einer echten Fahrzeugabfrage über den
ersetzten Transport. Der Adaptertest ersetzt den Dienst-Wrapper; er prüft die
Übergabe an den echten `CarState`, keine laufende Ladeanlage.

Vom Core-Repositoryroot mit einer Python-3.9-Testumgebung:

```sh
PYTHONPATH=packages python -m pytest -q packages/modules/vehicles/nissanconnect \
  --confcutdir=packages/modules/vehicles/nissanconnect
python -m flake8 packages/modules/vehicles/nissanconnect
```

Für die UI im separaten Repository:

```sh
npm ci --ignore-scripts
npx eslint src/components/vehicles/nissanconnect
npx vitest run src/components/vehicles/nissanconnect/vehicle.spec.js
npm run build
```

Der normale Build erzeugt lokale UI-Dateien. Die Skripte `build-dev` und
`build-prod` schreiben dagegen in einen openWB-Installationspfad und gehören
nicht zum hier beschriebenen Offline-Test.

## Späterer Test an einer eigenen Wallbox

1. Zunächst einen abgeschirmten Test auf einem separaten Rechner vorbereiten.
   Zugangsdaten lokal verdeckt eingeben, außerhalb eines Cloud-Agenten ausführen
   und Ergebnisse lokal mit der App vergleichen. Keine echten Werte in den
   Agenten-Kontext übernehmen. Ein solcher Live-Test ist hier noch nicht erfolgt.
2. Für die Installation zuerst einen konkreten Plan für Softwarestand,
   Sicherung, betroffene Dateien, Testfenster und Wiederherstellung erstellen.
3. **Vor jeder Wallbox-Änderung ausdrücklich mit Warnung vor Auswirkungen und
   Risiken nachfragen und eine ausdrückliche Genehmigung abwarten.** Das betrifft
   auch Sicherungsdateien auf dem Gerät, Dateiübertragung, Neustarts,
   Konfiguration sowie MQTT-SoC- oder Steuerwerte von einem anderen Rechner.
4. Nach genehmigter Installation zuerst SoC und Messzeitpunkt vergleichen,
   danach die vorhandene Laderegelung mit separat genehmigten Einstellungen
   beobachten. Ein Rollback ist ebenfalls eine Geräteänderung und muss im
   genehmigten Plan enthalten sein.

Für Schritt 1 enthält das Modul `probe.py`, das ausschließlich manuell in einem
privaten lokalen Terminal außerhalb von Codex/Cloud-Agenten gestartet wird:

```sh
python packages/modules/vehicles/nissanconnect/probe.py
```

Der Starter fordert eine Bestätigung vor dem Abruf, liest E-Mail, Passwort und
optionale FIN verdeckt und zeigt SoC/Messzeitpunkt nur im Terminal. Er verweigert
Pipes, Ausgabeumleitung und einige erkennbare Agentenumgebungen. Das ist keine
vollständige technische DLP-Grenze: Terminalaufzeichnung, Bildschirmfreigabe,
andere Agenten und Betriebssystemüberwachung lassen sich damit nicht ausschließen.
Kein Live-Test darf über Modell-Werkzeuge gestartet werden. Die reinen
Offline-Tests von `probe.py` verwenden einen ersetzten Client.

Kein Installations-, SSH-, MQTT- oder Neustartskript ist Bestandteil des Moduls.

## Zum Projekt beitragen

Core-Änderungen als eigenen Beitrag gegen `openWB/core:master` vorbereiten;
die Einstellungsseite als separaten Beitrag gegen
`openWB/openwb-ui-settings:main`. Die beiden Beiträge gegenseitig referenzieren,
Testgrenzen und API-Referenz nennen und keine gebauten UI-Dateien in den Core-PR
aufnehmen. Veröffentlichung und Remote-Merge benötigen eine eigene Beauftragung.

Referenzen:

- [openWB: neues Modul](https://github.com/openWB/core/blob/master/docs/Neues%20Modul%20programmieren.md)
- [openWB: Einstellungsseite](https://github.com/openWB/core/blob/master/docs/Einstellungs-Seite%20erstellen.md)
- [NissanConnect-Referenz, festgehaltener Stand](https://github.com/dan-r/HomeAssistant-NissanConnect/tree/b0bafe9108d4574e243aa182324584dbc68369ad)
- [OneID-Umstellung](https://github.com/dan-r/HomeAssistant-NissanConnect/pull/119)

Lizenzhinweise zur verwendeten Referenz stehen in `NOTICE.md`.
