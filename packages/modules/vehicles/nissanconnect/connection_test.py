"""One passive settings test. Credentials arrive on stdin, never in argv or files."""
import json
import logging
import os
import re
import sys

if __package__:
    from .api import AuthenticationError, NissanClient, NissanError, RateLimitError
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from api import AuthenticationError, NissanClient, NissanError, RateLimitError


def run_test(payload, client_factory=NissanClient):
    if not isinstance(payload, dict) or set(payload) - {"user_id", "password", "vin"}:
        return {"success": False, "code": "invalid_input"}
    user = payload.get("user_id")
    password = payload.get("password")
    vin = payload.get("vin")
    if vin == "":
        vin = None
    if (not isinstance(user, str) or not user.strip() or len(user) > 320
            or not isinstance(password, str) or not password or len(password) > 4096
            or (vin is not None and (not isinstance(vin, str)
                                     or not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin.strip().upper())))):
        return {"success": False, "code": "invalid_input"}
    client = None
    try:
        client = client_factory(user.strip(), password, vin.strip().upper() if vin else None)
        client.fetch_battery()
        return {"success": True, "code": "success", "query": client.last_query}
    except AuthenticationError:
        code = "authentication_failed"
    except RateLimitError:
        code = "rate_limited"
    except NissanError:
        code = "query_failed"
    except Exception:
        # Neither exception messages nor tracebacks belong in the web response.
        return {"success": False, "code": "internal_error"}
    return {"success": False, "code": code, "query": client.last_query if client else None}


def main():
    logging.disable(logging.CRITICAL)
    if any(os.environ.get(name) for name in ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_CI")):
        result = {"success": False, "code": "agent_environment"}
    else:
        try:
            body = sys.stdin.read(8193)
            result = run_test(json.loads(body)) if len(body) <= 8192 else {
                "success": False, "code": "invalid_input"}
        except Exception:
            result = {"success": False, "code": "invalid_input"}
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
