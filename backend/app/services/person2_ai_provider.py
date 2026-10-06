import atexit
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from app.schemas import FraudAnalysis
from app.services.ai_service_interface import FraudAnalysisService


class Person2AIServiceError(RuntimeError):
    """Raised when Person 2's AI worker cannot return usable analysis."""


_SCAM_TYPE_MAP = {
    "kyc scam": "KYC_SCAM",
    "bank impersonation": "BANK_IMPERSONATION",
    "upi scam": "UPI_SCAM",
    "investment scam": "INVESTMENT_SCAM",
    "job scam": "JOB_SCAM",
    "delivery scam": "DELIVERY_SCAM",
    "tech support scam": "TECH_SUPPORT_SCAM",
    "ai impersonation": "AI_IMPERSONATION",
    "lottery scam": "OTHER",
    "general scam": "OTHER",
}
_ENTITY_TYPE_MAP = {
    "urls": "URL",
    "upis": "UPI",
    "phones": "PHONE",
    "emails": "EMAIL",
}


def normalize_person2_result(result: Any) -> FraudAnalysis:
    if not isinstance(result, dict):
        raise Person2AIServiceError("AI worker returned malformed analysis data")

    try:
        raw_score = result["risk_score"]
        raw_level = result["risk_level"]
        raw_label = result["scam_type"]
        raw_entities = result["entities"]
        raw_reasons = result["reasons"]
    except KeyError as error:
        raise Person2AIServiceError(
            f"AI worker result is missing required field: {error.args[0]}"
        ) from error

    if isinstance(raw_score, bool) or not isinstance(raw_score, int):
        raise Person2AIServiceError("AI worker risk_score must be an integer")
    if not isinstance(raw_level, str):
        raise Person2AIServiceError("AI worker risk_level must be a string")
    if not isinstance(raw_label, str):
        raise Person2AIServiceError("AI worker scam_type must be a string")
    if not isinstance(raw_entities, dict):
        raise Person2AIServiceError("AI worker entities must be an object")
    if not isinstance(raw_reasons, list) or any(
        not isinstance(reason, str) for reason in raw_reasons
    ):
        raise Person2AIServiceError("AI worker reasons must be a list of strings")

    entities: list[dict[str, str]] = []
    indicators = list(raw_reasons)
    for category, entity_type in _ENTITY_TYPE_MAP.items():
        values = raw_entities.get(category, [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise Person2AIServiceError(
                f"AI worker entity category '{category}' must be a list of strings"
            )
        entities.extend({"type": entity_type, "value": value} for value in values)

    amounts = raw_entities.get("amounts", [])
    if not isinstance(amounts, list) or any(
        not isinstance(value, str) for value in amounts
    ):
        raise Person2AIServiceError(
            "AI worker entity category 'amounts' must be a list of strings"
        )
    indicators.extend(f"Mentions financial amount: {amount}" for amount in amounts)

    score = max(0, min(100, raw_score))
    # Adapter-derived score band, not a calibrated model probability.
    confidence = (
        0.60
        if score < 40
        else 0.75
        if score < 70
        else 0.90
        if score < 90
        else 0.95
    )
    scam_type = _SCAM_TYPE_MAP.get(raw_label.strip().casefold(), "OTHER")
    try:
        return FraudAnalysis(
            risk_score=raw_score,
            risk_level=raw_level,
            scam_type=scam_type,
            confidence=confidence,
            entities=entities,
            indicators=indicators,
        )
    except (TypeError, ValueError) as error:
        raise Person2AIServiceError(
            f"AI worker returned invalid analysis data: {error}"
        ) from error


class Person2AIProvider(FraudAnalysisService):
    def __init__(self, ai_directory: Path | None = None) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        self._ai_directory = (ai_directory or repository_root / "ai").resolve()
        self._worker_script = Path(__file__).with_name("person2_ai_worker.py").resolve()
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        atexit.register(self.close)

    def analyze_scam(self, text: str) -> FraudAnalysis:
        with self._lock:
            process = self._get_worker()
            if process.stdin is None or process.stdout is None:
                raise Person2AIServiceError("AI worker pipes are unavailable")
            try:
                process.stdin.write(json.dumps({"text": text}) + "\n")
                process.stdin.flush()
                response_line = process.stdout.readline()
            except (BrokenPipeError, OSError) as error:
                self._discard_worker()
                raise Person2AIServiceError(
                    f"AI worker communication failed: {error}"
                ) from error

            if not response_line:
                return_code = process.poll()
                self._discard_worker()
                raise Person2AIServiceError(
                    f"AI worker exited without a response (exit code: {return_code})"
                )

            try:
                response = json.loads(response_line)
            except json.JSONDecodeError as error:
                self._discard_worker()
                raise Person2AIServiceError("AI worker returned malformed JSON") from error

            if not isinstance(response, dict):
                raise Person2AIServiceError("AI worker returned malformed JSON data")
            if "error" in response:
                error = response["error"]
                if not isinstance(error, dict):
                    raise Person2AIServiceError("AI worker returned a malformed error")
                message = error.get("message")
                raise Person2AIServiceError(
                    message if isinstance(message, str) else "AI analysis failed"
                )
            if "result" not in response:
                raise Person2AIServiceError("AI worker response is missing result data")
            return normalize_person2_result(response["result"])

    def close(self) -> None:
        with self._lock:
            process = self._process
            self._process = None
            if process is None:
                return
            if process.stdin is not None:
                try:
                    process.stdin.close()
                except OSError:
                    pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def _get_worker(self) -> subprocess.Popen[str]:
        if self._process is not None and self._process.poll() is None:
            return self._process
        self._discard_worker()
        if not self._ai_directory.is_dir():
            raise Person2AIServiceError(
                f"AI directory does not exist: {self._ai_directory}"
            )
        try:
            self._process = subprocess.Popen(
                [sys.executable, str(self._worker_script)],
                cwd=self._ai_directory,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except OSError as error:
            raise Person2AIServiceError(f"Could not start AI worker: {error}") from error
        return self._process

    def _discard_worker(self) -> None:
        process = self._process
        self._process = None
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()