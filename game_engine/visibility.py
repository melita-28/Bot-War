"""
Visibility and Fog-of-War calculation for PROXY BOT WARS.
Ensures teams only receive data they can legitimately observe.
"""
from typing import Set, Tuple, List, Dict, Any
import math

class VisibilitySystem:
    @staticmethod
    def get_visible_cells_for_source(x: int, y: int, vision_range: int, width: int, height: int) -> Set[Tuple[int, int]]:
        visible = set()
        v_sq = vision_range * vision_range
        # Bounding box around source
        min_x = max(0, x - vision_range)
        max_x = min(width - 1, x + vision_range)
        min_y = max(0, y - vision_range)
        max_y = min(height - 1, y + vision_range)

        for cy in range(min_y, max_y + 1):
            for cx in range(min_x, max_x + 1):
                dx = cx - x
                dy = cy - y
                if dx * dx + dy * dy <= v_sq:
                    visible.add((cx, cy))
        return visible

    @staticmethod
    def compute_team_vision(game_state, team: str) -> Set[Tuple[int, int]]:
        visible_cells = set()
        w = game_state.game_map.width
        h = game_state.game_map.height

        # Base vision
        base = game_state.structures.get(f"base_{team}")
        if base and base.alive:
            visible_cells.update(VisibilitySystem.get_visible_cells_for_source(base.x, base.y, base.vision, w, h))

        # Unit vision
        for unit in game_state.units.values():
            if unit.alive and unit.team == team:
                visible_cells.update(VisibilitySystem.get_visible_cells_for_source(unit.x, unit.y, unit.vision, w, h))

        # Friendly structure vision
        for struct in game_state.structures.values():
            if struct.alive and struct.team == team:
                visible_cells.update(VisibilitySystem.get_visible_cells_for_source(struct.x, struct.y, struct.vision, w, h))

        return visible_cells

    @staticmethod
    def update_team_explored(game_state, team: str, current_visible: Set[Tuple[int, int]]):
        if team not in game_state.explored_cells:
            game_state.explored_cells[team] = set()
        game_state.explored_cells[team].update(current_visible)

