"""
Tests for Tournament Management, Database persistence, and Bracket generation.
"""
import pytest
import os
from tournament.database import TournamentDatabase
from tournament.manager import TournamentManager
from tournament.bracket import BracketManager

def test_team_registration_and_db(tmp_path):
    db_file = str(tmp_path / "t1.db")
    db = TournamentDatabase(db_file)
    t1_id = db.register_team(name="AlphaBot", institution="CSE Dept", members="Alice, Bob", bot_path="bots/starter_bot.py")
    t2_id = db.register_team(name="OmegaBot", institution="CSE Dept", members="Charlie, David", bot_path="bots/baseline_bot.py")

    teams = db.get_teams()
    assert len(teams) == 2
    assert teams[0]["name"] == "AlphaBot"
    assert teams[1]["name"] == "OmegaBot"

def test_bracket_generation():
    teams = [
        {"id": 1, "name": "Team 1"},
        {"id": 2, "name": "Team 2"},
        {"id": 3, "name": "Team 3"},
        {"id": 4, "name": "Team 4"}
    ]
    bracket = BracketManager.generate_single_elimination_bracket(teams)
    assert bracket["bracket_size"] == 4
    assert len(bracket["rounds"]) == 2 # Semifinals, Finals
    assert len(bracket["matches"]["Semifinals"]) == 2

def test_tournament_match_execution(tmp_path):
    db_file = str(tmp_path / "t2.db")
    tm = TournamentManager(db_file)
    t1 = tm.register_team("Team Blue", "Univ A", "Member 1", "bots/starter_bot.py")
    t2 = tm.register_team("Team Red", "Univ B", "Member 2", "bots/baseline_bot.py")

    # Run quick 10 turn match
    match_result = tm.execute_match(
        blue_team_id=t1["team_id"],
        red_team_id=t2["team_id"],
        round_name="Quarterfinals",
        max_turns=10,
        seed=101
    )

    assert "match_id" in match_result
    assert match_result["blue_team"] == "Team Blue"
    assert match_result["red_team"] == "Team Red"
    assert match_result["final_turn"] == 10

    # Check leaderboard
    lb = tm.get_leaderboard()
    assert len(lb) == 2
    assert lb[0]["matches_played"] == 1
    assert lb[1]["matches_played"] == 1
