from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6 import QtCore, QtGui

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
        self.start_tasks = []
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


class _ErrorDialogFake:
    calls = []

    def __init__(self, *_args) -> None:
        _ErrorDialogFake.calls.append(self)

    def exec(self) -> int:
        return 0


class _GeneralControllerFake:
    def __init__(self, cases_folder_path: str) -> None:
        self.configuration = {"cases_folder_path": cases_folder_path}


class _WizardFake:
    def __init__(self, case_name: str = "Case 1") -> None:
        self.case_info = {"name": case_name}
        self.reload_case_info_calls = 0
        self.show_calls = 0

    def reload_case_info(self) -> None:
        self.reload_case_info_calls += 1

    def show(self) -> None:
        self.show_calls += 1


class _SpinnerFake:
    def __init__(self, running: bool = False) -> None:
        self.running = running
        self.start_calls = 0
        self.stop_calls = 0

    def start(self) -> None:
        self.running = True
        self.start_calls += 1

    def stop(self) -> None:
        self.running = False
        self.stop_calls += 1

    def state(self) -> QtGui.QMovie.MovieState:
        return (
            QtGui.QMovie.MovieState.Running
            if self.running
            else QtGui.QMovie.MovieState.NotRunning
        )


class _TasksInfoFake:
    def __init__(self) -> None:
        self.show_calls = 0
        self.close_calls = 0
        self.geometry = None

    def show(self) -> None:
        self.show_calls += 1

    def close(self) -> None:
        self.close_calls += 1

    def setGeometry(self, geometry) -> None:
        self.geometry = geometry


