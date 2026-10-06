import contextlib
import json
import sys
from pathlib import Path
from typing import Any


_analyze_message = None


def _load_analyzer():
    global _analyze_message
    if _analyze_message is None:
        ai_directory = str(Path.cwd())
        if ai_directory not in sys.path:
            sys.path.insert(0, ai_directory)
        with contextlib.redirect_stdout(sys.stderr):
            from ai_engine import analyze_message

        _analyze_message = analyze_message
    return _analyze_message


def _write_response(response: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict) or not isinstance(request.get("text"), str):
                raise ValueError("Request must be a JSON object with a string 'text' field")
            with contextlib.redirect_stdout(sys.stderr):
                result = _load_analyzer()(request["text"])
            if not isinstance(result, dict):
                raise TypeError("AI analysis returned a non-object result")
            _write_response({"result": result})
        except Exception as error:
            _write_response(
                {
                    "error": {
                        "code": "AI_ANALYSIS_FAILED",
                        "message": f"{type(error).__name__}: {error}",
                    }
                }
            )


if __name__ == "__main__":
    main()