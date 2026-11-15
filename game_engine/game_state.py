"""
Comprehensive GameState representation and observation builder for PROXY BOT WARS.
"""
from typing import Dict, List, Set, Tuple, Any, Optional
from game_engine.map import GameMap
from game_engine.units import Unit, Structure
from game_engine.config import (
    DEFAULT_MAX_TURNS, STARTING_RESOURCES, BASE_MAX_HP, BASE_ATTACK,
    BASE_ATTACK_RANGE, BASE_VISION, TEAM_BLUE, TEAM_RED
)
from game_engine.visibility import VisibilitySystem
from game_engine.communication import CommunicationSystem

class GameState:
    def __init__(self, game_map: GameMap, max_turns: int = DEFAULT_MAX_TURNS):
        self.game_map = game_map
        self.current_turn = 0
        self.max_turns = max_turns

        self.units: Dict[int, Unit] = {}
        self.structures: Dict[str, Structure] = {}
        self.team_resources: Dict[str, int] = {
            TEAM_BLUE: STARTING_RESOURCES,
            TEAM_RED: STARTING_RESOURCES
        }

        self.explored_cells: Dict[str, Set[Tuple[int, int]]] = {
            TEAM_BLUE: set(),
            TEAM_RED: set()
        }

        self.communication = CommunicationSystem()
        self.next_unit_id = 1
        self.next_structure_id = 1

        # Match tracking metrics
        self.stats = {
            TEAM_BLUE: {
                "damage_dealt": 0,
                "damage_received": 0,
                "units_killed": 0,
                "units_lost": 0,
                "units_trained": 0,
                "structures_built": 0,
                "resources_collected": 0,
                "resources_spent": 0,
                "control_points": 0,
                "territory_turns": 0,
                "total_time_ms": 0.0,
                "turns_executed": 0
            },
            TEAM_RED: {
                "damage_dealt": 0,
                "damage_received": 0,
                "units_killed": 0,
                "units_lost": 0,
                "units_trained": 0,
                "structures_built": 0,
                "resources_collected": 0,
                "resources_spent": 0,
                "control_points": 0,
                "territory_turns": 0,
                "total_time_ms": 0.0,
                "turns_executed": 0
            }
        }

        # Initialize Base structures
        blue_bp = game_map.base_positions.get(TEAM_BLUE, (3, 3))
        red_bp = game_map.base_positions.get(TEAM_RED, (game_map.width - 4, game_map.height - 4))

        self.structures["base_blue"] = Structure(
            id="base_blue",
            structure_type="base",
            team=TEAM_BLUE,
            x=blue_bp[0],
            y=blue_bp[1],
            hp=BASE_MAX_HP,
            max_hp=BASE_MAX_HP,
            attack=BASE_ATTACK,
            attack_range=BASE_ATTACK_RANGE,
            vision=BASE_VISION,
            alive=True
        )

        self.structures["base_red"] = Structure(
            id="base_red",
            structure_type="base",
            team=TEAM_RED,
            x=red_bp[0],
            y=red_bp[1],
            hp=BASE_MAX_HP,
            max_hp=BASE_MAX_HP,
            attack=BASE_ATTACK,
            attack_range=BASE_ATTACK_RANGE,
            vision=BASE_VISION,
            alive=True
        )

        # Initialize initial units from map spawn specification
        for team, spawns in game_map.initial_unit_spawns.items():
            for sp in spawns:
                unit = Unit.create(
                    unit_id=self.next_unit_id,
                    unit_type=sp["type"],
                    team=team,
                    x=sp["x"],
                    y=sp["y"]
                )
                self.units[self.next_unit_id] = unit
                self.next_unit_id += 1

        # Initial visibility compute
        for t in [TEAM_BLUE, TEAM_RED]:
            visible = VisibilitySystem.compute_team_vision(self, t)
            VisibilitySystem.update_team_explored(self, t, visible)

    def get_observation_for_team(self, team: str) -> Dict[str, Any]:
        """
        Generates the restricted, fog-of-war compliant JSON observation for a bot.
        Enemy units outside visibility are strictly omitted.
        """
        opp_team = TEAM_RED if team == TEAM_BLUE else TEAM_BLUE
        current_visible = VisibilitySystem.compute_team_vision(self, team)
        VisibilitySystem.update_team_explored(self, team, current_visible)
        explored = self.explored_cells[team]

        # 1. Friendly units (all alive units)
        friendly_units = [
            u.to_dict() for u in self.units.values()
            if u.alive and u.team == team
        ]

        # 2. Visible enemy units (ONLY those in current_visible)
        visible_enemies = [
            u.to_dict() for u in self.units.values()
            if u.alive and u.team == opp_team and (u.x, u.y) in current_visible
        ]

        # 3. Structures (friendly base/structures always visible, enemy structures only if visible or explored)
        structures = []
        for s in self.structures.values():
            if not s.alive:
                continue
            if s.team == team:
                structures.append(s.to_dict())
            elif (s.x, s.y) in current_visible:
                structures.append(s.to_dict())

        # 4. Visible resources
        visible_resources = []
        for dep in self.game_map.resource_deposits.values():
            if (dep.x, dep.y) in current_visible or (dep.x, dep.y) in explored:
                visible_resources.append(dep.to_dict())

        # 5. Visible control zones
        control_zones = []
        for z in self.game_map.control_zones.values():
            if (z.x, z.y) in current_visible or (z.x, z.y) in explored:
                control_zones.append(z.to_dict())

        # 6. Explored obstacles
        known_obstacles = [
            list(pos) for pos in self.game_map.obstacles
            if pos in explored
        ]

        # 7. Incoming team broadcast
        team_message = self.communication.get_message(team)

        # Friendly base info
        my_base = self.structures.get(f"base_{team}")

        return {
            "turn": self.current_turn,
            "max_turns": self.max_turns,
            "team": team,
            "resources": self.team_resources[team],
            "base": my_base.to_dict() if my_base else None,
            "units": friendly_units,
            "visible_enemies": visible_enemies,
            "visible_structures": structures,
            "visible_resources": visible_resources,
            "control_zones": control_zones,
            "known_obstacles": known_obstacles,
            "team_message": team_message,
            "map_width": self.game_map.width,
            "map_height": self.game_map.height,
            "explored_count": len(explored),
            "stats": {
                "damage_dealt": self.stats[team]["damage_dealt"],
                "units_killed": self.stats[team]["units_killed"],
                "resources_collected": self.stats[team]["resources_collected"]
            }
        }

    def to_snapshot(self) -> Dict[str, Any]:
        """Full game state snapshot used for replays and spectator visualizer."""
        return {
            "turn": self.current_turn,
            "team_resources": dict(self.team_resources),
            "units": [u.to_dict() for u in self.units.values() if u.alive],
            "structures": [s.to_dict() for s in self.structures.values() if s.alive],
            "resource_deposits": [d.to_dict() for d in self.game_map.resource_deposits.values()],
            "control_zones": [z.to_dict() for z in self.game_map.control_zones.values()],
            "stats": {
                TEAM_BLUE: dict(self.stats[TEAM_BLUE]),
                TEAM_RED: dict(self.stats[TEAM_RED])
            }
        }

