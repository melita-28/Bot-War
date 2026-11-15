"""
Unit tests for the core game engine subsystems.
"""
import pytest
from game_engine.config import UNIT_SPECS, BASE_MAX_HP
from game_engine.map import MapGenerator, GameMap
from game_engine.game_state import GameState
from game_engine.engine import GameEngine
from game_engine.units import Unit, Structure
from game_engine.visibility import VisibilitySystem
from game_engine.scoring import ScoringSystem
from game_engine.victory import VictorySystem

def test_map_generation_and_symmetry():
    gmap = MapGenerator.generate(30, 30, seed=42)
    assert gmap.width == 30
    assert gmap.height == 30
    assert "blue" in gmap.base_positions
    assert "red" in gmap.base_positions
    # Symmetrical checks
    bx, by = gmap.base_positions["blue"]
    rx, ry = gmap.base_positions["red"]
    assert rx == 30 - 1 - bx
    assert ry == 30 - 1 - by
    assert len(gmap.control_zones) >= 3
    assert len(gmap.resource_deposits) >= 6

def test_unit_creation_and_stats():
    u = Unit.create(unit_id=1, unit_type="tank", team="blue", x=5, y=5)
    assert u.hp == 250
    assert u.attack == 40
    assert u.speed == 1
    assert u.vision == 4
    assert u.attack_range == 3
    assert u.alive is True

    # Test take damage
    dmg = u.take_damage(50)
    assert dmg == 50
    assert u.hp == 200
    assert u.alive is True

    # Test elimination
    u.take_damage(250)
    assert u.hp == 0
    assert u.alive is False

def test_movement_and_obstacles():
    engine = GameEngine()
    state = engine.state
    # Pick a friendly unit
    scout = [u for u in state.units.values() if u.team == "blue" and u.unit_type == "scout"][0]
    initial_x, initial_y = scout.x, scout.y

    # Test legal move
    output_blue = {
        "actions": [
            {"unit_id": scout.id, "action": "move", "dx": 1, "dy": 0}
        ]
    }
    step_res = engine.step(blue_output=output_blue, red_output={"actions": []})
    assert scout.x == initial_x + 1
    assert scout.y == initial_y

    # Test illegal move exceeding speed
    excess_move = {
        "actions": [
            {"unit_id": scout.id, "action": "move", "dx": 10, "dy": 0}
        ]
    }
    prev_x = scout.x
    engine.step(blue_output=excess_move, red_output={"actions": []})
    assert scout.x == prev_x # Stays in place

def test_combat_resolution():
    engine = GameEngine()
    state = engine.state

    # Place a blue soldier and a red soldier adjacent to each other
    blue_soldier = Unit.create(unit_id=101, unit_type="soldier", team="blue", x=10, y=10)
    red_soldier = Unit.create(unit_id=102, unit_type="soldier", team="red", x=11, y=10)
    state.units[101] = blue_soldier
    state.units[102] = red_soldier

    # Blue attacks red
    blue_act = {"actions": [{"unit_id": 101, "action": "attack", "target_id": 102, "target_type": "unit"}]}
    red_act = {"actions": [{"unit_id": 102, "action": "attack", "target_id": 101, "target_type": "unit"}]}

    engine.step(blue_output=blue_act, red_output=red_act)

    assert red_soldier.hp == 100 - blue_soldier.attack # 100 - 20 = 80
    assert blue_soldier.hp == 100 - red_soldier.attack # 100 - 20 = 80
    assert state.stats["blue"]["damage_dealt"] == 20
    assert state.stats["red"]["damage_dealt"] == 20

def test_resource_gathering_and_income():
    engine = GameEngine()
    state = engine.state
    # Find a deposit
    dep = list(state.game_map.resource_deposits.values())[0]
    # Place miner next to it
    miner = Unit.create(unit_id=201, unit_type="miner", team="blue", x=dep.x + 1, y=dep.y)
    state.units[201] = miner

    initial_res = state.team_resources["blue"]
    initial_dep_amt = dep.amount

    blue_act = {"actions": [{"unit_id": 201, "action": "gather", "deposit_id": dep.id}]}
    engine.step(blue_output=blue_act, red_output={"actions": []})

    # Gathered 10 + passive 5 = +15 resources
    assert state.team_resources["blue"] == initial_res + 15
    assert dep.amount == initial_dep_amt - 10

def test_visibility_and_fog_of_war():
    engine = GameEngine()
    state = engine.state

    # Blue observation should NOT see red units far away near red base
    blue_obs = engine.get_observation("blue")
    visible_enemies = blue_obs["visible_enemies"]

    # Red units near red base (26, 26) are not visible from blue base (3, 3)
    red_enemy_ids = [u.id for u in state.units.values() if u.team == "red"]
    for e in visible_enemies:
        assert e["team"] == "red"
        # Verify distance is within vision
        blue_units_and_base = [(u.x, u.y, u.vision) for u in state.units.values() if u.alive and u.team == "blue"]
        base = state.structures["base_blue"]
        blue_units_and_base.append((base.x, base.y, base.vision))
        can_see = any((e["x"] - ux)**2 + (e["y"] - uy)**2 <= v**2 for ux, uy, v in blue_units_and_base)
        assert can_see is True

    # At turn 0, with units separated, visible enemies should be empty
    assert len(visible_enemies) == 0

def test_scoring_weights():
    engine = GameEngine()
    scores = ScoringSystem.calculate_team_scores(engine.state, "blue")
    assert "final_score" in scores
    assert "breakdown" in scores
    assert 0.0 <= scores["final_score"] <= 100.0
    for k in ["combat", "resource_territory", "strategic", "efficiency", "adaptability"]:
        assert k in scores["breakdown"]

def test_base_destruction_victory():
    engine = GameEngine()
    # Damage red base to 0
    engine.state.structures["base_red"].hp = 0
    engine.state.structures["base_red"].alive = False

    result = VictorySystem.check_victory(engine.state)
    assert result is not None
    assert result["winner"] == "blue"
    assert "Red base destroyed" in result["reason"]

