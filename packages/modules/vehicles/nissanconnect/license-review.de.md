# Prüfung der Lizenzen und Nutzungsbedingungen

Deutsche Übersetzung des [englischen Originals](license-review.md), auf Wunsch
des Projektverantwortlichen als zusätzliche Datei erstellt. Die Prüfstände,
Quellen und offenen Punkte des Originals werden unverändert wiedergegeben;
die Übersetzung ist keine erneute rechtliche Prüfung.

Geprüft am **02.10.2026** für die europäische MyNISSAN-Integration anhand der
deutschen Nutzungsbedingungen. Quelltextgrundlage: Core-Beitrag `72c4786`,
Einstellungsoberfläche `776a60d`, Zielversion des Core
`3ced7f9cef3c70980ee1fab670f0d0717d1809ca` und Zielversion der Einstellungsoberfläche
`e8de268fa25f7efca2b5ffc005a757a2f36b530f`.

**Ergebnis:** Für den geprüften, angepassten Quelltext besteht ein mit GPLv3
vereinbarer Lizenzierungsweg. Der vorhandene MIT-Lizenztext ist korrekt; Herkunft
und Änderungshinweis sind jetzt ausdrücklich in [NOTICE.md](NOTICE.md)
dokumentiert. Dieses Ergebnis belegt keine Erlaubnis für den inoffiziellen
Zugriff auf den Dienst. Die endgültige Zusammenstellung des Veröffentlichungspakets
und die unten beschriebene Frage des Dienstzugangs bleiben offen. Dies ist eine
dokumentierte Quellenprüfung, keine rechtliche Zertifizierung oder Freigabe zur
Veröffentlichung.

## Herkunft des Quelltexts

