"""
Team communication bus with strict byte budget constraints.
"""
from typing import Dict, Any, Optional
from game_engine.config import COMMUNICATION_BUDGET_BYTES

class CommunicationSystem:
    def __init__(self, budget_bytes: int = COMMUNICATION_BUDGET_BYTES):
        self.budget_bytes = budget_bytes
        self.team_messages: Dict[str, str] = {"blue": "", "red": ""}

    def set_message(self, team: str, message: Any) -> Dict[str, Any]:
        """
        Validates and records a team's outgoing broadcast message for the next turn.
        Returns a dict indicating success or warning.
        """
        if message is None:
            self.team_messages[team] = ""
            return {"status": "ok", "bytes": 0}

        msg_str = str(message)
        byte_len = len(msg_str.encode('utf-8'))

        if byte_len > self.budget_bytes:
            # Safely truncate or reject
            # Truncate to maximum permissible bytes
            encoded = msg_str.encode('utf-8')[:self.budget_bytes]
            # Decode safely ignoring cut multi-byte codepoint
            truncated = encoded.decode('utf-8', errors='ignore')
            self.team_messages[team] = truncated
            return {
                "status": "truncated",
                "bytes": len(truncated.encode('utf-8')),
                "warning": f"Message of {byte_len} bytes exceeded budget of {self.budget_bytes} bytes."
            }

        self.team_messages[team] = msg_str
        return {"status": "ok", "bytes": byte_len}

    def get_message(self, team: str) -> str:
        return self.team_messages.get(team, "")

