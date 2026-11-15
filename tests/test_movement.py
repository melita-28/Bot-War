"""
Comprehensive unit tests for Movement, Collisions, and Map Boundaries.
"""
import pytest
from game_engine.engine import GameEngine
from game_engine.units import Unit

def test_movement_within_bounds():
    engine = GameEngine()
    unit = Unit.create(unit_id=1, unit_type="scout", team="blue", x=10, y=10)
    engine.state.units[1] = unit

    # Move right 3 cells (speed=4)
    engine.step(blue_output={"actions": [{"unit_id": 1, "action": "move", "dx": 3, "dy": 0}]}, red_output={})
    assert unit.x == 13
    assert unit.y == 10

def test_movement_boundary_enforcement():
    engine = GameEngine()
    unit = Unit.create(unit_id=1, unit_type="scout", team="blue", x=0, y=0)
    engine.state.units[1] = unit

    # Move out of left boundary (dx = -1)
    engine.step(blue_output={"actions": [{"unit_id": 1, "action": "move", "dx": -1, "dy": 0}]}, red_output={})
    assert unit.x == 0 # Must not move outside
    assert unit.y == 0

def test_movement_obstacle_collision():
    engine = GameEngine()
    # Place an obstacle directly at (10, 11)
    engine.state.game_map.obstacles.add((10, 11))

    unit = Unit.create(unit_id=1, unit_type="soldier", team="blue", x=10, y=10)
    engine.state.units[1] = unit

    # Move into obstacle
    engine.step(blue_output={"actions": [{"unit_id": 1, "action": "move", "dx": 0, "dy": 1}]}, red_output={})
    assert unit.x == 10
    assert unit.y == 10 # Rejected, stayed in place

def test_simultaneous_movement_collision_rebound():
    engine = GameEngine()
    # Blue unit at (10, 10), Red unit at (12, 10)
    u1 = Unit.create(unit_id=1, unit_type="soldier", team="blue", x=10, y=10)
    u2 = Unit.create(unit_id=2, unit_type="soldier", team="red", x=12, y=10)
    engine.state.units[1] = u1
    engine.state.units[2] = u2

    # Both units attempt to step into (11, 10) on the exact same turn
    b_act = {"actions": [{"unit_id": 1, "action": "move", "dx": 1, "dy": 0}]}
    r_act = {"actions": [{"unit_id": 2, "action": "move", "dx": -1, "dy": 0}]}

    step_res = engine.step(blue_output=b_act, red_output=r_act)

    # Collision detected: both bounce back to prevent collision favoritism
    assert u1.x == 10
    assert u2.x == 12
    collision_events = [e for e in step_res["events"] if e.get("type") == "move_collision"]
    assert len(collision_events) >= 2

