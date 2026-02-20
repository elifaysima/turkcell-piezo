from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import time
import numpy as np

from common import StepPacket


@dataclass
class Bucket:
    packets: List[StepPacket] = field(default_factory=list)


# site_id -> ts -> Bucket
BUCKETS: Dict[str, Dict[int, Bucket]] = defaultdict(lambda: defaultdict(Bucket))

# site_id -> history: (ts, flow, ratio, n_used)
FUSED_HISTORY: Dict[str, deque] = defaultdict(lambda: deque(maxlen=900))


@dataclass(frozen=True)
class FusionThresholds:
    close_lag_s: int = 2
    outlier_mad_k: float = 6.0


THR = FusionThresholds()


def ingest(pkt: StepPacket) -> None:
    BUCKETS[pkt.site_id][pkt.ts].packets.append(pkt)


def _robust_filter(values: List[float], k: float) -> List[float]:
    if len(values) < 3:
        return values
    med = float(np.median(values))
    mad = float(np.median([abs(v - med) for v in values]))
    mad = max(mad, 1e-6)
    kept = [v for v in values if abs(v - med) / mad < k]
    return kept if kept else values


def fuse_bucket(site_id: str, ts: int, thr: FusionThresholds = THR) -> Optional[Tuple[float, float, int]]:
    bucket = BUCKETS.get(site_id, {}).get(ts)
    if bucket is None or not bucket.packets:
        return None

    totals = [float(p.steps_dir1 + p.steps_dir2) for p in bucket.packets]
    dir1s = [float(p.steps_dir1) for p in bucket.packets]
    dir2s = [float(p.steps_dir2) for p in bucket.packets]

    totals_f = _robust_filter(totals, thr.outlier_mad_k)
    dir1s_f = _robust_filter(dir1s, thr.outlier_mad_k)
    dir2s_f = _robust_filter(dir2s, thr.outlier_mad_k)

    flow = float(np.median(totals_f))
    d1 = float(np.median(dir1s_f))
    d2 = float(np.median(dir2s_f))
    ratio = d1 / max(d1 + d2, 1.0)
    n_used = int(min(len(totals_f), len(dir1s_f), len(dir2s_f)))

    FUSED_HISTORY[site_id].append((ts, flow, ratio, n_used))

    # cleanup
    del BUCKETS[site_id][ts]
    if not BUCKETS[site_id]:
        del BUCKETS[site_id]

    return flow, ratio, n_used


def fuse_ready(now_ts: Optional[int] = None, thr: FusionThresholds = THR) -> List[Tuple[str, int, float, float, int]]:
    """
    close_lag_s kadar geride kalan bucket'ları fuse eder.
    """
    if now_ts is None:
        now_ts = int(time.time())

    out: List[Tuple[str, int, float, float, int]] = []
    for site_id, by_ts in list(BUCKETS.items()):
        ready = [t for t in by_ts.keys() if t <= now_ts - thr.close_lag_s]
        for ts in sorted(ready):
            res = fuse_bucket(site_id, ts, thr)
            if res is not None:
                flow, ratio, n_used = res
                out.append((site_id, ts, flow, ratio, n_used))
    return out
