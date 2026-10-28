"""Benchmark utility for Disaster Response System metrics audit.

Measures:
1. AI classification time (Relevance model, Priority model, Full NLP pipeline)
2. Average AI confidence across database records and test samples
3. Dashboard response time (HTTP GET /api/emergencies)

NOTE: This is a measurement utility for metrics audit only, NOT production code.
"""

from __future__ import annotations

import json
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Any
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
backend_path = ROOT / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.services.nlp_service import _load_models, analyze_message


def benchmark_ai_inference(runs: int = 500, warmup: int = 50) -> dict[str, Any]:
    print(f"Loading production models for AI latency benchmark (warmup={warmup}, runs={runs})...")
    relevance, priority = _load_models()

    # Benchmark test payloads
    relevant_text = "Severe flooding in our neighborhood, water is rising rapidly and people are trapped on roofs."
    not_relevant_text = "The weather was quite nice today, had a great walk in the park."
    structured_features = {
        "injured": 1,
        "trapped": 1,
        "fire": 0,
        "medical_emergency": 1,
        "people_affected": 4,
        "urgency": 4,
    }

    # Warmup
    for _ in range(warmup):
        _ = relevance.predict(relevant_text)
        _ = priority.predict(relevant_text, **structured_features)
        _ = analyze_message(relevant_text, **structured_features)
        _ = analyze_message(not_relevant_text)

    # 1. Relevance model alone
    rel_times = []
    rel_confidences = []
    for _ in range(runs):
        t0 = time.perf_counter()
        res = relevance.predict(relevant_text)
        t1 = time.perf_counter()
        rel_times.append((t1 - t0) * 1000.0)
        rel_confidences.append(res["confidence"])

    # 2. Priority model alone
    pri_times = []
    pri_confidences = []
    for _ in range(runs):
        t0 = time.perf_counter()
        res = priority.predict(relevant_text, **structured_features)
        t1 = time.perf_counter()
        pri_times.append((t1 - t0) * 1000.0)
        pri_confidences.append(res["confidence"])

    # 3. Full pipeline (Relevant message -> relevance + safety + priority)
    full_rel_times = []
    full_rel_confidences = []
    for _ in range(runs):
        t0 = time.perf_counter()
        res = analyze_message(relevant_text, **structured_features)
        t1 = time.perf_counter()
        full_rel_times.append((t1 - t0) * 1000.0)
        full_rel_confidences.append({
            "relevance": res["ai_relevance_confidence"],
            "priority": res["ai_priority_confidence"],
        })

    # 4. Full pipeline (Not-relevant message -> relevance fast exit)
    full_not_rel_times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        res = analyze_message(not_relevant_text)
        t1 = time.perf_counter()
        full_not_rel_times.append((t1 - t0) * 1000.0)

    def stats(data: list[float]) -> dict[str, float]:
        return {
            "mean_ms": round(statistics.mean(data), 3),
            "median_ms": round(statistics.median(data), 3),
            "min_ms": round(min(data), 3),
            "max_ms": round(max(data), 3),
            "stdev_ms": round(statistics.stdev(data), 3),
            "p95_ms": round(sorted(data)[int(len(data) * 0.95)], 3),
            "p99_ms": round(sorted(data)[int(len(data) * 0.99)], 3),
        }

    return {
        "runs": runs,
        "warmup": warmup,
        "relevance_alone": stats(rel_times),
        "priority_alone": stats(pri_times),
        "full_pipeline_relevant": stats(full_rel_times),
        "full_pipeline_not_relevant": stats(full_not_rel_times),
    }


def audit_database_confidences() -> dict[str, Any]:
    db_path = ROOT / "backend" / "disaster_response.db"
    if not db_path.exists():
        return {"error": "Database not found"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, message, ai_relevant, ai_relevance_confidence, ai_priority, ai_priority_confidence
        FROM emergencies
    """)
    rows = cursor.fetchall()
    conn.close()

    rel_confs = []
    pri_confs = []
    records = []

    for r in rows:
        rec_id, msg, ai_rel, rel_conf, ai_pri, pri_conf = r
        if rel_conf is not None:
            rel_confs.append(float(rel_conf))
        if pri_conf is not None:
            pri_confs.append(float(pri_conf))
        records.append({
            "id": rec_id,
            "message": msg[:50] + "..." if len(msg) > 50 else msg,
            "ai_relevant": bool(ai_rel),
            "relevance_confidence": rel_conf,
            "ai_priority": ai_pri,
            "priority_confidence": pri_conf,
        })

    all_confs = rel_confs + pri_confs

    return {
        "total_records": len(rows),
        "relevance_confidence_count": len(rel_confs),
        "priority_confidence_count": len(pri_confs),
        "relevance_confidence_mean": round(statistics.mean(rel_confs), 4) if rel_confs else None,
        "priority_confidence_mean": round(statistics.mean(pri_confs), 4) if pri_confs else None,
        "combined_confidence_mean": round(statistics.mean(all_confs), 4) if all_confs else None,
        "relevance_confidence_median": round(statistics.median(rel_confs), 4) if rel_confs else None,
        "priority_confidence_median": round(statistics.median(pri_confs), 4) if pri_confs else None,
        "records": records,
    }


def benchmark_dashboard_response_time(
    url: str = "http://localhost:8000/api/emergencies",
    requests_count: int = 200,
    warmup: int = 20,
) -> dict[str, Any]:
    print(f"Benchmarking Dashboard API ({url}) with {warmup} warmup and {requests_count} requests...")
    # Warmup
    for _ in range(warmup):
        req = urllib.request.Request(url, headers={"User-Agent": "Dashboard-Benchmark/1.0"})
        with urllib.request.urlopen(req) as resp:
            _ = resp.read()

    times = []
    status_codes = []
    for _ in range(requests_count):
        req = urllib.request.Request(url, headers={"User-Agent": "Dashboard-Benchmark/1.0"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req) as resp:
            _ = resp.read()
            status_codes.append(resp.status)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

    return {
        "endpoint": url,
        "requests": requests_count,
        "warmup": warmup,
        "mean_ms": round(statistics.mean(times), 3),
        "median_ms": round(statistics.median(times), 3),
        "min_ms": round(min(times), 3),
        "max_ms": round(max(times), 3),
        "stdev_ms": round(statistics.stdev(times), 3),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 3),
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 3),
        "all_200_ok": all(code == 200 for code in status_codes),
    }


if __name__ == "__main__":
    ai_results = benchmark_ai_inference(runs=500, warmup=50)
    print("\n--- AI INFERENCE LATENCY BENCHMARK ---")
    print(json.dumps(ai_results, indent=2))

    db_conf = audit_database_confidences()
    print("\n--- DATABASE CONFIDENCE AUDIT ---")
    print(json.dumps(db_conf, indent=2))

    dash_results = benchmark_dashboard_response_time(requests_count=200, warmup=20)
    print("\n--- DASHBOARD API LATENCY BENCHMARK ---")
    print(json.dumps(dash_results, indent=2))
