"""Regression tests for scripts/update_all_registers.py."""

import importlib.util
from datetime import date
from pathlib import Path


def load_update_script():
    """Load update_all_registers.py as a module for direct testing."""
    script_path = Path(__file__).parent.parent / "scripts" / "update_all_registers.py"
    spec = importlib.util.spec_from_file_location("update_all_registers_test_module", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_esma_date_missing_returns_deterministic_exit_code(monkeypatch):
    module = load_update_script()

    monkeypatch.setattr(module, "get_esma_update_date", lambda: None)
    monkeypatch.setattr(module, "ensure_directory_structure", lambda: None)
    monkeypatch.setattr(module, "save_report", lambda *args, **kwargs: None)

    import_calls = {"count": 0}

    def fake_import_to_db(*args, **kwargs):
        import_calls["count"] += 1
        return True, {}

    monkeypatch.setattr(module, "import_to_db", fake_import_to_db)
    monkeypatch.setattr(
        module.sys,
        "argv",
        ["update_all_registers.py", "--registers", "casp", "--dry-run"]
    )

    exit_code = module.main()

    assert exit_code == module.EXIT_ESMA_DATE_UNAVAILABLE
    assert import_calls["count"] == 0


def test_no_use_clean_llm_flag_is_passed_to_db_import(monkeypatch):
    module = load_update_script()

    monkeypatch.setattr(module, "get_esma_update_date", lambda: date(2026, 1, 30))
    monkeypatch.setattr(module, "ensure_directory_structure", lambda: None)
    monkeypatch.setattr(module, "save_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "update_frontend_date", lambda *args, **kwargs: True)

    def fake_update_register(register_type, **kwargs):
        result = module.UpdateResult(register_type=register_type)
        result.success = True
        return result

    monkeypatch.setattr(module, "update_register", fake_update_register)

    import_args = {}

    def fake_import_to_db(drop_db=False, prefer_llm=True, dry_run=False):
        import_args["prefer_llm"] = prefer_llm
        return True, {module.RegisterType.CASP: 1}

    monkeypatch.setattr(module, "import_to_db", fake_import_to_db)
    monkeypatch.setattr(
        module.sys,
        "argv",
        [
            "update_all_registers.py",
            "--registers",
            "casp",
            "--no-use-clean-llm",
            "--report",
            "/tmp/test_update_report.json",
        ],
    )

    exit_code = module.main()

    assert exit_code == module.EXIT_SUCCESS
    assert import_args["prefer_llm"] is False
