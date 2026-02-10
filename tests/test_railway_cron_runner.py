"""Tests for scripts/run_railway_cron_update.py."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def load_cron_runner():
    """Load cron runner script as importable module."""
    script_path = Path(__file__).parent.parent / "scripts" / "run_railway_cron_update.py"
    spec = importlib.util.spec_from_file_location("railway_cron_runner_test_module", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_update_returns_zero_on_success(monkeypatch, tmp_path):
    module = load_cron_runner()
    report_path = tmp_path / "update_report.json"

    def fake_run(cmd, cwd, check):
        assert "scripts/update_all_registers.py" in cmd
        assert cwd == str(module.PROJECT_ROOT)
        assert check is False

        report_data = {
            "summary": {
                "successful": 1,
                "skipped": 4,
                "failed": 0,
                "total_entities": 999,
            },
            "results": [
                {"register_type": "casp", "success": True, "entities_imported": 150},
            ],
        }
        Path(cmd[-1]).write_text(json.dumps(report_data), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    exit_code = module.run_update(report_path=report_path)
    assert exit_code == 0


def test_run_update_returns_non_zero_on_pipeline_failure(monkeypatch, tmp_path):
    module = load_cron_runner()
    report_path = tmp_path / "update_report.json"

    def fake_run(cmd, cwd, check):
        return SimpleNamespace(returncode=2)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    exit_code = module.run_update(report_path=report_path)
    assert exit_code == 2
