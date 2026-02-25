from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from PySide6.QtCore import SignalInstance

from fit_acquisition.acquisition import Acquisition

from fit_scraper.scraper import Scraper


@pytest.mark.contract
def test_scraper_declares_required_public_api() -> None:
    assert callable(getattr(Scraper, "create_acquisition_directory", None))
    assert callable(getattr(Scraper, "create_acquisition_subdirectory", None))
    assert callable(getattr(Scraper, "execute_start_tasks_flow", None))
    assert callable(getattr(Scraper, "execute_stop_tasks_flow", None))
    assert callable(getattr(Scraper, "on_post_acquisition_finished", None))


@pytest.mark.contract
def test_acquisition_exposes_interface_required_by_scraper() -> None:
    init_signature = inspect.signature(Acquisition.__init__)
    assert "logger" in init_signature.parameters
    assert "packages" in init_signature.parameters

    acquisition = Acquisition(logger=None, packages=[])

    assert isinstance(acquisition.start_tasks_finished, SignalInstance)
    assert isinstance(acquisition.stop_tasks_finished, SignalInstance)
    assert isinstance(acquisition.post_acquisition_finished, SignalInstance)

    for method_name in [
        "load_tasks",
        "run_start_tasks",
        "run_stop_tasks",
        "start_post_acquisition",
        "set_completed_progress_bar",
        "log_start_message",
        "log_stop_message",
        "log_end_message",
        "unload_tasks",
        "write_fit_system_environment_variables",
    ]:
        assert callable(getattr(acquisition, method_name, None)), method_name


@pytest.mark.contract
def test_language_files_define_keys_used_by_scraper() -> None:
    lang_dir = Path(__file__).resolve().parents[2] / "fit_scraper" / "lang"
    en_path = lang_dir / "en.json"
    it_path = lang_dir / "it.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    it = json.loads(it_path.read_text(encoding="utf-8"))

    required_keys = {
        "NO_CASE_SELECTED_TITLE",
        "NO_CASE_SELECTED_MESSAGE",
        "CREATE_DIRECTORY_ERROR_TITLE",
        "CREATE_ACQUISITION_DIRECTORY_ERROR_MESSAGE",
        "CREATE_ACQUISITION_SUBDIRECTORY_ERROR_MESSAGE",
        "ACQUISITION_DIRECTORY_DOES_NOT_EXIST",
        "ACQUISITION_IS_RUNNING",
        "WAR_ACQUISITION_IS_RUNNING",
    }
    assert required_keys.issubset(set(en.keys()))
    assert required_keys.issubset(set(it.keys()))
