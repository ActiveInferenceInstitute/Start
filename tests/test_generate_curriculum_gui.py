"""Tests for the curriculum generation GUI module.

Uses real imports instead of dynamic module loading to avoid Python 3.13 dataclass issues.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
        assert cfg.custom_entity_description is None

    def test_build_config_with_custom_entity_description(self):
        """Test building config with custom entity description."""
        from learning.curriculum_creation.generate_curriculum_gui import build_config_from_form

        cfg = build_config_from_form("neuroscience", "custom_person", "French", "A custom audience")
        assert cfg.target_domains == ["neuroscience"]
        assert cfg.target_entities == ["custom_person"]
        assert cfg.target_languages == ["French"]
        assert cfg.custom_entity_description == "A custom audience"

    def test_form_parser_preserves_custom_values_and_rejects_non_strings(self):
        from learning.curriculum_creation.generate_curriculum_gui import _parse_start_payload

        parsed = _parse_start_payload(
            {
                "domain": "Custom domain",
                "entity": "Custom audience",
                "language": "Esperanto",
                "entity_description": "A real description",
            }
        )
        assert parsed == (
            "Custom domain",
            "Custom audience",
            "Esperanto",
            "A real description",
        )

        try:
            _parse_start_payload({"domain": [], "entity": "reader", "language": "Spanish"})
        except ValueError as exc:
            assert "domain must be a string" in str(exc)
        else:
            raise AssertionError("non-string GUI input was accepted")

    def test_remote_binding_requires_explicit_authentication(self):
        from learning.curriculum_creation.generate_curriculum_gui import run_gui_server

        try:
            run_gui_server("0.0.0.0", 0, open_browser=False)
        except ValueError as exc:
            assert "allow-remote" in str(exc)
        else:
            raise AssertionError("remote GUI binding was accepted without opt-in")

        try:
            run_gui_server("0.0.0.0", 0, open_browser=False, allow_remote=True)
        except ValueError as exc:
            assert "authentication token" in str(exc)
        else:
            raise AssertionError("remote GUI binding was accepted without authentication")

    def test_public_errors_and_html_summary_are_redacted(self):
        from learning.curriculum_creation.generate_curriculum_gui import (
            _results_to_summary_html,
            _safe_public_error,
        )

        safe = _safe_public_error(
            "Bearer sk-secret-value at /Users/private/project/output with prompt details"
        )
        assert "sk-secret-value" not in safe
        assert "/Users/private" not in safe
        html = _results_to_summary_html(
            {"research": {"success": 0, "failed": 1, "skipped": 0, "errors": [safe]}}
        )
        assert "Run Summary" in html
        assert "sk-secret-value" not in html


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
