"""
Central Game Engine for PROXY BOT WARS.
Implements the 10-step deterministic turn sequence and replay logging.
"""
from typing import Dict, List, Any, Optional, Tuple
import time

from game_engine.game_state import GameState
from game_engine.map import GameMap, MapGenerator
from game_engine.movement import MovementSystem
from game_engine.combat import CombatSystem
from game_engine.resources import ResourceSystem
from game_engine.construction import ConstructionSystem
from game_engine.visibility import VisibilitySystem
from game_engine.victory import VictorySystem
from bot_api.validator import BotOutputValidator
from game_engine.config import TEAM_BLUE, TEAM_RED

class GameEngine:
    def __init__(self, game_map: Optional[GameMap] = None, max_turns: int = 150):
        if game_map is None:
            game_map = MapGenerator.generate()
        self.state = GameState(game_map=game_map, max_turns=max_turns)
        self.match_history: List[Dict[str, Any]] = []
        self.match_result: Optional[Dict[str, Any]] = None

        # Record initial frame (Turn 0)
        self._record_history_frame(turn_events=[], actions_summary={})

    def get_observation(self, team: str) -> Dict[str, Any]:
        return self.state.get_observation_for_team(team)

    def step(self, blue_output: Any, red_output: Any,
             blue_time_ms: float = 0.0, red_time_ms: float = 0.0) -> Dict[str, Any]:
        """
        Executes one full game turn deterministically using the outputs from both bots.
        """
        if self.match_result is not None:
            return self.match_result

        self.state.current_turn += 1
        turn = self.state.current_turn

        # Update execution time stats
        self.state.stats[TEAM_BLUE]["total_time_ms"] += blue_time_ms
        self.state.stats[TEAM_BLUE]["turns_executed"] += 1
        self.state.stats[TEAM_RED]["total_time_ms"] += red_time_ms
        self.state.stats[TEAM_RED]["turns_executed"] += 1

        turn_events: List[Dict[str, Any]] = []

        # 1. Parse and validate bot outputs
        blue_actions, blue_msg, blue_warns = BotOutputValidator.parse_and_validate(blue_output, TEAM_BLUE)
        red_actions, red_msg, red_warns = BotOutputValidator.parse_and_validate(red_output, TEAM_RED)

        for w in blue_warns:
            turn_events.append({"type": "validator_warning", "team": TEAM_BLUE, "warning": w})
        for w in red_warns:
            turn_events.append({"type": "validator_warning", "team": TEAM_RED, "warning": w})

        # 2. Update communication bus
        if blue_msg is not None:
            self.state.communication.set_message(TEAM_BLUE, blue_msg)
        if red_msg is not None:
            self.state.communication.set_message(TEAM_RED, red_msg)

        # Categorize actions
        all_actions = blue_actions + red_actions

        moves = [a for a in all_actions if a["action"] == "move"]
        attacks = [a for a in all_actions if a["action"] == "attack"]
        gathers = [a for a in all_actions if a["action"] == "gather"]
        builds = [a for a in all_actions if a["action"] == "build"]
        repairs = [a for a in all_actions if a["action"] == "repair"]
        trains = [a for a in all_actions if a["action"] == "train"]

        # 3. Resolve Movement
        move_events = MovementSystem.resolve_movement(self.state, moves)
        turn_events.extend(move_events)

        # 4. Resolve Combat
        combat_events = CombatSystem.resolve_combat(self.state, attacks)
        turn_events.extend(combat_events)

        # 5. Resolve Gathering & Passive Income
        gather_events = ResourceSystem.resolve_gathering(self.state, gathers)
        turn_events.extend(gather_events)

        # 6. Resolve Construction & Repair
        construction_events = ConstructionSystem.resolve_construction_and_repair(self.state, builds + repairs)
        turn_events.extend(construction_events)

        # 7. Resolve Control Zones
        zone_events = ConstructionSystem.resolve_control_zones(self.state)
        turn_events.extend(zone_events)

        # 8. Resolve Unit Training
        train_events = ResourceSystem.resolve_training(self.state, trains)
        turn_events.extend(train_events)

        # 9. Update Visibility & Explored Cells
        for t in [TEAM_BLUE, TEAM_RED]:
            visible = VisibilitySystem.compute_team_vision(self.state, t)
            VisibilitySystem.update_team_explored(self.state, t, visible)

        # 10. Check Victory Conditions
        game_over_result = VictorySystem.check_victory(self.state)
        if game_over_result:
            self.match_result = game_over_result
            turn_events.append({
                "type": "game_over",
                "winner": game_over_result["winner"],
                "reason": game_over_result["reason"]
            })

        # Record replay state frame
        self._record_history_frame(
            turn_events=turn_events,
            actions_summary={
                TEAM_BLUE: len(blue_actions),
                TEAM_RED: len(red_actions)
            }
        )

        return {
            "turn": turn,
            "events": turn_events,
            "game_over": self.match_result is not None,
            "result": self.match_result
        }

    def _record_history_frame(self, turn_events: List[Dict[str, Any]], actions_summary: Dict[str, int]):
        frame = {
            "turn": self.state.current_turn,
            "events": turn_events,
            "actions_summary": actions_summary,
            "snapshot": self.state.to_snapshot()
        }
        self.match_history.append(frame)

    def get_full_replay_data(self) -> Dict[str, Any]:
        """Exports the complete replay package."""
        return {
            "metadata": {
                "map_width": self.state.game_map.width,
                "map_height": self.state.game_map.height,
                "map_seed": self.state.game_map.seed,
                "max_turns": self.state.max_turns,
                "total_turns": self.state.current_turn,
                "winner": self.match_result.get("winner") if self.match_result else "in_progress",
                "reason": self.match_result.get("reason") if self.match_result else "Match unfinished",
                "final_scores": self.match_result.get("scores") if self.match_result else None
            },
            "initial_map": self.state.game_map.to_dict(),
            "history": self.match_history
        }