| Quelle | Nachweis mit festgelegtem Versionsstand | Verwendung und lizenzrechtliche Bewertung |
| --- | --- | --- |
| openWB Core und Einstellungsoberfläche | Jeweilige `LICENSE` des Repositorys, GNU GPL Version 3; Versionsstände wie oben | Die native Integration und der Beitrag zur Oberfläche folgen GPLv3; bestehende Hinweise bleiben erhalten. Keine neue Laufzeit- oder UI-Abhängigkeit. |
| HomeAssistant-NissanConnect | [MIT-Lizenz](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/LICENSE.md), [Client](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/custom_components/nissan_connect/kamereon/kamereon.py), [Konstanten](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/custom_components/nissan_connect/kamereon/kamereon_const.py) | Direkte Referenz für den Parser des HTML-Anmeldeformulars, OneID/PKCE, Austausch und Erneuerung von Tokens, EU-Endpunkte und Batteriedatenfelder. Unser Transport über die Python-Standardbibliothek, die Validierung, die Fehlerbehandlung und der openWB-Adapter unterscheiden sich davon. Daniel Rapers MIT-Hinweis von 2024 bleibt wortgetreu erhalten. |
| mitchellrj/kamereon-python | [Apache-2.0-Lizenz](https://github.com/mitchellrj/kamereon-python/blob/146904802301aa0b0008e2bdb3a88ed10ff50acf/LICENSE.md), [Dateikopf des Clients](https://github.com/mitchellrj/kamereon-python/blob/146904802301aa0b0008e2bdb3a88ed10ff50acf/kamereon/kamereon.py) nennt Richard Mitchell, 2020 | Indirekte Referenzkette. Entscheidend ist die Aussage im Dateikopf des unmittelbar verwendeten HA-Clients, dass Apache-Anteile mit Erlaubnis neu lizenziert wurden. Wir stützen uns auf diese veröffentlichte MIT-Lizenzgewährung und nehmen nicht an, dass die Apache-Urheberhinweise einfach entfallen wären. Bei dieser Prüfung wurde kein separater Apache-Quelltext in den Beitrag übernommen. |
| Tobiaswk/dartnissanconnect | [MIT-Lizenz](https://github.com/Tobiaswk/dartnissanconnect/blob/5e34e8c573d34dc4d3d48e63052f015f99080d2d/LICENSE), Tobias Westergaard Kjeldsen, 2021 | Recherchequelle und Herkunftshinweis. Es werden weder ein Dart-Paket noch Anwendungsressourcen ausgeliefert. Die Namensnennung bleibt erhalten; die Lizenz dieser Bibliothek darf nicht mit der Lizenz einer anderen Anwendung verwechselt werden. |

Die Aussage zur Neulizenzierung im HA-Projekt ist ein Nachweis aus dem
Ursprungsprojekt; der private Schriftverkehr zur Erlaubnis wurde nicht eingesehen.
Dies ist das übliche Vertrauen auf die angegebene Quelltextlizenz und keine
unabhängige Überprüfung sämtlicher Rechte aller Urheber.
Sollte künftig Apache-lizenzierter Quelltext unmittelbar übernommen werden,
müssen dessen Urheber- und Herkunftshinweise sowie eine gegebenenfalls vorhandene
NOTICE erhalten bleiben. Apache-2.0 ist beizulegen; geänderte Dateien sind gemäß
[Abschnitt 4](https://www.apache.org/licenses/LICENSE-2.0) zu kennzeichnen.
Nach Angaben der
[Apache Software Foundation](https://apache.org/licenses/GPL-compatibility.html)
ist Apache-2.0 mit GPLv3 vereinbar. Die Vereinbarkeit von MIT/Expat dokumentiert die
[Free Software Foundation](https://www.gnu.org/licenses/license-list.html#Expat).

## Pflichten bei der Weitergabe und Abhängigkeiten

Für die vorgesehenen Quelltextbeiträge sind die GPL-Texte beider Repositorys,
die NOTICE des Moduls und bestehende Hinweise zu Drittanbietern zu erhalten.
Der datierte Anpassungshinweis benennt die Änderungen für openWB; der gesamte
Beitrag darf nicht als MIT-lizenziert dargestellt werden.
Die Abschnitte 4 bis 6 der GPLv3 behandeln Hinweise, geänderten Quelltext und den
zugehörigen Quelltext bei der Weitergabe in anderer Form als Quelltext. Bei einer
Veröffentlichung der kompilierten Oberfläche müssen der passende Quelltext in
der bevorzugten Bearbeitungsform, die Lockdatei und die erforderlichen
Build-Unterlagen über einen lizenzkonformen Weg bereitgestellt werden.
Eine rein lokale private Nutzung erfordert für sich genommen keine öffentliche
Bereitstellung. Maßgeblicher Lizenztext ist die `LICENSE` des Repositorys;
der [GPLv3-Leitfaden](https://www.gnu.org/licenses/quick-guide-gplv3.en.html)
liefert ergänzende Erläuterungen.

**BP-LIC-01 erledigt (Korrektur):** Im früheren Bericht wurde die kleingeschriebene
`readme.md` von `urlsafe-base64` 1.0.0 übersehen. Sie enthält den MIT-Hinweis mit
Copyright 2014 RGBboy. Die
[README im festgelegten Quelltextstand](https://github.com/RGBboy/urlsafe-base64/blob/4438da5b18040af1c1789dd3c53b6595b3bea512/readme.md)
und das konkrete
[npm-Archiv](https://registry.npmjs.org/urlsafe-base64/-/urlsafe-base64-1.0.0.tgz)
bestätigen dies. Der SHA-512-Wert des Archivs stimmt mit beiden UI-Lockdateien
überein; README, package.json und die beiden JavaScript-Dateien stimmen Byte für
Byte mit den installierten Kopien überein. Ein Austausch oder Update der
Abhängigkeit war nicht erforderlich. Fehlende Metadaten in der Lockdatei bedeuten
keine fehlende Lizenz. Auch die anderen zuvor festgestellten Metadatenlücken
betreffen Pakete mit vorhandenen MIT-Hinweisen; siehe
[Bestandsaufnahme](contribution-review.md).

**BP-LIC-02 offen, ausschließlich Zusammenstellung des Veröffentlichungspakets:**
Die 699 Einträge der Ziel-Lockdatei beziehungsweise 662 Einträge der
Entwicklungs-Lockdatei umfassen auch reine Build-Abhängigkeiten und optionale
Pakete; sie sind keine Stückliste der tatsächlich ausgelieferten Software (SBOM).
Das eingefrorene Overlay-Archiv enthält 367 Einträge. Unter den Dateien mit
lizenzbezogenen Namen befindet sich nur die NOTICE des Moduls. Daraus folgt
nicht, dass eingebettete Hinweise fehlen; außerdem setzt das Overlay eine
bestehende Installation mit GPL-Text voraus. Es ist jedoch kein Nachweis für
ein vollständig zur Weitergabe geeignetes Lizenzpaket. Vor der Veröffentlichung
einer endgültigen kompilierten Oberfläche müssen die enthaltenen JavaScript-,
CSS-, Schrift- und Symbolressourcen ihren tatsächlichen Paketversionen zugeordnet,
die erforderlichen MIT-/BSD-/Apache-Hinweise und sonstigen Namensnennungen erhalten
sowie die Anforderungen an den zugehörigen GPL-Quelltext geprüft werden.
Dies soll einmal anhand des endgültigen Builds geschehen; allein für diese
Prüfung sollen weder gemeinsame Abhängigkeiten geändert noch der eingefrorene
Wallbox-Teststand neu gebaut werden.

## Zugang zu Nissan-Diensten: BP-TERMS-01 offen

Das [offizielle deutsche AGB-Verzeichnis](https://www.nissan.de/rechtliches/agb.html)
verlinkt die
[Nutzungsbedingungen für NissanConnect Services, Mai 2026](https://www.nissan.de/content/dam/Nissan/nissan_europe/services/Ownership/NissanConnectServices_FULL/PDF/TermsOfUse/NissanConnect%20Services%20Terms%20and%20Conditions%20-%20Germany.pdf).
Diese öffentliche Fassung umfasst ausdrücklich MyNISSAN. Relevante Regelungen:

- Abschnitt 1.2, Seite 4: Anwendungen, die Nissan oder Dritte in dessen Auftrag bereitstellen.
- Abschnitte 6.1 und 7.3–7.4, Seiten 23, 25–26: Beschränkungen zu Technik und Inhalten,
  Reverse Engineering und zulässige Dienstnutzung; Abschnitt 7.2 behandelt Zugangsdaten.
- Abschnitte 5.2 und 5.7, Seiten 19 und 21: Datenzugang, Datenweitergabe und rechtmäßige
  Weiterverwendung durch Nutzer, jeweils unter Einschränkungen. Diese sind zusammen
  mit den weiter gefassten Regelungen zu Inhalten zu lesen.
- Abschnitt 2.6, Seite 7: Aussetzung und Beendigung von Diensten, unter anderem bei Verstößen.

Unsere Einschätzung: Diese Regelungen belegen weder eine konkrete Erlaubnis für
den vorliegenden Client noch rechtfertigen sie die Aussage, jede lokale Nutzung
sei rechtswidrig. Das Modul verwendet eine öffentliche Client-Kennung der
offiziellen App, fragt das Konto des Fahrzeughalters regelmäßig ab und speichert
beziehungsweise zeigt Werte für die Laderegelung an. Eine urheberrechtliche
Erlaubnis eines unabhängigen Bibliotheksautors klärt dieses Dienstverhältnis nicht.
Die vom Nutzer akzeptierte Fassung der Konto-/App-Bedingungen und mögliche
zusätzliche OneID-/Kamereon-Bedingungen wurden nicht eingesehen. Eine separate
öffentliche Entwicklerfreigabe für die konkreten Anmelde-/BFF-Endpunkte oder ein
zahlenmäßig festgelegtes zulässiges Abfrageintervall konnte nicht festgestellt
werden. Wartezeiten nach Fehlern (Backoff) und Abfragesperren sind technische Schutzmaßnahmen, keine
vertragliche Erlaubnis.

Auch das deutsche Urheberrecht begrenzt pauschale Schlussfolgerungen:
Schnittstellenideen behandelt
[§ 69a Absatz 2 UrhG](https://www.gesetze-im-internet.de/urhg/__69a.html),
rechtmäßiges Beobachten und Testen
[§ 69d Absatz 3](https://www.gesetze-im-internet.de/urhg/__69d.html),
und zur Herstellung der Interoperabilität notwendige Dekompilierung
[§ 69e](https://www.gesetze-im-internet.de/urhg/__69e.html).
[§ 69g Absatz 2](https://www.gesetze-im-internet.de/urhg/__69g.html)
erklärt bestimmte entgegenstehende vertragliche Regelungen für nichtig.
Diese an Voraussetzungen gebundenen Regeln sind keine pauschale Erlaubnis für
den Zugriff auf einen gehosteten Dienst oder das Umgehen von Zugangskontrollen.
Ihre Anwendung auf diese Implementierung erfordert eine Einzelfallbewertung.

## Offizielle Alternative, deren Prüfung sinnvoll ist

Nissans [deutsche Seite zu vernetzten Fahrzeugdaten](https://www.nissan.de/vernetzte-fahrzeugdaten.html)
nennt für diesen Datenzugang den LEAF ab Produktion Mai 2019. Ob ein konkretes
Fahrzeug des Baujahrs 2019 teilnahmeberechtigt ist, wurde nicht überprüft.
Die [deutschen FAQ](https://www.nissan.de/kundenservice/faq.html) verlinken die
öffentliche
[MyNISSANdata-Entwicklerdokumentation](https://mynissandata.com/developer-documentation).
Sie beschreibt registrierte geschäftliche Integrationen, die Einwilligung des
Fahrzeughalters, separate Zugangsdaten, Zahlung und Abrechnung sowie die rein
lesende Datenbereitstellung durch Abruf oder Webhooks. Die Referenz zu Ladedaten
enthält Ladestand und Aktualisierungszeitpunkt. Dies ist eine andere API als die
derzeit verwendeten Endpunkte der MyNISSAN-App. Die Dokumentation belegt nicht,
dass unser Fahrzeug, der private Einsatzzweck oder die Anforderungen an Kosten
und Datenaktualität die Voraussetzungen erfüllen.

Die öffentliche
[Seite mit den Plattformbedingungen](https://mynissandata.com/terms-of-service)
lieferte bei dieser Prüfung Navigation, aber keine inhaltlichen Bedingungen.
Die Plattformbedingungen und die „Data Terms“ sind deshalb weiterhin ungeprüft.
Es wurden weder ein Konto eingerichtet noch eine Einwilligungsanfrage, eine
kostenpflichtige Aktion oder eine Live-API-Abfrage durchgeführt. Eine Umstellung
auf diese API ist nicht Bestandteil dieser Lizenzprüfung.

## Konkret noch zu treffende Entscheidung

Bevor der Punkt Nutzungsbedingungen abgeschlossen wird, ist eine dokumentierte
Bewertung anhand der anwendbaren Bedingungen und einer qualifizierten Auslegung
oder einer Klärung durch den Anbieter erforderlich. Die folgende Anfrage ist
vorbereitet, wurde aber **nicht versandt**:

> Erlaubt Nissan einem Fahrzeughalter, eine quelloffene, lokal betriebene
> openWB-Integration für regelmäßige, rein lesende Batterieabfragen über die
> OneID-/Kamereon-Endpunkte und die öffentliche Client-Kennung der MyNISSAN-EU-App
> zu verwenden, wobei die Daten lokal für die Laderegelung gespeichert und
> angezeigt werden? Welche Zugangsbedingungen und Abfragegrenzen gelten?
> Falls dieser Zugangsweg nicht unterstützt wird: Kann eine unabhängig
> registrierte MyNISSANdata-Integration diesen privaten Einsatzzweck erfüllen,
> und welche Bedingungen gelten dabei hinsichtlich Teilnahmeberechtigung,
> Datenaktualität, Weitergabe und Gebühren?

Für die Anfrage werden weder Passwort noch VIN, private API-Antworten oder
Screenshots des Kontos benötigt. Vor dem Versand ist eine gesonderte Genehmigung
erforderlich. Die abschließende Datenschutz- und Sicherheitsprüfung wird separat
in [privacy.md](privacy.md) und im Bulletproof-Projektdatensatz verfolgt;
diese Lizenzprüfung schließt die dortigen Befunde nicht ab.

## Reproduzierbare öffentliche Nachweise

Zusätzlich zu den oben genannten unveränderlich versionierten URLs wurden die
folgenden SHA-256-Prüfsummen der heruntergeladenen Dateien festgehalten:

| Artefakt | SHA-256 |
| --- | --- |
| HA LICENSE.md | `b7dc3fcde759bb78fd2e22b8725c6d384ced62a612c1c73b579f5a82cbdb05e2` |
| HA-Client | `f6360df94a70a6f51d49fbc5ba37ba3f5c89f9af7865360cb5022acf1573d743` |
| kamereon-python LICENSE.md | `43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1` |
| LICENSE der Dart-Bibliothek | `e7b839ced10822fbc7f0eb1655f0a8070c4b1b541769c600e3567c0d2e136d17` |
| npm-Archiv von urlsafe-base64 | `c0a12871ac0a9dc23d79a701be42da557b8a31ad3e45820628576f9e5f7be0f4` |

Die Downloads öffentlicher Quellen und Lizenztexte dienten ausschließlich als
Prüfunterlagen; es wurde kein Paket installiert. Nissan-Seiten sind veränderlich
und müssen für die abschließende Entscheidung zum Dienstzugang erneut geprüft werden.

## Herkunft des Kilometerstand-Felds (02.10.2026)

Derselbe MIT-lizenzierte HA-Versionsstand liefert die zusätzliche Feldzuordnung:
[OdometerSensor](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/custom_components/nissan_connect/sensor.py)
verwendet `total_mileage` mit der Einheit Kilometer; der bereits geprüfte Client
ordnet dieses Attribut dem Cockpit-Feld `totalMileage` zu. Der neue Parser,
Transport und die Fehlerbehandlung wurden lokal implementiert; der bestehende
MIT-Hinweis gilt weiterhin. Es kommen weder ein neues Paket noch eine neue Lizenz
hinzu. Die tatsächliche Verfügbarkeit beim LEAF und der Dienstzugang bleiben
separate Fragen der Abnahme beziehungsweise der Nutzungsbedingungen.

## Aktualisierter Nachweis der Lizenzhinweise im Build (02.10.2026)

Die [Offline-Prüfung vor der Veröffentlichung](release-review.md) dokumentiert
einen neu gebauten Teststand mit Kilometerstand-Abfrage und Oberfläche. Er enthält
die vollständigen Lizenzhinweise für alle 126 npm-Paketverzeichnisse, die im
Vite-Ausgabe-/CSS-Abhängigkeitsgraphen gefunden wurden. Außerdem ist ein passendes
Quelltextarchiv vorbereitet. BP-LIC-02 bleibt für unabhängig vorgefertigte ältere
Bibliotheksbündel und die endgültige Zusammenstellung zur Veröffentlichung
teilweise offen. Aus dieser Paketprüfung folgt weder eine Erlaubnis zum
Dienstzugang noch eine rechtliche Freigabe. Der eingefrorene installierte
Teststand bleibt unverändert.
