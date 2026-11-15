"""
Tournament Bracket generation and progression for PROXY BOT WARS.
Supports single-elimination knockout brackets (Quarterfinals, Semifinals, Finals).
"""
import math
from typing import List, Dict, Any, Optional

class BracketManager:
    @staticmethod
    def generate_single_elimination_bracket(teams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates bracket structure for N teams (seeds 1 to N).
        Pads to power of 2 with byes if necessary.
        """
        num_teams = len(teams)
        if num_teams < 2:
            return {"rounds": [], "error": "At least 2 teams required"}

        # Find power of 2
        bracket_size = 1
        while bracket_size < num_teams:
            bracket_size *= 2

        # Round names
        round_names = {
            2: ["Finals"],
            4: ["Semifinals", "Finals"],
            8: ["Quarterfinals", "Semifinals", "Finals"],
            16: ["Round of 16", "Quarterfinals", "Semifinals", "Finals"]
        }.get(bracket_size, [f"Round of {bracket_size // (2**i)}" for i in range(int(math.log2(bracket_size)))])

        # Seed assignments
        seeded_teams = list(teams)
        while len(seeded_teams) < bracket_size:
            seeded_teams.append({"id": None, "name": "BYE", "bot_path": None})

        # Pairings for Round 1
        round_1_matches = []
        half = bracket_size // 2
        for i in range(half):
            blue = seeded_teams[i]
            red = seeded_teams[bracket_size - 1 - i]
            round_1_matches.append({
                "match_id": f"R1_M{i+1}",
                "round": round_names[0],
                "blue_team": blue,
                "red_team": red,
                "winner": None,
                "replay_path": None
            })

        return {
            "bracket_size": bracket_size,
            "rounds": round_names,
            "current_round": round_names[0],
            "matches": {round_names[0]: round_1_matches}
        }

