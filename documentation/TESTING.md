# Testing & Verification Guide - PROXY BOT WARS

PROXY BOT WARS includes a comprehensive automated test suite verifying all game engine subsystems, collision logic, combat damage, fog of war, JSON validators, tournament brackets, and end-to-end battle execution.

---

## 1. Running the Automated Test Suite

Execute pytest across the entire test suite:
```bash
python -m pytest tests/ -v
```

### Test Coverage Summary:
- **`tests/test_engine.py`**:
  - `test_map_generation_and_symmetry`: Verifies rotational symmetry and deposit layouts.
  - `test_unit_creation_and_stats`: Verifies all baseline unit statistics and HP deductions.
  - `test_movement_and_obstacles`: Verifies boundary constraints and speed limits.
  - `test_combat_resolution`: Verifies damage dealt, reciprocal attacks, and statistics tracking.
  - `test_resource_gathering_and_income`: Verifies miner extraction and passive treasury growth.
  - `test_visibility_and_fog_of_war`: Verifies that unrevealed enemies are hidden from observations.
  - `test_scoring_weights`: Verifies that the 5 competition scoring weights sum to 100%.
  - `test_base_destruction_victory`: Verifies immediate game-over upon base HQ destruction.
- **`tests/test_movement.py`**:
  - `test_movement_within_bounds`: Speed adherence and coordinate updating.
  - `test_movement_boundary_enforcement`: Rejection of out-of-bounds attempts.
  - `test_movement_obstacle_collision`: Wall / obstacle collision handling.
  - `test_simultaneous_movement_collision_rebound`: Deterministic collision rebound when two units contest the same tile.
- **`tests/test_combat.py`**:
  - `test_combat_friendly_fire_prevention`: Rejection of attacks against teammates.
  - `test_combat_simultaneous_mutual_elimination`: Resolves simultaneous fatal damage.
  - `test_base_automated_defense`: Automated base defense fire within range 2.
- **`tests/test_visibility.py`**:
  - `test_visibility_range_calculation`: Euclidean circular vision checks.
  - `test_enemy_hidden_outside_vision`: Dynamic reveal of enemies upon entering scout vision.
- **`tests/test_api.py`**:
  - `test_validator_legal_actions`: JSON schema compliance.
  - `test_validator_rejects_duplicate_unit_actions`: Prevention of multiple actions per unit.
  - `test_validator_handles_malformed_json_safely`: Error containment for invalid JSON.
  - `test_submission_validator_on_starter_bot`: AST validation and dry-run check.
  - `test_submission_validator_on_baseline_bot`: AST validation on competitive bot.
- **`tests/test_tournament.py`**:
  - `test_team_registration_and_db`: SQLite persistence.
  - `test_bracket_generation`: Knockout bracket tree generation.
  - `test_tournament_match_execution`: End-to-end tournament battle execution.

---

## 2. End-to-End Verification Check

To test a full match between different bots and verify replay generation:
```bash
python run_match.py --blue bots/starter_bot.py --red bots/baseline_bot.py --turns 50 --output-replay replays/verification.json
```
Verify the replay is readable:
```bash
python -c "import json; r = json.load(open('replays/verification.json')); print('Frames recorded:', len(r['history']), '| Winner:', r['metadata']['winner'])"
```

