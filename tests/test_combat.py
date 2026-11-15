"""
Comprehensive unit tests for Combat mechanics, Simultaneous Damage, and Defense.
"""
import pytest
from game_engine.engine import GameEngine
from game_engine.units import Unit, Structure

def test_combat_friendly_fire_prevention():
    engine = GameEngine()
    u1 = Unit.create(unit_id=1, unit_type="soldier", team="blue", x=10, y=10)
    u2 = Unit.create(unit_id=2, unit_type="soldier", team="blue", x=11, y=10)
    engine.state.units[1] = u1
    engine.state.units[2] = u2

    # Blue attacks Blue
    b_act = {"actions": [{"unit_id": 1, "action": "attack", "target_id": 2, "target_type": "unit"}]}
    step_res = engine.step(blue_output=b_act, red_output={})

    assert u2.hp == 100 # No damage dealt
    fails = [e for e in step_res["events"] if e.get("type") == "attack_failed"]
    assert any("Cannot attack friendly" in f["reason"] for f in fails)

def test_combat_simultaneous_mutual_elimination():
    engine = GameEngine()
    # Both units at 10 HP (below attack 20)
    u1 = Unit.create(unit_id=1, unit_type="soldier", team="blue", x=10, y=10)
    u2 = Unit.create(unit_id=2, unit_type="soldier", team="red", x=11, y=10)
    u1.hp = 10
    u2.hp = 10
    engine.state.units[1] = u1
    engine.state.units[2] = u2

    b_act = {"actions": [{"unit_id": 1, "action": "attack", "target_id": 2, "target_type": "unit"}]}
    r_act = {"actions": [{"unit_id": 2, "action": "attack", "target_id": 1, "target_type": "unit"}]}

    engine.step(blue_output=b_act, red_output=r_act)

    # Both dealt damage and eliminated simultaneously
    assert u1.alive is False
    assert u2.alive is False
    assert u1.hp == 0
    assert u2.hp == 0

def test_base_automated_defense():
    engine = GameEngine()
    base = engine.state.structures["base_blue"]

    # Place an enemy soldier adjacent to blue base
    enemy = Unit.create(unit_id=99, unit_type="soldier", team="red", x=base.x + 1, y=base.y)
    engine.state.units[99] = enemy
    initial_hp = enemy.hp

    # Turn with no explicit attack actions
    engine.step(blue_output={}, red_output={})

    # Base automatically struck the adjacent enemy unit
    assert enemy.hp == initial_hp - base.attack # 100 - 15 = 85

