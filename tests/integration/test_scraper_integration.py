from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from fit_scraper import scraper as scraper_module


class _Signal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)


class _AcquisitionIntegrationFake:
    def __init__(self, logger, packages) -> None:
        self.logger = logger
        self.packages = packages
        self.start_tasks_finished = _Signal()
        self.stop_tasks_finished = _Signal()
        self.post_acquisition_finished = _Signal()
        self.start_tasks = ["SCREENRECORDER"]
        self.stop_tasks = ["WHOIS"]
        self.progress_bar_visible = False
        self.status_bar_visible = False
        self.calls: list[str] = []

    @property
    def reset_progress_bar(self) -> None:
        return None

    @property
    def reset_status_bar(self) -> None:
        return None

    def load_tasks(self) -> None:
        self.calls.append("load_tasks")

    def log_start_message(self) -> None:
        self.calls.append("log_start_message")

    def write_fit_system_environment_variables(self) -> None:
        self.calls.append("write_fit_system_environment_variables")

    def run_start_tasks(self) -> None:
        self.calls.append("run_start_tasks")

    def set_completed_progress_bar(self) -> None:
        self.calls.append("set_completed_progress_bar")

    def log_stop_message(self) -> None:
        self.calls.append("log_stop_message")

    def run_stop_tasks(self) -> None:
        self.calls.append("run_stop_tasks")

    def start_post_acquisition(self) -> None:
        self.calls.append("start_post_acquisition")

    def log_end_message(self) -> None:
        self.calls.append("log_end_message")

    def unload_tasks(self) -> None:
        self.calls.append("unload_tasks")


class _GeneralControllerFake:
    def __init__(self, cases_folder_path: str) -> None:
        self.configuration = {"cases_folder_path": cases_folder_path}


class _WizardFake:
    def __init__(self, case_name: str = "Integration Case") -> None:
        self.case_info = {"name": case_name}


class _SpinnerFake:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def state(self):
        return (
            scraper_module.QtGui.QMovie.MovieState.Running
            if self._running
            else scraper_module.QtGui.QMovie.MovieState.NotRunning
        )


@pytest.fixture
def integration_scraper(
    qapp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> scraper_module.Scraper:
    monkeypatch.setattr(scraper_module, "Acquisition", _AcquisitionIntegrationFake)
    monkeypatch.setattr(scraper_module, "Spinner", _SpinnerFake)
    monkeypatch.setattr(scraper_module.os, "chmod", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        scraper_module,
        "GeneralController",
        lambda: _GeneralControllerFake(str(tmp_path / "cases")),
    )
    monkeypatch.setattr(scraper_module.QtCore.QEventLoop, "exec", lambda self: 0)
    monkeypatch.setattr(
        scraper_module.QtCore.QTimer, "singleShot", lambda _ms, fn: fn()
    )
    monkeypatch.setattr(
        scraper_module, "show_finish_acquisition_dialog", lambda _path: None
    )

    return scraper_module.Scraper(
        logger=SimpleNamespace(),
        acquisition_type="web",
        packages=[],
        wizard=_WizardFake(),
    )


@pytest.mark.integration
def test_scraper_overlay_initialization_smoke(
    integration_scraper: scraper_module.Scraper,
) -> None:
    integration_scraper._Scraper__init_execution_overlay()
    assert integration_scraper.tasks_info is not None
    assert integration_scraper.tasks_info.parent() is integration_scraper


@pytest.mark.integration
def test_scraper_flow_start_stop_post_smoke(
    integration_scraper: scraper_module.Scraper,
) -> None:
    assert integration_scraper.create_acquisition_directory() is True
    assert integration_scraper.create_acquisition_subdirectory("screenshot") is True

    integration_scraper._Scraper__init_execution_overlay()
    integration_scraper.execute_start_tasks_flow()
    integration_scraper.on_start_tasks_finished()
    integration_scraper.execute_stop_tasks_flow()
    integration_scraper.on_stop_tasks_finished()
    integration_scraper.on_post_acquisition_finished()

    calls = integration_scraper.acquisition.calls
    assert "load_tasks" in calls
    assert "run_start_tasks" in calls
    assert "run_stop_tasks" in calls
    assert "start_post_acquisition" in calls
    assert "log_end_message" in calls
    assert "unload_tasks" in calls
    assert integration_scraper.acquisition_directory is not None
