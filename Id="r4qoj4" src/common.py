from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json

REQUIRED_FIELDS = {"site_id", "module_id", "ts", "window_s", "steps_dir1", "steps_dir2"}


@dataclass(frozen=True)
class StepPacket:
    """
    StepPacket: sensörden (veya fake publisher'dan) MQTT ile gelen tek pencere (window_s) özet verisi.
    """
    site_id: str
    module_id: str
    ts: int # Unix epoch seconds
    window_s: int # aggregation window in seconds (expected 1)
    steps_dir1: int
    steps_dir2: int
    vcap: Optional[float] = None # optional energy metric


def decode_packet(payload: str) -> StepPacket:
    """
    JSON string -> StepPacket
    Schema hatalarında ValueError fırlatır.
    """
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ValueError("Payload must be a JSON object")

    missing = REQUIRED_FIELDS - set(obj.keys())
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")

    try:
        pkt = StepPacket(
            site_id=str(obj["site_id"]),
            module_id=str(obj["module_id"]),
            ts=int(obj["ts"]),
            window_s=int(obj["window_s"]),
            steps_dir1=int(obj["steps_dir1"]),
            steps_dir2=int(obj["steps_dir2"]),
            vcap=float(obj["vcap"]) if "vcap" in obj and obj["vcap"] is not None else None,
        )
    except Exception as e:
        raise ValueError(f"Bad field types: {e}") from e

    if pkt.window_s <= 0:
        raise ValueError("window_s must be > 0")
    if pkt.ts <= 0:
        raise ValueError("ts must be a Unix epoch seconds integer > 0")
    if pkt.steps_dir1 < 0 or pkt.steps_dir2 < 0:
        raise ValueError("steps_dir1/steps_dir2 must be >= 0")

    return pkt


def encode_packet(pkt: StepPacket) -> str:
    """
    StepPacket -> compact JSON string
    """
    d: Dict[str, Any] = {
        "site_id": pkt.site_id,
        "module_id": pkt.module_id,
        "ts": pkt.ts,
        "window_s": pkt.window_s,
        "steps_dir1": pkt.steps_dir1,
        "steps_dir2": pkt.steps_dir2,
    }
    if pkt.vcap is not None:
        d["vcap"] = pkt.vcap
    return json.dumps(d, separators
