"""
Victory condition evaluation and tie-breaking for PROXY BOT WARS.
"""
from typing import Dict, Any, Optional, Tuple
from game_engine.scoring import ScoringSystem

class VictorySystem:
    @staticmethod
    def check_victory(game_state) -> Optional[Dict[str, Any]]:
        """
        Evaluates match termination conditions.
        Returns None if match continues, or result dictionary if finished.
        """
        blue_base = game_state.structures.get("base_blue")
        red_base = game_state.structures.get("base_red")

        blue_base_alive = blue_base and blue_base.alive
        red_base_alive = red_base and red_base.alive

        # Condition 1: Base destruction
        if not blue_base_alive and not red_base_alive:
            # Both bases destroyed in simultaneous turn
            return VictorySystem._resolve_score_winner(game_state, reason="Mutual base destruction")
        elif not blue_base_alive:
            return VictorySystem._format_winner(game_state, winner="red", reason="Blue base destroyed")
        elif not red_base_alive:
            return VictorySystem._format_winner(game_state, winner="blue", reason="Red base destroyed")

        # Condition 2: Elimination of all units and base
        blue_units = [u for u in game_state.units.values() if u.alive and u.team == "blue"]
        red_units = [u for u in game_state.units.values() if u.alive and u.team == "red"]

        if len(blue_units) == 0 and game_state.team_resources["blue"] < 30:
            # Blue has no units and cannot afford to train any unit
            return VictorySystem._format_winner(game_state, winner="red", reason="Blue eliminated and bankrupt")
        if len(red_units) == 0 and game_state.team_resources["red"] < 30:
            return VictorySystem._format_winner(game_state, winner="blue", reason="Red eliminated and bankrupt")

        # Condition 3: Turn limit reached
        if game_state.current_turn >= game_state.max_turns:
            return VictorySystem._resolve_score_winner(game_state, reason="Turn limit reached")

        return None

    @staticmethod
    def _format_winner(game_state, winner: str, reason: str) -> Dict[str, Any]:
        scores = {
            "blue": ScoringSystem.calculate_team_scores(game_state, "blue"),
            "red": ScoringSystem.calculate_team_scores(game_state, "red")
        }
        return {
            "is_game_over": True,
            "winner": winner,
            "reason": reason,
            "final_turn": game_state.current_turn,
            "scores": scores
        }

    @staticmethod
    def _resolve_score_winner(game_state, reason: str) -> Dict[str, Any]:
        blue_score_data = ScoringSystem.calculate_team_scores(game_state, "blue")
        red_score_data = ScoringSystem.calculate_team_scores(game_state, "red")

        b_score = blue_score_data["final_score"]
        r_score = red_score_data["final_score"]

        winner = None
        tie_break_used = None

        if b_score > r_score:
            winner = "blue"
        elif r_score > b_score:
            winner = "red"
        else:
            # Deterministic Tie-breaks:
            # 1. Combat score
            b_combat = blue_score_data["breakdown"]["combat"]
            r_combat = red_score_data["breakdown"]["combat"]
            if b_combat > r_combat:
                winner = "blue"
                tie_break_used = "Higher combat performance"
            elif r_combat > b_combat:
                winner = "red"
                tie_break_used = "Higher combat performance"
            else:
                # 2. Resources collected
                b_res = game_state.stats["blue"]["resources_collected"]
                r_res = game_state.stats["red"]["resources_collected"]
                if b_res > r_res:
                    winner = "blue"
                    tie_break_used = "Most resources collected"
                elif r_res > b_res:
                    winner = "red"
                    tie_break_used = "Most resources collected"
                else:
                    # 3. Total surviving unit HP
                    b_hp = sum(u.hp for u in game_state.units.values() if u.alive and u.team == "blue")
                    r_hp = sum(u.hp for u in game_state.units.values() if u.alive and u.team == "red")
                    if b_hp > r_hp:
                        winner = "blue"
                        tie_break_used = "Highest surviving army HP"
                    elif r_hp > b_hp:
                        winner = "red"
                        tie_break_used = "Highest surviving army HP"
                    else:
                        winner = "draw"
                        tie_break_used = "Absolute draw"

        full_reason = reason + (f" ({tie_break_used})" if tie_break_used else "")
        return {
            "is_game_over": True,
            "winner": winner,
            "reason": full_reason,
            "final_turn": game_state.current_turn,
            "scores": {
                "blue": blue_score_data,
                "red": red_score_data
            }
        }

