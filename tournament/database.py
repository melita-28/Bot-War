"""
SQLite Database interface for PROXY BOT WARS tournament management.
Persists teams, submissions, matches, scores, and leaderboard rankings.
"""
import sqlite3
import os
import json
from typing import Dict, List, Any, Optional

DEFAULT_DB_PATH = "tournament.db"

class TournamentDatabase:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Teams table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                institution TEXT,
                members TEXT,
                bot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Submissions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                bot_path TEXT NOT NULL,
                is_valid INTEGER DEFAULT 0,
                report TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
            """)

            # Matches table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_name TEXT,
                blue_team_id INTEGER,
                red_team_id INTEGER,
                winner_team_id INTEGER,
                winner_name TEXT,
                reason TEXT,
                blue_score REAL,
                red_score REAL,
                final_turn INTEGER,
                replay_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(blue_team_id) REFERENCES teams(id),
                FOREIGN KEY(red_team_id) REFERENCES teams(id)
            );
            """)

            conn.commit()

    def register_team(self, name: str, institution: str = "", members: str = "", bot_path: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO teams (name, institution, members, bot_path) VALUES (?, ?, ?, ?)",
                (name, institution, members, bot_path)
            )
            conn.commit()
            return cursor.lastrowid

    def get_teams(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def record_submission(self, team_id: int, bot_path: str, is_valid: bool, report: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO submissions (team_id, bot_path, is_valid, report) VALUES (?, ?, ?, ?)",
                (team_id, bot_path, 1 if is_valid else 0, report)
            )
            # Update team's active bot_path
            if is_valid:
                cursor.execute("UPDATE teams SET bot_path = ? WHERE id = ?", (bot_path, team_id))
            conn.commit()
            return cursor.lastrowid

    def record_match(
        self,
        round_name: str,
        blue_team_id: int,
        red_team_id: int,
        winner_team_id: Optional[int],
        winner_name: str,
        reason: str,
        blue_score: float,
        red_score: float,
        final_turn: int,
        replay_path: str
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO matches (
                round_name, blue_team_id, red_team_id, winner_team_id,
                winner_name, reason, blue_score, red_score, final_turn, replay_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                round_name, blue_team_id, red_team_id, winner_team_id,
                winner_name, reason, blue_score, red_score, final_turn, replay_path
            ))
            conn.commit()
            return cursor.lastrowid

    def get_matches(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT m.*, tb.name as blue_team_name, tr.name as red_team_name
            FROM matches m
            LEFT JOIN teams tb ON m.blue_team_id = tb.id
            LEFT JOIN teams tr ON m.red_team_id = tr.id
            ORDER BY m.id DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Calculates tournament rankings from recorded match statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            teams = self.get_teams()
            stats = {t["id"]: {
                "id": t["id"],
                "name": t["name"],
                "matches_played": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "total_score": 0.0,
                "avg_score": 0.0
            } for t in teams}

            cursor.execute("SELECT * FROM matches")
            matches = cursor.fetchall()
            for m in matches:
                b_id = m["blue_team_id"]
                r_id = m["red_team_id"]
                w_id = m["winner_team_id"]

                if b_id in stats:
                    stats[b_id]["matches_played"] += 1
                    stats[b_id]["total_score"] += m["blue_score"] or 0.0
                    if w_id == b_id:
                        stats[b_id]["wins"] += 1
                    elif w_id == r_id:
                        stats[b_id]["losses"] += 1
                    else:
                        stats[b_id]["draws"] += 1

                if r_id in stats:
                    stats[r_id]["matches_played"] += 1
                    stats[r_id]["total_score"] += m["red_score"] or 0.0
                    if w_id == r_id:
                        stats[r_id]["wins"] += 1
                    elif w_id == b_id:
                        stats[r_id]["losses"] += 1
                    else:
                        stats[r_id]["draws"] += 1

            for s in stats.values():
                if s["matches_played"] > 0:
                    s["avg_score"] = round(s["total_score"] / s["matches_played"], 2)
                    s["total_score"] = round(s["total_score"], 2)

            # Rank by wins descending, then avg_score descending
            ranked = sorted(stats.values(), key=lambda x: (x["wins"], x["avg_score"]), reverse=True)
            for idx, item in enumerate(ranked):
                item["rank"] = idx + 1
            return ranked

