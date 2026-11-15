"""
Action parsing, schema validation, and safe error-handling for bot responses.
"""
import json
from typing import Dict, List, Tuple, Any, Optional
from bot_api.schemas import LEGAL_ACTIONS, LEGAL_UNIT_TYPES, LEGAL_STRUCTURE_TYPES, ACTION_SCHEMA_SPEC

class BotOutputValidator:
    @staticmethod
    def parse_and_validate(raw_output: Any, team: str) -> Tuple[List[Dict[str, Any]], Optional[str], List[str]]:
        """
        Parses bot output (JSON string or dict) and returns:
        (valid_actions, broadcast_message, warnings)
        """
        warnings = []
        valid_actions = []
        broadcast_message = None

        data = raw_output
        if isinstance(raw_output, str):
            try:
                data = json.loads(raw_output.strip())
            except Exception as e:
                warnings.append(f"Invalid JSON string received: {str(e)}")
                return [], None, warnings

        if not isinstance(data, dict):
            warnings.append(f"Expected JSON object at top level, got {type(data).__name__}")
            return [], None, warnings

        # Optional communication message
        if "message" in data:
            broadcast_message = str(data["message"])

        raw_actions = data.get("actions", [])
        if not isinstance(raw_actions, list):
            warnings.append(f"'actions' key must be a list, got {type(raw_actions).__name__}")
            return [], broadcast_message, warnings

        unit_acted = set()

        for idx, act in enumerate(raw_actions):
            if not isinstance(act, dict):
                warnings.append(f"Action at index {idx} is not a JSON object")
                continue

            action_name = act.get("action")
            if action_name not in LEGAL_ACTIONS:
                warnings.append(f"Unknown action '{action_name}' at index {idx}")
                continue

            schema = ACTION_SCHEMA_SPEC[action_name]
            missing = [req for req in schema["required"] if req not in act]
            if missing:
                warnings.append(f"Action '{action_name}' missing required fields: {missing}")
                continue

            # Type checking
            type_mismatch = False
            for field_name, expected_type in schema["types"].items():
                if field_name in act and not isinstance(act[field_name], expected_type):
                    warnings.append(f"Field '{field_name}' in action '{action_name}' must be of type {expected_type.__name__}")
                    type_mismatch = True
                    break
            if type_mismatch:
                continue

            # Check unit duplicate action prevention
            u_id = act.get("unit_id")
            if u_id is not None:
                if u_id in unit_acted:
                    warnings.append(f"Unit {u_id} attempted multiple actions in a single turn. Only first action accepted.")
                    continue
                unit_acted.add(u_id)

            # Specific validations
            if action_name == "train":
                u_type = act.get("unit_type")
                if u_type not in LEGAL_UNIT_TYPES:
                    warnings.append(f"Invalid train unit_type '{u_type}'")
                    continue
                act["team"] = team

            if action_name == "build":
                s_type = act.get("structure_type")
                if s_type not in LEGAL_STRUCTURE_TYPES:
                    warnings.append(f"Invalid build structure_type '{s_type}'")
                    continue

            valid_actions.append(act)

        return valid_actions, broadcast_message, warnings

