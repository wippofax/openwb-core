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
        print("Aborted: Please run in a private terminal outside a Codex or agent session.")
        return 2
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Aborted: An interactive local terminal is required; no redirection or pipes.")
        return 2
    print("Local MyNISSAN test: This request sends credentials directly to Nissan.")
    print("No wallbox connection. No files are written. The result is confidential.")
    print("Only use outside cloud agents, terminal recording and screen sharing.")
    print("The environment check is a precaution, not a complete technical safeguard.")
    if input("Run a single battery query now? [y/N] ").strip().lower() != "y":
        return 0
    try:
        with warnings.catch_warnings():
            # getpass must abort instead of falling back to an echoed input.
            warnings.simplefilter("error", GetPassWarning)
            user = getpass("MyNISSAN email (hidden): ")
            password = getpass("MyNISSAN password (hidden): ")
            vin = getpass("VIN (hidden; leave blank for a single vehicle): ")
        # This separate process owns logging; never expose dependency debug output.
        logging.disable(logging.CRITICAL)
        status = NissanClient(user, password, vin).fetch_battery()
        measured = datetime.fromtimestamp(status.timestamp, tz=timezone.utc).astimezone()
        print("SoC: {:g} %".format(status.soc))
        print("Measurement time: " + measured.isoformat())
        if status.range_km is not None:
            print("Range: {:g} km".format(status.range_km))
        print("Compare with MyNISSAN. Do not copy values, screenshots or credentials into a cloud chat.")
        return 0
    except GetPassWarning:
        print("Hidden input is unavailable in this terminal. Aborted.")
        return 2
    except NissanError as error:
        print("Query failed: " + str(error))
        return 1
    except (KeyboardInterrupt, EOFError):
        print("Aborted.")
        return 130
    except Exception:
        # Never print an unexpected exception/traceback with potentially private data.
        print("Unexpected local error; no confidential details were displayed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
