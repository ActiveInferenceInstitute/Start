from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.parent / "learning" / "curriculum_creation"
GUI_PATH = SCRIPT_DIR / "generate_curriculum_gui.py"


def _import_gui():
    spec = importlib.util.spec_from_file_location("generate_curriculum_gui", GUI_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_build_config_from_form_mapping():
    gui = _import_gui()
    cfg = gui.build_config_from_form("biochemistry", "karl_friston", "Spanish", None)
    assert cfg.target_domains == ["biochemistry"]
    assert cfg.target_entities == ["karl_friston"]
    assert cfg.target_languages == ["Spanish"]
    assert cfg.skip_existing_research is False
    assert getattr(cfg, "_custom_entity_description", None) is None


def test_build_config_with_custom_entity_description():
    gui = _import_gui()
    cfg = gui.build_config_from_form("neuroscience", "custom_person", "French", "A custom audience")
    assert cfg.target_domains == ["neuroscience"]
    assert cfg.target_entities == ["custom_person"]
    assert cfg.target_languages == ["French"]
    assert getattr(cfg, "_custom_entity_description", None) == "A custom audience"


def test_progress_and_eta_estimators():
    gui = _import_gui()
    p0 = gui.estimate_progress(-1, False)
    assert p0 == 0.0
    p1 = gui.estimate_progress(0, True)
    assert 0.0 < p1 < 1.0
    # ETA should be None for near-zero progress
    eta_none = gui.estimate_eta_seconds(started_at=0.0, progress=0.0)
    assert eta_none is None


