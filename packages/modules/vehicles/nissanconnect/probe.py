"""Run manually in a private local terminal, never through a cloud agent tool.

No credentials as command-line arguments, no files, no wallbox access.
The output is private and must not be copied into an issue or cloud chat.
"""
from datetime import datetime, timezone
from getpass import getpass, GetPassWarning
import logging
import os
import sys
import warnings

if __package__:
    from .api import NissanClient, NissanError
else:
    from api import NissanClient, NissanError


def main():
    if any(os.environ.get(name) for name in ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_CI")):
        print("Abbruch: Bitte außerhalb einer Codex-/Agenten-Sitzung in einem privaten Terminal starten.")
        return 2
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Abbruch: Ein interaktives lokales Terminal ist erforderlich; keine Umleitung oder Pipe.")
        return 2
    print("Lokaler MyNISSAN-Test: Dieser Aufruf sendet Anmeldedaten direkt an Nissan.")
    print("Keine Wallbox-Verbindung. Keine Dateiablage. Das Ergebnis bleibt vertraulich.")
    print("Nur außerhalb von Cloud-Agenten, Terminalaufzeichnung und Bildschirmfreigabe verwenden.")
    print("Die Umgebungsprüfung ist eine Vorsichtsmaßnahme, keine technisch vollständige Abschirmung.")
    if input("Jetzt eine einzelne Batterieabfrage ausführen? [j/N] ").strip().lower() != "j":
        return 0
    try:
        with warnings.catch_warnings():
            # getpass must abort instead of falling back to an echoed input.
            warnings.simplefilter("error", GetPassWarning)
            user = getpass("MyNISSAN-E-Mail (verdeckt): ")
            password = getpass("MyNISSAN-Passwort (verdeckt): ")
            vin = getpass("FIN (verdeckt; bei einem Fahrzeug leer lassen): ")
        # This separate process owns logging; never expose dependency debug output.
        logging.disable(logging.CRITICAL)
        status = NissanClient(user, password, vin).fetch_battery()
        measured = datetime.fromtimestamp(status.timestamp, tz=timezone.utc).astimezone()
        print("SoC: {:g} %".format(status.soc))
        print("Messzeitpunkt: " + measured.isoformat())
        if status.range_km is not None:
            print("Reichweite: {:g} km".format(status.range_km))
        print("Mit MyNISSAN vergleichen. Keine Werte, Screenshots oder Zugangsdaten in den Cloud-Chat kopieren.")
        return 0
    except GetPassWarning:
        print("Verdeckte Eingabe ist in diesem Terminal nicht möglich. Abgebrochen.")
        return 2
    except NissanError as error:
        print("Abfrage fehlgeschlagen: " + str(error))
        return 1
    except (KeyboardInterrupt, EOFError):
        print("Abgebrochen.")
        return 130
    except Exception:
        # Never print an unexpected exception/traceback with potentially private data.
        print("Unerwarteter lokaler Fehler; keine vertraulichen Details ausgegeben.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
