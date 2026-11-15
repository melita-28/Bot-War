"""
Replay storage, serialization, and playback utilities for PROXY BOT WARS.
"""
import json
import os
from typing import Dict, Any, Optional

class ReplayManager:
    @staticmethod
    def save_replay(replay_data: Dict[str, Any], filepath: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(replay_data, f, indent=2)
        return os.path.abspath(filepath)

    @staticmethod
    def load_replay(filepath: str) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_summary(replay_data: Dict[str, Any]) -> Dict[str, Any]:
        meta = replay_data.get("metadata", {})
        return {
            "winner": meta.get("winner"),
            "reason": meta.get("reason"),
            "total_turns": meta.get("total_turns"),
            "final_scores": meta.get("final_scores")
        }

