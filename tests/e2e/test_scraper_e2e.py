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


class _AcquisitionFake:
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
    def reset_progress_bar(self):
        return None

    @property
    def reset_status_bar(self):
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


class _SpinnerFake:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.running = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def state(self):
        return (
            scraper_module.QtGui.QMovie.MovieState.Running
            if self.running
            else scraper_module.QtGui.QMovie.MovieState.NotRunning
        )


class _GeneralControllerFake:
    def __init__(self, cases_folder_path: str) -> None:
        self.configuration = {"cases_folder_path": cases_folder_path}


class _WizardFake:
    def __init__(self, case_name: str = "E2E Case") -> None:
        self.case_info = {"name": case_name}


@pytest.mark.e2e
def test_scraper_happy_path_e2e(
    qapp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(scraper_module, "Acquisition", _AcquisitionFake)
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

    finished = {"dialog_calls": 0}
    monkeypatch.setattr(
        scraper_module,
        "show_finish_acquisition_dialog",
        lambda _path: finished.__setitem__("dialog_calls", 1),
    )

    scraper = scraper_module.Scraper(
        logger=SimpleNamespace(),
        acquisition_type="web",
        packages=[],
        wizard=_WizardFake(),
    )

    assert scraper.create_acquisition_directory() is True
    assert scraper.create_acquisition_subdirectory("screenshot") is True
    scraper._Scraper__init_execution_overlay()

    scraper.execute_start_tasks_flow()
    scraper.on_start_tasks_finished()
    scraper.execute_stop_tasks_flow()
    scraper.on_stop_tasks_finished()
    scraper.on_post_acquisition_finished()

    assert scraper.acquisition_status == scraper_module.AcquisitionStatus.FINISHED
    assert Path(scraper.acquisition_directory).is_dir()
    assert finished["dialog_calls"] == 1
    assert scraper.acquisition.calls == [
        "load_tasks",
        "log_start_message",
        "write_fit_system_environment_variables",
        "run_start_tasks",
        "set_completed_progress_bar",
        "log_stop_message",
        "run_stop_tasks",
        "set_completed_progress_bar",
        "start_post_acquisition",
        "set_completed_progress_bar",
        "log_end_message",
        "set_completed_progress_bar",
        "unload_tasks",
    ]
