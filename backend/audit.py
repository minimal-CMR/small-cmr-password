import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from fastapi import Request

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
APP_NAME = os.getenv("APP_NAME", "small-cmr-base")
ENV = os.getenv("APP_ENV", "prod")

_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 10

_CATEGORIES = {
    "audit": "audit.log",
    "app": "app.log",
    "access": "access.log",
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "app": APP_NAME,
            "env": ENV,
            "category": getattr(record, "category", record.name.split(".")[-1]),
            "message": record.getMessage(),
        }
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _build_logger(category: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(f"audit.{category}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        LOG_DIR / filename, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8",
    )
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    return logger


def init_audit_logging() -> None:
    for category, filename in _CATEGORIES.items():
        _build_logger(category, filename)


def _emit(category: str, message: str, fields: dict[str, Any], level: int = logging.INFO) -> None:
    logger = logging.getLogger(f"audit.{category}")
    if not logger.handlers:
        _build_logger(category, _CATEGORIES[category])
    logger.log(level, message, extra={"category": category, "fields": fields})


def _client_info(request: Optional[Request]) -> dict[str, Any]:
    if request is None:
        return {"ip": None, "ua": None}
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
    return {"ip": ip, "ua": request.headers.get("user-agent")}


def log_password_event(
    *, action: str, actor_id: Optional[int], actor_email: Optional[str],
    target_id: Optional[int], target_email: Optional[str],
    request: Optional[Request] = None, success: bool = True, reason: Optional[str] = None,
) -> None:
    fields = {
        "event": "password_change", "action": action,
        "actor_id": actor_id, "actor_email": actor_email,
        "target_id": target_id, "target_email": target_email,
        "success": success, "reason": reason,
        **_client_info(request),
    }
    _emit("audit", f"password_change action={action} target={target_email}", fields)


def log_login(
    *, email: str, success: bool, user_id: Optional[int] = None,
    request: Optional[Request] = None, reason: Optional[str] = None,
) -> None:
    fields = {
        "event": "login", "email": email, "user_id": user_id,
        "success": success, "reason": reason,
        **_client_info(request),
    }
    _emit("audit", f"login email={email} success={success}", fields)


def log_access(
    *, method: str, path: str, status_code: int, duration_ms: float,
    user_id: Optional[int], request: Request,
) -> None:
    fields = {
        "event": "http_request", "method": method, "path": path,
        "status": status_code, "duration_ms": round(duration_ms, 2),
        "user_id": user_id, **_client_info(request),
    }
    _emit("access", f"{method} {path} {status_code}", fields)


def log_app(message: str, level: str = "info", **fields: Any) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    _emit("app", message, fields, level=lvl)
