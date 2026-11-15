"""
Formal JSON Schemas and action specifications for PROXY BOT WARS.
"""
from typing import Dict, Any, List

LEGAL_ACTIONS = {"move", "attack", "gather", "build", "repair", "train", "wait"}
LEGAL_UNIT_TYPES = {"scout", "soldier", "tank", "miner", "engineer"}
LEGAL_STRUCTURE_TYPES = {"barricade", "turret"}

ACTION_SCHEMA_SPEC = {
    "move": {
        "required": ["unit_id", "dx", "dy"],
        "types": {"unit_id": int, "dx": int, "dy": int}
    },
    "attack": {
        "required": ["unit_id", "target_id"],
        "types": {"unit_id": int}
    },
    "gather": {
        "required": ["unit_id", "deposit_id"],
        "types": {"unit_id": int, "deposit_id": int}
    },
    "build": {
        "required": ["unit_id", "structure_type", "target_x", "target_y"],
        "types": {"unit_id": int, "structure_type": str, "target_x": int, "target_y": int}
    },
    "repair": {
        "required": ["unit_id", "target_id"],
        "types": {"unit_id": int}
    },
    "train": {
        "required": ["unit_type"],
        "types": {"unit_type": str}
    },
    "wait": {
        "required": ["unit_id"],
        "types": {"unit_id": int}
    }
}

