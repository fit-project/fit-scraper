from __future__ import annotations

import pytest

from fit_scraper import lang as lang_module


@pytest.mark.unit
def test_load_translations_uses_selected_language() -> None:
    translations = lang_module.load_translations("it")
    assert translations["NO_CASE_SELECTED_TITLE"] == "Nessun caso selezionato"


@pytest.mark.unit
def test_load_translations_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lang_module, "DEFAULT_LANG", "en")
    translations = lang_module.load_translations("zz")
    assert translations["NO_CASE_SELECTED_TITLE"] == "No case selected"


@pytest.mark.unit
def test_load_translations_uses_system_language_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lang_module, "get_system_lang", lambda: "en")
    translations = lang_module.load_translations()
    assert translations["ACQUISITION_IS_RUNNING"] == "Acquisition is in progress"
