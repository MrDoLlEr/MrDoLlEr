#!/usr/bin/env python3
"""Forecast journal for short-form video cohorts.

Records a fixed cohort, its timestamped view observations, and a frozen
forecast. Refuses to overwrite a frozen forecast. Scores the frozen picks
against a plain recent-velocity baseline once outcomes are collected.

What this does NOT do: prove when a decision was made. The checksum detects a
changed record, nothing more. For a public test, place the frozen block in an
externally timestamped record before the observation window opens.

Usage
-----
  forecast_journal.py init     --cohort C1 --niche surreal-reveal --candidates candidates.csv
  forecast_journal.py observe  --cohort C1 --observations obs-t0.csv
  forecast_journal.py metrics  --cohort C1
  forecast_journal.py freeze   --cohort C1 --cutoff 2026-09-17T18:00:00Z \
                               --picks v03,v11,v18 --reasons reasons.json
  forecast_journal.py outcome  --cohort C1 --observations obs-t48.csv
  forecast_journal.py score    --cohort C1
  forecast_journal.py verify   --cohort C1

CSV formats
-----------
candidates.csv   video_id,url,creator,published_at[,source_evidence,notes]
observations.csv video_id,observed_at,views[,likes,comments,shares,source_evidence]

All timestamps are ISO-8601. A trailing "Z" is accepted and treated as UTC.
Missing fields stay missing; nothing is inferred or back-filled.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

JOURNAL_DIR = Path(__file__).resolve().parent / "journal"
SCHEMA = 1


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
class JournalError(RuntimeError):
    """A refusal or a malformed input. Reported to the caller, not raised past main."""


def parse_ts(value: str, field: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        raise JournalError(f"{field}: missing timestamp")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise JournalError(f"{field}: not an ISO-8601 timestamp: {raw!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fmt_ts(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.exists():
        raise JournalError(f"no such file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in required if column not in (reader.fieldnames or [])]
        if missing:
            raise JournalError(f"{path.name}: missing column(s): {', '.join(missing)}")
        rows = [row for row in reader if any((value or "").strip() for value in row.values())]
    if not rows:
        raise JournalError(f"{path.name}: no data rows")
    return rows


def journal_path(cohort_id: str) -> Path:
    safe = "".join(ch for ch in cohort_id if ch.isalnum() or ch in "-_")
    if safe != cohort_id or not safe:
        raise JournalError("cohort id must be alphanumeric, dash or underscore")
    return JOURNAL_DIR / f"{safe}.json"


def load(cohort_id: str) -> dict:
    path = journal_path(cohort_id)
    if not path.exists():
        raise JournalError(f"cohort {cohort_id!r} not initialised ({path})")
    return json.loads(path.read_text(encoding="utf-8"))


def save(record: dict) -> Path:
    path = journal_path(record["cohort_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def checksum(payload: dict) -> str:
    body = {key: value for key, value in payload.items() if key != "checksum"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# observation maths
# --------------------------------------------------------------------------
def observations_for(record: dict, video_id: str, at_or_before: datetime | None = None) -> list[dict]:
    rows = [row for row in record["observations"] if row["video_id"] == video_id]
    if at_or_before is not None:
        rows = [row for row in rows if parse_ts(row["observed_at"], "observed_at") <= at_or_before]
    return sorted(rows, key=lambda row: parse_ts(row["observed_at"], "observed_at"))


def intervals(rows: list[dict]) -> list[dict]:
    """Views per hour between consecutive observations, using actual elapsed time."""
    out = []
    for earlier, later in zip(rows, rows[1:]):
        start = parse_ts(earlier["observed_at"], "observed_at")
        end = parse_ts(later["observed_at"], "observed_at")
        elapsed_hours = (end - start).total_seconds() / 3600.0
        if elapsed_hours <= 0:
            raise JournalError(
                f"{later['video_id']}: observations are not strictly increasing in time "
                f"({fmt_ts(start)} -> {fmt_ts(end)})"
            )
        out.append(
            {
                "from": fmt_ts(start),
                "to": fmt_ts(end),
                "elapsed_hours": round(elapsed_hours, 4),
                "view_gain": later["views"] - earlier["views"],
                "views_per_hour": round((later["views"] - earlier["views"]) / elapsed_hours, 2),
            }
        )
    return out


def metrics_table(record: dict, cutoff: datetime | None = None) -> list[dict]:
    table = []
    for candidate in record["candidates"]:
        video_id = candidate["video_id"]
        rows = observations_for(record, video_id, cutoff)
        legs = intervals(rows)
        recent = legs[-1]["views_per_hour"] if legs else None
        previous = legs[-2]["views_per_hour"] if len(legs) >= 2 else None
        table.append(
            {
                "video_id": video_id,
                "creator": candidate.get("creator", ""),
                "observations": len(rows),
                "latest_views": rows[-1]["views"] if rows else None,
                "latest_observed_at": rows[-1]["observed_at"] if rows else None,
                "intervals": legs,
                "recent_views_per_hour": recent,
                "previous_views_per_hour": previous,
                "velocity_change": None if recent is None or previous is None else round(recent - previous, 2),
                "insufficient_data": len(legs) < 1,
            }
        )
    return table


def rank_by(table: list[dict], key: str, limit: int) -> dict:
    scored = [row for row in table if row.get(key) is not None]
    unscored = [row["video_id"] for row in table if row.get(key) is None]
    scored.sort(key=lambda row: (-row[key], row["video_id"]))
    picks = [row["video_id"] for row in scored[:limit]]
    ties = []
    if len(scored) > limit:
        boundary = scored[limit - 1][key]
        ties = [row["video_id"] for row in scored[limit:] if row[key] == boundary]
    return {"picks": picks, "ties_at_cutoff": ties, "unrankable": unscored}


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_init(args: argparse.Namespace) -> int:
    path = journal_path(args.cohort)
    if path.exists() and not args.replace:
        raise JournalError(f"cohort {args.cohort!r} already exists: {path} (use --replace only before freezing)")
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("forecast"):
            raise JournalError(f"cohort {args.cohort!r} carries a frozen forecast and cannot be replaced")

    rows = read_csv(Path(args.candidates), ("video_id", "url", "creator", "published_at"))
    candidates, seen = [], set()
    for row in rows:
        video_id = row["video_id"].strip()
        if not video_id:
            raise JournalError("candidates.csv: blank video_id")
        if video_id in seen:
            raise JournalError(f"candidates.csv: duplicate video_id {video_id!r}")
        seen.add(video_id)
        candidates.append(
            {
                "video_id": video_id,
                "url": row["url"].strip(),
                "creator": row["creator"].strip(),
                "published_at": fmt_ts(parse_ts(row["published_at"], f"{video_id}.published_at")),
                "source_evidence": (row.get("source_evidence") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
            }
        )

    record = {
        "schema": SCHEMA,
        "cohort_id": args.cohort,
        "niche": args.niche,
        "created_at": fmt_ts(datetime.now(timezone.utc)),
        "candidates": candidates,
        "observations": [],
        "forecast": None,
        "outcomes": [],
    }
    written = save(record)
    print(f"initialised cohort {args.cohort!r} with {len(candidates)} candidates -> {written}")
    if len(candidates) < 8:
        print("note: a cohort this small makes top-quartile scoring coarse; 20 is the suggested size")
    return 0


def _ingest_observations(record: dict, path: Path) -> int:
    known = {candidate["video_id"] for candidate in record["candidates"]}
    rows = read_csv(path, ("video_id", "observed_at", "views"))
    existing = {(row["video_id"], row["observed_at"]) for row in record["observations"]}
    added = 0
    for row in rows:
        video_id = row["video_id"].strip()
        if video_id not in known:
            raise JournalError(f"{path.name}: {video_id!r} is not in this cohort")
        observed_at = fmt_ts(parse_ts(row["observed_at"], f"{video_id}.observed_at"))
        try:
            views = int(str(row["views"]).replace(",", "").strip())
        except ValueError as exc:
            raise JournalError(f"{path.name}: {video_id} views is not an integer: {row['views']!r}") from exc
        if views < 0:
            raise JournalError(f"{path.name}: {video_id} views is negative")
        if (video_id, observed_at) in existing:
            continue
        entry = {"video_id": video_id, "observed_at": observed_at, "views": views}
        for optional in ("likes", "comments", "shares"):
            raw = (row.get(optional) or "").strip()
            if raw:
                entry[optional] = int(raw.replace(",", ""))
        evidence = (row.get("source_evidence") or "").strip()
        if evidence:
            entry["source_evidence"] = evidence
        record["observations"].append(entry)
        existing.add((video_id, observed_at))
        added += 1
    record["observations"].sort(key=lambda row: (row["video_id"], row["observed_at"]))
    return added


def cmd_observe(args: argparse.Namespace) -> int:
    record = load(args.cohort)
    added = _ingest_observations(record, Path(args.observations))
    save(record)
    print(f"added {added} observation(s); {len(record['observations'])} on file")
    missing = [
        candidate["video_id"]
        for candidate in record["candidates"]
        if not observations_for(record, candidate["video_id"])
    ]
    if missing:
        print(f"still unobserved: {', '.join(missing)}")
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    record = load(args.cohort)
    cutoff = parse_ts(args.cutoff, "--cutoff") if args.cutoff else None
    table = metrics_table(record, cutoff)
    if args.json:
        print(json.dumps({"cohort_id": record["cohort_id"], "rows": table}, indent=2))
        return 0
    print(f"{'video':<10}{'obs':>4}{'views':>12}{'v/h now':>12}{'v/h prev':>12}{'change':>12}")
    for row in sorted(table, key=lambda item: -(item["recent_views_per_hour"] or -1)):
        print(
            f"{row['video_id']:<10}{row['observations']:>4}"
            f"{'-' if row['latest_views'] is None else row['latest_views']:>12}"
            f"{'-' if row['recent_views_per_hour'] is None else row['recent_views_per_hour']:>12}"
            f"{'-' if row['previous_views_per_hour'] is None else row['previous_views_per_hour']:>12}"
            f"{'-' if row['velocity_change'] is None else row['velocity_change']:>12}"
        )
    thin = [row["video_id"] for row in table if row["insufficient_data"]]
    if thin:
        print(f"\nno velocity yet (needs two observations): {', '.join(thin)}")
    return 0


def cmd_freeze(args: argparse.Namespace) -> int:
    record = load(args.cohort)
    if record.get("forecast"):
        frozen_at = record["forecast"]["frozen_at"]
        raise JournalError(
            f"cohort {args.cohort!r} was frozen at {frozen_at} and will not be overwritten. "
            "Start a new cohort instead."
        )

    cutoff = parse_ts(args.cutoff, "--cutoff")
    picks = [pick.strip() for pick in args.picks.split(",") if pick.strip()]
    if len(picks) != len(set(picks)):
        raise JournalError("--picks contains a duplicate")
    known = {candidate["video_id"] for candidate in record["candidates"]}
    unknown = [pick for pick in picks if pick not in known]
    if unknown:
        raise JournalError(f"--picks not in cohort: {', '.join(unknown)}")
    if len(picks) != args.select:
        raise JournalError(f"--picks has {len(picks)} entries, --select is {args.select}")

    later = [row for row in record["observations"] if parse_ts(row["observed_at"], "observed_at") > cutoff]
    if later:
        raise JournalError(
            f"{len(later)} observation(s) postdate the cutoff. A forecast may only use data "
            "available at or before its cutoff — move the cutoff or start a new cohort."
        )

    table = metrics_table(record, cutoff)
    baseline = rank_by(table, "recent_views_per_hour", args.select)

    reasons = {}
    if args.reasons:
        reasons = json.loads(Path(args.reasons).read_text(encoding="utf-8"))
        if not isinstance(reasons, dict):
            raise JournalError("--reasons must be a JSON object keyed by video_id")
        stray = [key for key in reasons if key not in picks]
        if stray:
            raise JournalError(f"--reasons mentions non-picks: {', '.join(stray)}")
    undocumented = [pick for pick in picks if pick not in reasons]

    forecast = {
        "frozen_at": fmt_ts(datetime.now(timezone.utc)),
        "cutoff": fmt_ts(cutoff),
        "window_hours": args.window_hours,
        "select": args.select,
        "success_rule": (
            f"A selected video is a hit if its absolute view gain over the {args.window_hours}h window "
            "places it in the top quarter of this cohort."
        ),
        "cohort_size": len(record["candidates"]),
        "cohort": sorted(candidate["video_id"] for candidate in record["candidates"]),
        "model_picks": picks,
        "model_reasons": reasons,
        "undocumented_picks": undocumented,
        "velocity_baseline_picks": baseline["picks"],
        "velocity_baseline_ties": baseline["ties_at_cutoff"],
        "velocity_baseline_unrankable": baseline["unrankable"],
        "metrics_at_cutoff": table,
    }
    forecast["checksum"] = checksum(forecast)
    record["forecast"] = forecast
    save(record)

    print(f"frozen at {forecast['frozen_at']} (cutoff {forecast['cutoff']}, window {args.window_hours}h)")
    print(f"  model picks:       {', '.join(picks)}")
    print(f"  velocity baseline: {', '.join(baseline['picks']) or '-'}")
    if baseline["ties_at_cutoff"]:
        print(f"  baseline ties at the boundary: {', '.join(baseline['ties_at_cutoff'])}")
    if undocumented:
        print(f"  warning: no recorded reasoning for {', '.join(undocumented)}")
    print(f"  checksum: {forecast['checksum']}")
    print("  the checksum detects a changed record; it does not prove when you decided")
    return 0


def cmd_outcome(args: argparse.Namespace) -> int:
    record = load(args.cohort)
    if not record.get("forecast"):
        raise JournalError("freeze a forecast before recording outcomes")
    added = _ingest_observations(record, Path(args.observations))
    save(record)
    print(f"added {added} outcome observation(s)")
    return 0


def _views_at(record: dict, video_id: str, moment: datetime) -> int | None:
    rows = observations_for(record, video_id, moment)
    return rows[-1]["views"] if rows else None


def _views_after(record: dict, video_id: str, moment: datetime) -> dict | None:
    """The first observation at or after the window end — the one nearest the boundary."""
    rows = [
        row
        for row in observations_for(record, video_id)
        if parse_ts(row["observed_at"], "observed_at") >= moment
    ]
    return rows[0] if rows else None


def cmd_score(args: argparse.Namespace) -> int:
    record = load(args.cohort)
    forecast = record.get("forecast")
    if not forecast:
        raise JournalError("nothing to score: no frozen forecast")
    if checksum(forecast) != forecast["checksum"]:
        print("WARNING: the frozen forecast no longer matches its checksum. Treat this test as void.")

    cutoff = parse_ts(forecast["cutoff"], "cutoff")
    window_end = cutoff + timedelta(hours=forecast["window_hours"])

    gains, missing = {}, []
    for candidate in record["candidates"]:
        video_id = candidate["video_id"]
        start = _views_at(record, video_id, cutoff)
        end_row = _views_after(record, video_id, window_end)
        if start is None or end_row is None:
            missing.append(video_id)
            continue
        gains[video_id] = {
            "view_gain": end_row["views"] - start,
            "measured_at": end_row["observed_at"],
        }

    if not gains:
        raise JournalError("no candidate has both a cutoff and a post-window observation")

    quartile_size = max(1, math.ceil(len(gains) / 4))
    ordered = sorted(gains.items(), key=lambda item: (-item[1]["view_gain"], item[0]))
    boundary_gain = ordered[min(quartile_size, len(ordered)) - 1][1]["view_gain"]
    top_quarter = [video_id for video_id, row in ordered if row["view_gain"] >= boundary_gain]
    boundary_ties = [
        video_id for video_id, row in ordered if row["view_gain"] == boundary_gain
    ]

    def hits(picks: list[str]) -> dict:
        scored = [pick for pick in picks if pick in gains]
        return {
            "picks": picks,
            "hits": [pick for pick in scored if pick in top_quarter],
            "misses": [pick for pick in scored if pick not in top_quarter],
            "unmeasured": [pick for pick in picks if pick not in gains],
        }

    model = hits(forecast["model_picks"])
    baseline = hits(forecast["velocity_baseline_picks"])

    report = {
        "cohort_id": record["cohort_id"],
        "cutoff": forecast["cutoff"],
        "window_end": fmt_ts(window_end),
        "measured_candidates": len(gains),
        "unmeasured_candidates": missing,
        "top_quarter_size": len(top_quarter),
        "top_quarter": top_quarter,
        "boundary_gain": boundary_gain,
        "boundary_ties": boundary_ties if len(boundary_ties) > 1 else [],
        "checksum_ok": checksum(forecast) == forecast["checksum"],
        "model": model,
        "velocity_baseline": baseline,
        "view_gains": {video_id: row["view_gain"] for video_id, row in ordered},
    }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"cohort {record['cohort_id']}  cutoff {forecast['cutoff']}  window {forecast['window_hours']}h")
    print(f"measured {len(gains)}/{len(record['candidates'])} candidates; top quarter = {len(top_quarter)} slot(s)")
    if missing:
        print(f"unmeasured (excluded, not counted as misses): {', '.join(missing)}")
    if len(boundary_ties) > 1:
        print(f"tie at the quartile boundary ({boundary_gain} views): {', '.join(boundary_ties)}")
    print(f"\ntop quarter by view gain: {', '.join(top_quarter)}")
    for label, result in (("model", model), ("velocity baseline", baseline)):
        print(
            f"\n{label}: {len(result['hits'])}/{len(result['picks']) - len(result['unmeasured'])} hit"
            f"  picks={', '.join(result['picks'])}"
        )
        if result["hits"]:
            print(f"  hits:   {', '.join(result['hits'])}")
        if result["misses"]:
            print(f"  misses: {', '.join(result['misses'])}")
        if result["unmeasured"]:
            print(f"  unmeasured: {', '.join(result['unmeasured'])}")
    print("\nOne cohort is one data point. Repeat across fresh cohorts before claiming an advantage.")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    record = load(args.cohort)
    forecast = record.get("forecast")
    if not forecast:
        print("no frozen forecast on this cohort")
        return 1
    recomputed = checksum(forecast)
    ok = recomputed == forecast["checksum"]
    print(f"stored:     {forecast['checksum']}")
    print(f"recomputed: {recomputed}")
    print("match: the frozen block is unchanged since freeze" if ok else "MISMATCH: the frozen block was edited")
    print("This checks the record's integrity only. It is not evidence of decision time.")
    return 0 if ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a cohort from candidates.csv")
    init.add_argument("--cohort", required=True)
    init.add_argument("--niche", required=True)
    init.add_argument("--candidates", required=True)
    init.add_argument("--replace", action="store_true", help="replace an unfrozen cohort of the same id")
    init.set_defaults(func=cmd_init)

    observe = subparsers.add_parser("observe", help="append timestamped observations")
    observe.add_argument("--cohort", required=True)
    observe.add_argument("--observations", required=True)
    observe.set_defaults(func=cmd_observe)

    metrics = subparsers.add_parser("metrics", help="views/hour per interval and its change")
    metrics.add_argument("--cohort", required=True)
    metrics.add_argument("--cutoff", help="ignore observations after this ISO timestamp")
    metrics.add_argument("--json", action="store_true")
    metrics.set_defaults(func=cmd_metrics)

    freeze = subparsers.add_parser("freeze", help="write the forecast; refuses to overwrite one")
    freeze.add_argument("--cohort", required=True)
    freeze.add_argument("--cutoff", required=True)
    freeze.add_argument("--picks", required=True, help="comma-separated video ids")
    freeze.add_argument("--reasons", help="JSON object keyed by video_id")
    freeze.add_argument("--select", type=int, default=3)
    freeze.add_argument("--window-hours", type=int, default=48)
    freeze.set_defaults(func=cmd_freeze)

    outcome = subparsers.add_parser("outcome", help="append post-window observations")
    outcome.add_argument("--cohort", required=True)
    outcome.add_argument("--observations", required=True)
    outcome.set_defaults(func=cmd_outcome)

    score = subparsers.add_parser("score", help="score the frozen picks against the velocity baseline")
    score.add_argument("--cohort", required=True)
    score.add_argument("--json", action="store_true")
    score.set_defaults(func=cmd_score)

    verify = subparsers.add_parser("verify", help="recompute the frozen block's checksum")
    verify.add_argument("--cohort", required=True)
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except JournalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
