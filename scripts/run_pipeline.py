"""CLI script to run data collector pipeline and update repository and static site."""
import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config.settings import config
from src.collectors.base import BaseSource
from src.collectors.tmdb import TMDBDigitalSource
from src.collectors.cinemeta import CinemetaSource
from src.collectors.release_rss import ReleaseRSSSource
from src.collectors.fixture import FixtureSource
from src.storage.repository import MovieRepository
from src.pipeline.runner import PipelineRunner


def setup_logging(log_level: str = "INFO") -> None:
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = config.logs_dir / "pipeline.log"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def write_github_summary(results: dict) -> None:
    """Writes Markdown summary to $GITHUB_STEP_SUMMARY if running inside GitHub Actions."""
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    md_lines = [
        "## 🎬 Digital Releases Pipeline Summary",
        f"- **Status**: `{results['status']}`",
        f"- **Duration**: `{results['duration_seconds']}s`",
        f"- **Total Movies in DB**: `{results['total_movies']}`",
        f"- **New Movies Added**: `{results['new_movies_count']}`",
        f"- **New Events Added**: `{results['new_events_count']}`",
        f"- **Telegram Notifications Sent**: `{results['notified_count']}`",
        "",
        "### Source Execution Details",
        "| Source | Status | Items Fetched | Error |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for src_name, info in results.get("sources", {}).items():
        err = info.get("error") or "None"
        md_lines.append(f"| **{src_name}** | `{info['status']}` | {info['count']} | {err} |")

    stats = results.get("stats", {})
    md_lines.extend([
        "",
        "### Quality Distribution",
        f"- 4K (2160p): **{stats.get('four_k_count', 0)}**",
        f"- HDR: **{stats.get('hdr_count', 0)}**",
        f"- RU Audio: **{stats.get('ru_audio_count', 0)}**",
        f"- Average Rating: **{stats.get('avg_rating', '—')}**",
    ])

    try:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write to GITHUB_STEP_SUMMARY: {e}")


def main():
    parser = argparse.ArgumentParser(description="Digital Movie Releases Collector Pipeline")
    parser.add_argument("--from", dest="date_from", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--sources",
        type=str,
        default="all",
        help="Comma-separated sources: tmdb,cinemeta,rss,fixture",
    )
    parser.add_argument("--fixture", type=str, help="Path to fixture JSON file if using fixture source")
    parser.add_argument("--log-level", type=str, default=config.log_level, help="Log level (DEBUG, INFO, etc.)")

    args = parser.parse_args()
    setup_logging(args.log_level)

    # Initialize sources
    selected = [s.strip().lower() for s in args.sources.split(",")]
    sources = []

    if "all" in selected or "tmdb" in selected:
        sources.append(TMDBDigitalSource())
    if "all" in selected or "cinemeta" in selected:
        sources.append(CinemetaSource())
    if "all" in selected or "rss" in selected:
        sources.append(ReleaseRSSSource())
    if "fixture" in selected and args.fixture:
        sources.append(FixtureSource(Path(args.fixture)))

    runner = PipelineRunner(sources=sources)
    result = runner.run(date_from=args.date_from, date_to=args.date_to)

    write_github_summary(result)

    print("\n--- Pipeline Execution Summary ---")
    print(f"Status: {result['status']}")
    print(f"Total Movies: {result['total_movies']} (+{result['new_movies_count']} new)")
    print(f"New Events: {result['new_events_count']}")
    print("Sources:")
    for src, info in result["sources"].items():
        print(f"  - {src}: {info['status']} ({info['count']} items) {info.get('error') or ''}")

    if result["status"] == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()
