"""
Unit tests for Visibility, Fog of War, and Exploration.
"""
import pytest
from game_engine.engine import GameEngine
from game_engine.units import Unit
from game_engine.visibility import VisibilitySystem

def test_visibility_range_calculation():
    # Test circular Euclidean range around (15, 15) with vision 5
    cells = VisibilitySystem.get_visible_cells_for_source(15, 15, vision_range=5, width=30, height=30)
    assert (15, 15) in cells
    assert (15, 20) in cells # distance 5
    assert (15, 21) not in cells # distance 6 (out of range)
    # Check corner: dx=4, dy=4 -> d^2 = 32 > 25 (should not be in range)
    assert (19, 19) not in cells
    # dx=3, dy=4 -> d^2 = 25 (exact edge)
    assert (18, 19) in cells

def test_enemy_hidden_outside_vision():
    engine = GameEngine()
    # Place a hidden enemy at (15, 15)
    hidden_enemy = Unit.create(unit_id=99, unit_type="tank", team="red", x=15, y=15)
    engine.state.units[99] = hidden_enemy

    # Blue units are all near (3, 3) (distance > 10 from (15, 15))
    blue_obs = engine.get_observation("blue")
    visible_enemy_ids = [e["id"] for e in blue_obs["visible_enemies"]]
    assert 99 not in visible_enemy_ids

    # Now move a blue scout close to (15, 14)
    scout = [u for u in engine.state.units.values() if u.team == "blue" and u.unit_type == "scout"][0]
    scout.x = 15
    scout.y = 14

    # Red enemy must now become visible in blue observation!
    blue_obs_after = engine.get_observation("blue")
    visible_after = [e["id"] for e in blue_obs_after["visible_enemies"]]
    assert 99 in visible_after

