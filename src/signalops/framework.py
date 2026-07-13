from __future__ import annotations

import json
import random
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class StepError(RuntimeError):
    pass


class JsonlLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._run_event_counts: dict[str, int] = {}

    def event(self, run_id: str, step: str, event_type: str, payload: dict[str, Any]) -> None:
        record = {
            "timestamp": self._demo_timestamp(run_id),
            "run_id": run_id,
            "step": step,
            "event_type": event_type,
            "payload": to_jsonable(payload),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _demo_timestamp(self, run_id: str) -> str:
        event_count = self._run_event_counts.get(run_id, 0)
        self._run_event_counts[run_id] = event_count + 1
        offset = timedelta(seconds=event_count * 2)
        return (datetime.now(timezone.utc) + offset).isoformat()


class RunContext:
    def __init__(self, run_id: str, logger: JsonlLogger):
        self.run_id = run_id
        self.logger = logger

    def log(self, step: str, event_type: str, payload: dict[str, Any]) -> None:
        self.logger.event(self.run_id, step, event_type, payload)


class AgentStep(ABC, Generic[TIn, TOut]):
    name: str

    @abstractmethod
    def run(self, value: TIn, context: RunContext) -> TOut:
        raise NotImplementedError

    def __call__(self, value: TIn, context: RunContext) -> TOut:
        context.log(self.name, "started", {"input": value})
        try:
            output = self.run(value, context)
        except Exception as exc:
            context.log(
                self.name,
                "failed",
                {"error": str(exc), "traceback": traceback.format_exc(limit=5)},
            )
            raise
        context.log(self.name, "finished", {"output": output})
        return output


def retry_call(
    operation: Callable[[], TOut],
    *,
    retries: int = 3,
    base_delay_seconds: float = 0.25,
    retryable: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError, StepError),
) -> TOut:
    last_error: BaseException | None = None
    for attempt in range(1, retries + 1):
        try:
            return operation()
        except retryable as exc:
            last_error = exc
            if attempt == retries:
                break
            jitter = random.uniform(0, base_delay_seconds)
            time.sleep(base_delay_seconds * attempt + jitter)
    raise StepError(f"operation failed after {retries} attempts: {last_error}") from last_error


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
