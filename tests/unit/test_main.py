from __future__ import annotations

from types import SimpleNamespace

import pytest

import main as main_module


@pytest.mark.unit
def test_testscraper_sets_task_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_scraper_init(self, logger, acquisition_type, packages, wizard=None):
        self._Scraper__acquisition = SimpleNamespace(start_tasks=[], stop_tasks=[])

    monkeypatch.setattr(main_module.Scraper, "__init__", fake_scraper_init)
    monkeypatch.setattr(
        main_module.TestScraper,
        "_TestScraper__init_execution_overlay",
        lambda self: None,
    )

    instance = main_module.TestScraper()

    assert instance.acquisition.start_tasks == [
        main_module.class_names.SCREENRECORDER,
        main_module.class_names.PACKETCAPTURE,
    ]
    assert instance.acquisition.stop_tasks == [
        main_module.class_names.WHOIS,
        main_module.class_names.NSLOOKUP,
        main_module.class_names.HEADERS,
        main_module.class_names.SSLKEYLOG,
        main_module.class_names.SSLCERTIFICATE,
        main_module.class_names.TRACEROUTE,
        main_module.class_names.SCREENRECORDER,
        main_module.class_names.PACKETCAPTURE,
    ]


@pytest.mark.unit
def test_main_exits_with_app_code_when_case_is_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _AppFake:
        def exec(self) -> int:
            return 42

    class _WindowFake:
        has_valid_case = True

        def __init__(self) -> None:
            self.show_calls = 0

        def show(self) -> None:
            self.show_calls += 1

    window = _WindowFake()
    monkeypatch.setattr(main_module, "QApplication", lambda _argv: _AppFake())
    monkeypatch.setattr(main_module, "TestScraper", lambda: window)

    captured = {"code": None}

    def fake_exit(code: int) -> None:
        captured["code"] = code
        raise SystemExit(code)

    monkeypatch.setattr(main_module.sys, "exit", fake_exit)

    with pytest.raises(SystemExit):
        main_module.main()

    assert window.show_calls == 1
    assert captured["code"] == 42


@pytest.mark.unit
def test_main_exits_zero_when_case_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _AppFake:
        def exec(self) -> int:
            return 42

    class _WindowFake:
        has_valid_case = False

        def show(self) -> None:
            raise AssertionError("show() should not be called when no case is valid")

    messages: list[str] = []
    monkeypatch.setattr(main_module, "QApplication", lambda _argv: _AppFake())
    monkeypatch.setattr(main_module, "TestScraper", lambda: _WindowFake())
    monkeypatch.setattr(main_module, "debug", lambda msg, context=None: messages.append(msg))

    captured = {"code": None}

    def fake_exit(code: int) -> None:
        captured["code"] = code
        raise SystemExit(code)

    monkeypatch.setattr(main_module.sys, "exit", fake_exit)

    with pytest.raises(SystemExit):
        main_module.main()

    assert captured["code"] == 0
    assert any("User cancelled the case form" in m for m in messages)
