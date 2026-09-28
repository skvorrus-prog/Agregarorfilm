"""Historical backfill script for digital releases."""
import argparse
from datetime import datetime, timedelta, timezone
import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config.settings import config
from src.collectors.tmdb import TMDBDigitalSource
from src.pipeline.runner import PipelineRunner


def main():
    parser = argparse.ArgumentParser(description="Historical backfill of digital releases")
    parser.add_argument("--from", dest="date_from", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--chunk-days", type=int, default=14, help="Days per fetch chunk")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    d_from = datetime.fromisoformat(args.date_from).date()
    d_to = datetime.fromisoformat(args.date_to).date()

    if d_from > d_to:
        print("Error: --from cannot be after --to")
        sys.exit(1)

    runner = PipelineRunner(sources=[TMDBDigitalSource()])
    cur_start = d_from

    print(f"Starting historical backfill from {d_from} to {d_to}...")

    while cur_start <= d_to:
        cur_end = min(cur_start + timedelta(days=args.chunk_days - 1), d_to)
        print(f"-> Processing window: {cur_start.isoformat()} to {cur_end.isoformat()}")

        res = runner.run(date_from=cur_start.isoformat(), date_to=cur_end.isoformat())
        print(f"   Status: {res['status']}, New Movies: {res['new_movies_count']}, Total: {res['total_movies']}")

        cur_start = cur_end + timedelta(days=1)

    print("Historical backfill completed!")


if __name__ == "__main__":
    main()
