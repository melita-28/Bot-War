"""
Tests for Bot API, JSON Schema validation, and Submission Validator.
"""
import pytest
from bot_api.validator import BotOutputValidator
from bot_api.submission_validator import SubmissionValidator

def test_validator_legal_actions():
    sample_output = {
        "message": "Scouting perimeter",
        "actions": [
            {"unit_id": 1, "action": "move", "dx": 1, "dy": 0},
            {"unit_id": 2, "action": "gather", "deposit_id": 3},
            {"unit_id": 3, "action": "attack", "target_id": 10, "target_type": "unit"},
            {"unit_id": 4, "action": "build", "structure_type": "turret", "target_x": 5, "target_y": 5},
            {"unit_id": 5, "action": "repair", "target_id": 1, "target_type": "unit"},
            {"action": "train", "unit_type": "soldier"}
        ]
    }
    valid_actions, msg, warns = BotOutputValidator.parse_and_validate(sample_output, team="blue")
    assert len(valid_actions) == 6
    assert msg == "Scouting perimeter"
    assert len(warns) == 0

def test_validator_rejects_duplicate_unit_actions():
    sample_output = {
        "actions": [
            {"unit_id": 1, "action": "move", "dx": 1, "dy": 0},
            {"unit_id": 1, "action": "attack", "target_id": 2}
        ]
    }
    valid_actions, msg, warns = BotOutputValidator.parse_and_validate(sample_output, team="blue")
    assert len(valid_actions) == 1
    assert any("multiple actions" in w for w in warns)

def test_validator_handles_malformed_json_safely():
    valid_actions, msg, warns = BotOutputValidator.parse_and_validate("{bad_json:", team="blue")
    assert valid_actions == []
    assert len(warns) > 0

def test_submission_validator_on_starter_bot():
    report = SubmissionValidator.validate_file("bots/starter_bot.py")
    assert report["valid"] is True
    assert report["checks"]["syntax_valid"] is True
    assert report["checks"]["process_start"] is True
    assert report["checks"]["dry_run_response"] is True
    assert report["checks"]["schema_compliance"] is True

def test_submission_validator_on_baseline_bot():
    report = SubmissionValidator.validate_file("bots/baseline_bot.py")
    assert report["valid"] is True
    assert report["checks"]["dry_run_response"] is True

