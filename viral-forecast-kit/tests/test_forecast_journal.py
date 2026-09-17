"""Tests for the forecast journal.

Run: python3 -m pytest viral-forecast-kit/tests -q
  or python3 viral-forecast-kit/tests/test_forecast_journal.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import forecast_journal as fj  # noqa: E402

T0 = datetime(2026, 9, 17, 6, 0, tzinfo=timezone.utc)


def write_candidates(path: Path, count: int) -> Path:
    lines = ["video_id,url,creator,published_at"]
    for index in range(1, count + 1):
        lines.append(
            f"v{index:02d},https://example.test/v{index:02d},creator{index % 4},"
            f"{fj.fmt_ts(T0 - timedelta(hours=8))}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_observations(path: Path, rows: list[tuple[str, datetime, int]]) -> Path:
    lines = ["video_id,observed_at,views"]
    lines += [f"{video_id},{fj.fmt_ts(moment)},{views}" for video_id, moment, views in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def setup_cohort(tmp: Path, cohort: str = "T1", count: int = 8) -> None:
    fj.JOURNAL_DIR = tmp / "journal"
    candidates = write_candidates(tmp / "candidates.csv", count)
    assert fj.main(["init", "--cohort", cohort, "--niche", "test", "--candidates", str(candidates)]) == 0


def observe(tmp: Path, cohort: str, rows: list[tuple[str, datetime, int]], command: str = "observe") -> int:
    path = write_observations(tmp / f"obs-{command}-{len(rows)}-{rows[0][2]}.csv", rows)
    return fj.main([command, "--cohort", cohort, "--observations", str(path)])


def linear_cohort(tmp: Path, count: int = 8) -> None:
    """v01 fastest, v08 slowest, with two pre-cutoff observations each."""
    setup_cohort(tmp, count=count)
    first, second = [], []
    for index in range(1, count + 1):
        rate = (count + 1 - index) * 1000
        first.append((f"v{index:02d}", T0, 10_000))
        second.append((f"v{index:02d}", T0 + timedelta(hours=3), 10_000 + 3 * rate))
    observe(tmp, "T1", first)
    observe(tmp, "T1", second)


# -- interval maths ---------------------------------------------------------
def test_velocity_and_change(tmp_path: Path) -> None:
    setup_cohort(tmp_path)
    observe(tmp_path, "T1", [("v01", T0, 12_000)])
    observe(tmp_path, "T1", [("v01", T0 + timedelta(hours=3), 21_000)])
    observe(tmp_path, "T1", [("v01", T0 + timedelta(hours=6), 39_000)])
    row = next(r for r in fj.metrics_table(fj.load("T1")) if r["video_id"] == "v01")
    assert row["previous_views_per_hour"] == 3000.0
    assert row["recent_views_per_hour"] == 6000.0
    assert row["velocity_change"] == 3000.0


def test_uneven_interval_uses_actual_elapsed_time(tmp_path: Path) -> None:
    setup_cohort(tmp_path)
    observe(tmp_path, "T1", [("v01", T0, 1_000)])
    observe(tmp_path, "T1", [("v01", T0 + timedelta(hours=4, minutes=30), 10_000)])
    row = next(r for r in fj.metrics_table(fj.load("T1")) if r["video_id"] == "v01")
    assert row["recent_views_per_hour"] == 2000.0


def test_single_observation_is_unrankable(tmp_path: Path) -> None:
    setup_cohort(tmp_path)
    observe(tmp_path, "T1", [("v01", T0, 1_000)])
    row = next(r for r in fj.metrics_table(fj.load("T1")) if r["video_id"] == "v01")
    assert row["insufficient_data"] and row["recent_views_per_hour"] is None


# -- freezing ---------------------------------------------------------------
def test_freeze_records_both_pick_sets(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    cutoff = fj.fmt_ts(T0 + timedelta(hours=3))
    assert fj.main(["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v01,v04,v07"]) == 0
    forecast = fj.load("T1")["forecast"]
    assert forecast["model_picks"] == ["v01", "v04", "v07"]
    assert forecast["velocity_baseline_picks"] == ["v01", "v02", "v03"]
    assert forecast["undocumented_picks"] == ["v01", "v04", "v07"]
    assert forecast["checksum"] == fj.checksum(forecast)


def test_freeze_refuses_to_overwrite(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    cutoff = fj.fmt_ts(T0 + timedelta(hours=3))
    assert fj.main(["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v01,v02,v03"]) == 0
    assert fj.main(["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v04,v05,v06"]) == 1
    assert fj.load("T1")["forecast"]["model_picks"] == ["v01", "v02", "v03"]


def test_freeze_rejects_data_past_the_cutoff(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    assert fj.main(["freeze", "--cohort", "T1", "--cutoff", fj.fmt_ts(T0), "--picks", "v01,v02,v03"]) == 1
    assert fj.load("T1")["forecast"] is None


def test_freeze_rejects_unknown_pick(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    cutoff = fj.fmt_ts(T0 + timedelta(hours=3))
    assert fj.main(["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v01,v02,v99"]) == 1


def test_reasons_must_match_picks(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    reasons = tmp_path / "reasons.json"
    reasons.write_text(json.dumps({"v05": "stray"}), encoding="utf-8")
    cutoff = fj.fmt_ts(T0 + timedelta(hours=3))
    args = ["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v01,v02,v03", "--reasons", str(reasons)]
    assert fj.main(args) == 1


def test_init_will_not_replace_a_frozen_cohort(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    cutoff = fj.fmt_ts(T0 + timedelta(hours=3))
    fj.main(["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v01,v02,v03"])
    candidates = write_candidates(tmp_path / "other.csv", 8)
    args = ["init", "--cohort", "T1", "--niche", "test", "--candidates", str(candidates), "--replace"]
    assert fj.main(args) == 1


# -- scoring ----------------------------------------------------------------
def score_report(tmp_path: Path, model_picks: str, outcome_gains: dict[str, int]) -> dict:
    linear_cohort(tmp_path)
    cutoff_dt = T0 + timedelta(hours=3)
    fj.main(["freeze", "--cohort", "T1", "--cutoff", fj.fmt_ts(cutoff_dt), "--picks", model_picks])
    record = fj.load("T1")
    rows = []
    for video_id, gain in outcome_gains.items():
        base = fj._views_at(record, video_id, cutoff_dt)
        rows.append((video_id, cutoff_dt + timedelta(hours=48), base + gain))
    observe(tmp_path, "T1", rows, command="outcome")

    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        assert fj.main(["score", "--cohort", "T1", "--json"]) == 0
    return json.loads(buffer.getvalue())


def test_top_quarter_and_hit_counting(tmp_path: Path) -> None:
    gains = {f"v{index:02d}": (9 - index) * 100 for index in range(1, 9)}
    report = score_report(tmp_path, "v01,v04,v07", gains)
    assert report["top_quarter_size"] == 2  # ceil(8/4)
    assert report["top_quarter"] == ["v01", "v02"]
    assert report["model"]["hits"] == ["v01"]
    assert report["model"]["misses"] == ["v04", "v07"]
    assert report["velocity_baseline"]["hits"] == ["v01", "v02"]
    assert report["checksum_ok"] is True


def test_boundary_tie_is_reported_and_included(tmp_path: Path) -> None:
    gains = {f"v{index:02d}": 100 for index in range(1, 9)}
    report = score_report(tmp_path, "v01,v02,v03", gains)
    assert report["boundary_ties"] == [f"v{index:02d}" for index in range(1, 9)]
    assert len(report["top_quarter"]) == 8
    assert report["model"]["misses"] == []


def test_missing_outcome_is_excluded_not_a_miss(tmp_path: Path) -> None:
    gains = {f"v{index:02d}": (9 - index) * 100 for index in range(1, 9)}
    gains.pop("v04")
    report = score_report(tmp_path, "v01,v04,v07", gains)
    assert report["unmeasured_candidates"] == ["v04"]
    assert report["model"]["unmeasured"] == ["v04"]
    assert "v04" not in report["model"]["misses"]
    assert report["measured_candidates"] == 7


def test_score_flags_a_tampered_forecast(tmp_path: Path) -> None:
    gains = {f"v{index:02d}": (9 - index) * 100 for index in range(1, 9)}
    score_report(tmp_path, "v01,v04,v07", gains)
    record = fj.load("T1")
    record["forecast"]["model_picks"] = ["v01", "v02", "v03"]
    fj.save(record)
    assert fj.main(["verify", "--cohort", "T1"]) == 2


def test_verify_passes_on_an_untouched_forecast(tmp_path: Path) -> None:
    linear_cohort(tmp_path)
    cutoff = fj.fmt_ts(T0 + timedelta(hours=3))
    fj.main(["freeze", "--cohort", "T1", "--cutoff", cutoff, "--picks", "v01,v02,v03"])
    assert fj.main(["verify", "--cohort", "T1"]) == 0


# -- input validation -------------------------------------------------------
def test_duplicate_observation_is_ignored(tmp_path: Path) -> None:
    setup_cohort(tmp_path)
    observe(tmp_path, "T1", [("v01", T0, 1_000)])
    observe(tmp_path, "T1", [("v01", T0, 1_000)])
    assert len(fj.load("T1")["observations"]) == 1


def test_observation_for_unknown_video_is_rejected(tmp_path: Path) -> None:
    setup_cohort(tmp_path)
    assert observe(tmp_path, "T1", [("v99", T0, 1_000)]) == 1


def test_duplicate_candidate_is_rejected(tmp_path: Path) -> None:
    fj.JOURNAL_DIR = tmp_path / "journal"
    path = tmp_path / "dupes.csv"
    path.write_text(
        "video_id,url,creator,published_at\n"
        f"v01,https://example.test/a,c1,{fj.fmt_ts(T0)}\n"
        f"v01,https://example.test/b,c2,{fj.fmt_ts(T0)}\n",
        encoding="utf-8",
    )
    assert fj.main(["init", "--cohort", "T2", "--niche", "test", "--candidates", str(path)]) == 1


def test_non_monotonic_observations_are_an_error(tmp_path: Path) -> None:
    setup_cohort(tmp_path)
    observe(tmp_path, "T1", [("v01", T0, 1_000)])
    record = fj.load("T1")
    record["observations"].append({"video_id": "v01", "observed_at": fj.fmt_ts(T0), "views": 2_000})
    try:
        fj.intervals(fj.observations_for(record, "v01"))
    except fj.JournalError:
        return
    raise AssertionError("expected a JournalError for a zero-length interval")


if __name__ == "__main__":
    import tempfile
    import traceback

    failures = 0
    for name, test in sorted(globals().items()):
        if not name.startswith("test_") or not callable(test):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                test(Path(tmp))
                print(f"ok   {name}")
            except Exception:  # noqa: BLE001 - standalone runner reports and continues
                failures += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)
