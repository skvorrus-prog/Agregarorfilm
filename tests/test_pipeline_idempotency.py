"""Integration tests verifying multi-run idempotency and duplicate elimination."""
import json
import tempfile
from pathlib import Path

from src.collectors.fixture import FixtureSource
from src.config.settings import Settings
from src.pipeline.runner import PipelineRunner
from src.storage.repository import MovieRepository


def test_pipeline_multi_run_idempotency():
    """Verifies that running pipeline multiple times does not duplicate movies or events."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_releases.json"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        settings = Settings(
            base_dir=tmp,
            data_dir=tmp / "data",
            history_dir=tmp / "data" / "history",
            website_dir=tmp / "website",
            website_data_dir=tmp / "website" / "data",
            database_path=tmp / "data" / "releases.db",
            logs_dir=tmp / "logs",
        )

        repo = MovieRepository(settings.database_path)
        source = FixtureSource(fixture_path)
        runner = PipelineRunner(repository=repo, sources=[source], settings=settings)

        # 1. First Run
        res1 = runner.run()
        assert res1["status"] == "SUCCESS"
        assert res1["total_movies"] == 3
        assert res1["new_movies_count"] == 3
        assert res1["new_events_count"] == 3

        # 2. Second Run with identical data
        res2 = runner.run()
        assert res2["status"] == "SUCCESS"
        assert res2["total_movies"] == 3
        assert res2["new_movies_count"] == 0  # No new movies!
        assert res2["new_events_count"] == 0  # No duplicate events!

        # 3. Third Run
        res3 = runner.run()
        assert res3["status"] == "SUCCESS"
        assert res3["total_movies"] == 3
        assert res3["new_movies_count"] == 0
        assert res3["new_events_count"] == 0

        # Check database directly
        all_movies = repo.get_all_movies(load_events=True)
        assert len(all_movies) == 3
        for m in all_movies:
            assert len(m.events) == 1

        # Check generated daily history snapshot
        oct_snap = settings.history_dir / "2024" / "10" / "01.json"
        assert oct_snap.exists()
        with open(oct_snap, "r", encoding="utf-8") as f:
            snap_data = json.load(f)
            assert snap_data["date"] == "2024-10-01"
            assert snap_data["count"] == 1
            assert snap_data["movies"][0]["title"] == "Дэдпул и Росомаха"

        repo.close()
