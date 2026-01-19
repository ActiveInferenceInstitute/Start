"""Tests for the curriculum generation GUI module.

Uses real imports instead of dynamic module loading to avoid Python 3.13 dataclass issues.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is on path for imports
SCRIPT_DIR = Path(__file__).parent.parent / "learning" / "curriculum_creation"
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


class TestBuildConfigFromForm:
    """Tests for build_config_from_form function."""

    def test_build_config_from_form_mapping(self):
        """Test building config from form data."""
        # Import the module properly to avoid dataclass issues
        from learning.curriculum_creation.generate_curriculum_gui import build_config_from_form

        cfg = build_config_from_form("biochemistry", "karl_friston", "Spanish", None)
        assert cfg.target_domains == ["biochemistry"]
        assert cfg.target_entities == ["karl_friston"]
        assert cfg.target_languages == ["Spanish"]
        assert cfg.skip_existing_research is False
        assert getattr(cfg, "_custom_entity_description", None) is None

    def test_build_config_with_custom_entity_description(self):
        """Test building config with custom entity description."""
        from learning.curriculum_creation.generate_curriculum_gui import build_config_from_form

        cfg = build_config_from_form(
            "neuroscience", "custom_person", "French", "A custom audience"
        )
        assert cfg.target_domains == ["neuroscience"]
        assert cfg.target_entities == ["custom_person"]
        assert cfg.target_languages == ["French"]
        assert getattr(cfg, "_custom_entity_description", None) == "A custom audience"


class TestProgressEstimators:
    """Tests for progress estimation functions."""

    def test_estimate_progress_idle(self):
        """Test progress estimation when idle."""
        from learning.curriculum_creation.generate_curriculum_gui import estimate_progress

        p0 = estimate_progress(-1, False)
        assert p0 == 0.0

    def test_estimate_progress_in_stage(self):
        """Test progress estimation during a stage."""
        from learning.curriculum_creation.generate_curriculum_gui import estimate_progress

        p1 = estimate_progress(0, True)
        assert 0.0 < p1 < 1.0

    def test_estimate_eta_none_for_zero_progress(self):
        """Test ETA returns None for near-zero progress."""
        from learning.curriculum_creation.generate_curriculum_gui import estimate_eta_seconds

        eta_none = estimate_eta_seconds(started_at=0.0, progress=0.0)
        assert eta_none is None

    def test_estimate_eta_with_progress(self):
        """Test ETA calculation with real progress."""
        import time

        from learning.curriculum_creation.generate_curriculum_gui import estimate_eta_seconds

        started = time.time() - 10  # 10 seconds ago
        eta = estimate_eta_seconds(started_at=started, progress=0.5)
        # Should estimate ~10 more seconds (50% done in 10s)
        assert eta is not None
        assert isinstance(eta, int)
        assert eta >= 0