@pytest.fixture
def scraper_with_fakes(
    qapp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[scraper_module.Scraper, _WizardFake]:
    translations = {
        "NO_CASE_SELECTED_TITLE": "No case selected",
        "NO_CASE_SELECTED_MESSAGE": "No case",
        "CREATE_DIRECTORY_ERROR_TITLE": "Create directory error",
        "CREATE_ACQUISITION_DIRECTORY_ERROR_MESSAGE": "Create acquisition dir error",
        "CREATE_ACQUISITION_SUBDIRECTORY_ERROR_MESSAGE": "Create subdir error {}",
        "ACQUISITION_DIRECTORY_DOES_NOT_EXIST": "Missing acquisition directory",
        "ACQUISITION_IS_RUNNING": "Acquisition running",
        "WAR_ACQUISITION_IS_RUNNING": "Cannot close while running",
    }
    monkeypatch.setattr(
        scraper_module, "load_scraper_translations", lambda: translations
    )
    monkeypatch.setattr(scraper_module, "Acquisition", _AcquisitionFake)
    monkeypatch.setattr(scraper_module.os, "chmod", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(scraper_module, "Error", _ErrorDialogFake)
    _ErrorDialogFake.calls.clear()

    cases_root = tmp_path / "cases"
    monkeypatch.setattr(
        scraper_module,
        "GeneralController",
        lambda: _GeneralControllerFake(str(cases_root)),
    )

    wizard = _WizardFake()
    scraper = scraper_module.Scraper(
        logger=SimpleNamespace(), acquisition_type="web", packages=[], wizard=wizard
    )
    return scraper, wizard


@pytest.mark.unit
def test_create_acquisition_directory_increments_index(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes

    assert scraper.create_acquisition_directory() is True
    first_path = Path(scraper.acquisition_directory)
    assert first_path.name == "acquisition_1"
    assert first_path.is_dir()

    assert scraper.create_acquisition_directory() is True
    second_path = Path(scraper.acquisition_directory)
    assert second_path.name == "acquisition_2"
    assert second_path.is_dir()


@pytest.mark.unit
def test_create_acquisition_directory_ignores_non_matching_names(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes

    assert scraper.create_acquisition_directory() is True
    root = Path(scraper.acquisition_directory).parent
    (root / "acquisition_custom").mkdir(exist_ok=True)
    (root / "notes").mkdir(exist_ok=True)
    (root / "acquisition_7").mkdir(exist_ok=True)

    assert scraper.create_acquisition_directory() is True
    assert Path(scraper.acquisition_directory).name == "acquisition_8"


@pytest.mark.unit
def test_create_acquisition_directory_failure_shows_error(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scraper, _wizard = scraper_with_fakes

    real_makedirs = os.makedirs
    state = {"n": 0}

    def failing_once(*args, **kwargs):
        state["n"] += 1
        if state["n"] == 1:
            raise OSError("simulated failure")
        return real_makedirs(*args, **kwargs)

    monkeypatch.setattr(scraper_module.os, "makedirs", failing_once)

    assert scraper.create_acquisition_directory() is False
    assert scraper.acquisition_directory is None
    assert len(_ErrorDialogFake.calls) == 1


@pytest.mark.unit
def test_create_acquisition_subdirectory_requires_base_directory(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes

    assert scraper.create_acquisition_subdirectory("screenshot") is False
    assert len(_ErrorDialogFake.calls) == 1


@pytest.mark.unit
def test_create_acquisition_subdirectory_success_path(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes
    assert scraper.create_acquisition_directory() is True

    assert scraper.create_acquisition_subdirectory("screenshot") is True
    subdir = Path(scraper.acquisition_directory) / "screenshot"
    assert subdir.is_dir()


@pytest.mark.unit
def test_can_close_depends_on_acquisition_status(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes

    scraper.acquisition_status = scraper_module.AcquisitionStatus.UNSTARTED
    assert scraper.can_close() is True

    scraper.acquisition_status = scraper_module.AcquisitionStatus.STARTED
    assert scraper.can_close() is False
    assert len(_ErrorDialogFake.calls) == 1


@pytest.mark.unit
def test_close_event_with_wizard_routes_back_to_wizard(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, wizard = scraper_with_fakes
    scraper.acquisition_status = scraper_module.AcquisitionStatus.UNSTARTED

    event = SimpleNamespace(accepted=False, ignored=False)
    event.accept = lambda: setattr(event, "accepted", True)
    event.ignore = lambda: setattr(event, "ignored", True)

    scraper.closeEvent(event)

    assert event.ignored is True
    assert event.accepted is False
    assert wizard.reload_case_info_calls == 1
    assert wizard.show_calls == 1


@pytest.mark.unit
def test_close_event_without_wizard_accepts_when_not_running(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes
    scraper._Scraper__wizard = None
    scraper.acquisition_status = scraper_module.AcquisitionStatus.FINISHED

    event = SimpleNamespace(accepted=False, ignored=False)
    event.accept = lambda: setattr(event, "accepted", True)
    event.ignore = lambda: setattr(event, "ignored", True)

    scraper.closeEvent(event)
    assert event.accepted is True
    assert event.ignored is False


@pytest.mark.unit
def test_close_event_without_wizard_ignores_when_running(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes
    scraper._Scraper__wizard = None
    scraper.acquisition_status = scraper_module.AcquisitionStatus.STARTED

    event = SimpleNamespace(accepted=False, ignored=False)
    event.accept = lambda: setattr(event, "accepted", True)
    event.ignore = lambda: setattr(event, "ignored", True)

    scraper.closeEvent(event)
    assert event.accepted is False
    assert event.ignored is True
    assert len(_ErrorDialogFake.calls) == 1


@pytest.mark.unit
def test_execute_start_tasks_flow_updates_status_and_calls_acquisition(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scraper, _wizard = scraper_with_fakes
    spinner = _SpinnerFake()
    monkeypatch.setattr(
        scraper_module.Scraper,
        "_Scraper__init_execution_overlay",
        lambda self: setattr(self, "_Scraper__spinner", spinner),
    )
    monkeypatch.setattr(scraper_module.QtCore.QEventLoop, "exec", lambda self: 0)
    monkeypatch.setattr(
        scraper_module.QtCore.QTimer, "singleShot", lambda _ms, fn: fn()
    )

    scraper.execute_start_tasks_flow()

    assert scraper.acquisition_status == scraper_module.AcquisitionStatus.STARTED
    assert spinner.start_calls == 1
    assert scraper.acquisition.calls == [
        "load_tasks",
        "log_start_message",
        "write_fit_system_environment_variables",
        "run_start_tasks",
    ]
    assert scraper.acquisition.progress_bar_visible is True
    assert scraper.acquisition.status_bar_visible is True


@pytest.mark.unit
def test_execute_stop_tasks_flow_stops_spinner_and_runs_stop_tasks(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scraper, _wizard = scraper_with_fakes
    spinner = _SpinnerFake(running=True)
    tasks_info = _TasksInfoFake()
    scraper._Scraper__spinner = spinner
    scraper._Scraper__tasks_info = tasks_info
    scraper.acquisition.start_tasks = ["task"]
    monkeypatch.setattr(scraper_module.QtCore.QEventLoop, "exec", lambda self: 0)
    monkeypatch.setattr(
        scraper_module.QtCore.QTimer, "singleShot", lambda _ms, fn: fn()
    )

    scraper.execute_stop_tasks_flow()

    assert scraper.acquisition_status == scraper_module.AcquisitionStatus.STOPPED
    assert spinner.stop_calls == 1
    assert tasks_info.show_calls == 1
    assert scraper.acquisition.calls[-2:] == ["log_stop_message", "run_stop_tasks"]


@pytest.mark.unit
def test_on_post_acquisition_finished_completes_and_finishes(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scraper, _wizard = scraper_with_fakes
    tasks_info = _TasksInfoFake()
    scraper._Scraper__tasks_info = tasks_info
    finished = {"called": 0}
    monkeypatch.setattr(scraper, "finish_acquisition", lambda: finished.__setitem__("called", 1))
    monkeypatch.setattr(
        scraper_module.QtCore.QTimer, "singleShot", lambda _ms, fn: fn()
    )

    scraper.on_post_acquisition_finished()

    assert scraper.acquisition_status == scraper_module.AcquisitionStatus.FINISHED
    assert tasks_info.close_calls == 1
    assert "log_end_message" in scraper.acquisition.calls
    assert "unload_tasks" in scraper.acquisition.calls
    assert finished["called"] == 1
    assert scraper.acquisition.progress_bar_visible is False
    assert scraper.acquisition.status_bar_visible is False


@pytest.mark.unit
def test_wrapper_dialog_methods_delegate(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scraper, _wizard = scraper_with_fakes
    record = {"finish": None, "config": 0, "case_info": None}
    scraper._Scraper__acquisition_directory = "/tmp/case/acquisition_1"

    monkeypatch.setattr(
        scraper_module,
        "show_finish_acquisition_dialog",
        lambda path: record.__setitem__("finish", path),
    )
    monkeypatch.setattr(
        scraper_module,
        "show_configuration_dialog",
        lambda: record.__setitem__("config", record["config"] + 1),
    )
    monkeypatch.setattr(
        scraper_module,
        "show_case_info_dialog",
        lambda case_info: record.__setitem__("case_info", case_info),
    )

    scraper.finish_acquisition()
    scraper.configuration_dialog()
    scraper.show_case_info()

    assert record["finish"] == "/tmp/case/acquisition_1"
    assert record["config"] == 1
    assert record["case_info"] == {"name": "Case 1"}


@pytest.mark.unit
def test_window_drag_helpers_update_position(
    scraper_with_fakes: tuple[scraper_module.Scraper, _WizardFake],
) -> None:
    scraper, _wizard = scraper_with_fakes
    position = QtCore.QPoint(100, 100)
    moved_to = {"value": None}

    scraper.pos = lambda: position
    scraper.move = lambda p: moved_to.__setitem__("value", p)

    start_event = SimpleNamespace(globalPosition=lambda: QtCore.QPointF(10, 10))
    scraper.mousePressEvent(start_event)

    drag_event = SimpleNamespace(
        buttons=lambda: QtCore.Qt.MouseButton.LeftButton,
        globalPosition=lambda: QtCore.QPointF(20, 30),
        accepted=False,
        accept=lambda: setattr(drag_event, "accepted", True),
    )
    scraper.move_window(drag_event)

    assert moved_to["value"] == QtCore.QPoint(110, 120)
    assert drag_event.accepted is True
