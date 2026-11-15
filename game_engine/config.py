"""
Game engine configuration and rules constants for PROXY BOT WARS.
All baseline statistics, costs, ranges, scoring weights, and limits are formally defined here.
"""
from dataclasses import dataclass
from typing import Dict, Any

# Map Dimensions
DEFAULT_MAP_WIDTH = 30
DEFAULT_MAP_HEIGHT = 30

# Turn and Computation Limits
DEFAULT_MAX_TURNS = 150
DEFAULT_TURN_TIMEOUT_SECONDS = 1.0
COMMUNICATION_BUDGET_BYTES = 100

# Economy and Resources
STARTING_RESOURCES = 100
BASE_PASSIVE_INCOME = 5
MINER_GATHER_RATE = 10
RESOURCE_DEPOSIT_DEFAULT_CAPACITY = 500

# Base Building Stats
BASE_MAX_HP = 500
BASE_ATTACK = 15
BASE_ATTACK_RANGE = 2
BASE_VISION = 6

# Unit Baseline Specifications
# Unit | HP | Attack | Speed | Vision | Range | Cost
UNIT_SPECS = {
    "scout": {
        "hp": 40,
        "attack": 5,
        "speed": 4,
        "vision": 10,
        "attack_range": 1,
        "cost": 30,
        "description": "Exploration, reconnaissance and rapid movement."
    },
    "soldier": {
        "hp": 100,
        "attack": 20,
        "speed": 2,
        "vision": 5,
        "attack_range": 2,
        "cost": 50,
        "description": "General combat and tactical skirmishing."
    },
    "tank": {
        "hp": 250,
        "attack": 40,
        "speed": 1,
        "vision": 4,
        "attack_range": 3,
        "cost": 100,
        "description": "Heavy frontline combat and siege warfare."
    },
    "miner": {
        "hp": 60,
        "attack": 0,
        "speed": 2,
        "vision": 5,
        "attack_range": 0,
        "cost": 40,
        "description": "Extracts resources from nearby deposits."
    },
    "engineer": {
        "hp": 70,
        "attack": 5,
        "speed": 2,
        "vision": 6,
        "attack_range": 1,
        "cost": 60,
        "description": "Constructs barricades/turrets and repairs friendly units."
    }
}

# Structures constructible by Engineer
STRUCTURE_SPECS = {
    "barricade": {
        "hp": 150,
        "cost": 25,
        "attack": 0,
        "attack_range": 0,
        "vision": 2,
        "build_time": 1, # turns
        "description": "Defensive obstacle blocking enemy movement."
    },
    "turret": {
        "hp": 120,
        "cost": 75,
        "attack": 15,
        "attack_range": 2,
        "vision": 4,
        "build_time": 1,
        "description": "Stationary automated defensive weapon."
    }
}

ENGINEER_REPAIR_AMOUNT = 20
ENGINEER_REPAIR_RANGE = 1

# Neutral Control Zones
CONTROL_ZONE_POINTS_PER_TURN = 2
CONTROL_ZONE_CAPTURE_THRESHOLD = 3 # Consecutive uncontested turns to capture

# Official Scoring Category Weights (Total = 1.00 / 100%)
SCORING_WEIGHTS = {
    "combat": 0.30,
    "resource_territory": 0.20,
    "strategic": 0.20,
    "efficiency": 0.15,
    "adaptability": 0.15
}

# Teams
TEAM_BLUE = "blue"
TEAM_RED = "red"
TEAMS = [TEAM_BLUE, TEAM_RED]

