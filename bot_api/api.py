"""
Bot API toolkit and base controller for PROXY BOT WARS participants.
"""
import sys
import json
import math
from typing import Dict, List, Any, Optional, Tuple

class BotHelper:
    @staticmethod
    def distance(x1: int, y1: int, x2: int, y2: int) -> int:
        """Chebyshev distance (grid distance allowing 8-directional moves)."""
        return max(abs(x1 - x2), abs(y1 - y2))

    @staticmethod
    def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x1 - x2) + abs(y1 - y2)

    @staticmethod
    def step_towards(from_x: int, from_y: int, to_x: int, to_y: int, max_step: int = 1) -> Tuple[int, int]:
        """Calculates (dx, dy) step towards a target bounded by max_step."""
        dx = to_x - from_x
        dy = to_y - from_y
        step_x = 0
        step_y = 0
        if dx > 0:
            step_x = min(dx, max_step)
        elif dx < 0:
            step_x = max(dx, -max_step)
        if dy > 0:
            step_y = min(dy, max_step)
        elif dy < 0:
            step_y = max(dy, -max_step)
        return step_x, step_y


class BotController:
    """Base controller class. Participants override decide() to build strategies."""

    def on_init(self, team: str):
        self.team = team

    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receives current turn observation and returns actions dictionary:
        {
            "actions": [...],
            "message": "optional broadcast text (max 100 bytes)"
        }
        """
        return {"actions": [], "message": ""}


def run_bot(bot_instance: BotController):
    """
    Standard I/O communication harness. Reads JSON observations from STDIN,
    executes bot.decide(), and writes JSON actions to STDOUT.
    """
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            obs = json.loads(line.strip())
            response = bot_instance.decide(obs)
            if not isinstance(response, dict):
                response = {"actions": []}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            # Crash safety: return safe empty response with error message
            sys.stdout.write(json.dumps({"actions": [], "error": str(e)}) + "\n")
            sys.stdout.flush()

