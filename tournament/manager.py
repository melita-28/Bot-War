"""
High-level Tournament Manager for PROXY BOT WARS organizers.
"""
import os
import json
from typing import List, Dict, Any, Optional

from tournament.database import TournamentDatabase
from tournament.bracket import BracketManager
from bot_api.submission_validator import SubmissionValidator
from match_runner.runner import run_match

class TournamentManager:
    def __init__(self, db_path: str = "tournament.db"):
        self.db = TournamentDatabase(db_path=db_path)

    def register_team(self, name: str, institution: str = "", members: str = "", bot_path: str = "") -> Dict[str, Any]:
        """Registers a new participating team."""
        try:
            team_id = self.db.register_team(name=name, institution=institution, members=members, bot_path=bot_path)
            return {"success": True, "team_id": team_id, "name": name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def submit_and_validate_bot(self, team_id: int, script_path: str) -> Dict[str, Any]:
        """Validates a bot file and records the submission in the database."""
        report = SubmissionValidator.validate_file(script_path)
        sub_id = self.db.record_submission(
            team_id=team_id,
            bot_path=script_path,
            is_valid=report["valid"],
            report=json.dumps(report)
        )
        return {
            "submission_id": sub_id,
            "team_id": team_id,
            "is_valid": report["valid"],
            "report": report
        }

    def execute_match(
        self,
        blue_team_id: int,
        red_team_id: int,
        round_name: str = "Knockout",
        max_turns: int = 150,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Executes an official tournament match between two registered teams."""
        blue_team = self.db.get_team_by_id(blue_team_id)
        red_team = self.db.get_team_by_id(red_team_id)

        if not blue_team or not blue_team.get("bot_path"):
            return {"error": f"Blue team {blue_team_id} not found or missing bot script"}
        if not red_team or not red_team.get("bot_path"):
            return {"error": f"Red team {red_team_id} not found or missing bot script"}

        replay_filename = f"replays/match_t{blue_team_id}_vs_t{red_team_id}_s{seed}.json"

        match_output = run_match(
            blue_bot_path=blue_team["bot_path"],
            red_bot_path=red_team["bot_path"],
            max_turns=max_turns,
            seed=seed,
            output_replay=replay_filename,
            quiet=True
        )

        res = match_output["result"]
        winner_side = res.get("winner")
        winner_id = None
        winner_name = "Draw"
        if winner_side == "blue":
            winner_id = blue_team_id
            winner_name = blue_team["name"]
        elif winner_side == "red":
            winner_id = red_team_id
            winner_name = red_team["name"]

        scores = res.get("scores", {})
        blue_score = scores.get("blue", {}).get("final_score", 0.0)
        red_score = scores.get("red", {}).get("final_score", 0.0)

        match_id = self.db.record_match(
            round_name=round_name,
            blue_team_id=blue_team_id,
            red_team_id=red_team_id,
            winner_team_id=winner_id,
            winner_name=winner_name,
            reason=res.get("reason", ""),
            blue_score=blue_score,
            red_score=red_score,
            final_turn=res.get("final_turn", 0),
            replay_path=replay_filename
        )

        return {
            "match_id": match_id,
            "round": round_name,
            "blue_team": blue_team["name"],
            "red_team": red_team["name"],
            "winner": winner_name,
            "reason": res.get("reason"),
            "blue_score": blue_score,
            "red_score": red_score,
            "final_turn": res.get("final_turn"),
            "replay_path": replay_filename
        }

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        return self.db.get_leaderboard()

    def get_bracket(self) -> Dict[str, Any]:
        teams = self.db.get_teams()
        return BracketManager.generate_single_elimination_bracket(teams)

