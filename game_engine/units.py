"""
Unit and Structure data models for PROXY BOT WARS.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from game_engine.config import UNIT_SPECS, STRUCTURE_SPECS

@dataclass
class Unit:
    id: int
    unit_type: str
    team: str
    x: int
    y: int
    hp: int
    max_hp: int
    attack: int
    speed: int
    vision: int
    attack_range: int
    carried_resources: int = 0
    alive: bool = True
    last_action: Optional[Dict[str, Any]] = None

    @classmethod
    def create(cls, unit_id: int, unit_type: str, team: str, x: int, y: int) -> 'Unit':
        spec = UNIT_SPECS[unit_type]
        return cls(
            id=unit_id,
            unit_type=unit_type,
            team=team,
            x=x,
            y=y,
            hp=spec["hp"],
            max_hp=spec["hp"],
            attack=spec["attack"],
            speed=spec["speed"],
            vision=spec["vision"],
            attack_range=spec["attack_range"],
            carried_resources=0,
            alive=True,
            last_action=None
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.unit_type,
            "team": self.team,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "speed": self.speed,
            "vision": self.vision,
            "attack_range": self.attack_range,
            "carried_resources": self.carried_resources,
            "alive": self.alive,
            "last_action": self.last_action
        }

    def take_damage(self, amount: int) -> int:
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual_damage

    def heal(self, amount: int) -> int:
        if not self.alive:
            return 0
        actual_heal = min(self.max_hp - self.hp, amount)
        self.hp += actual_heal
        return actual_heal


@dataclass
class Structure:
    id: int
    structure_type: str # 'base', 'barricade', 'turret'
    team: str # 'blue', 'red', or 'neutral'
    x: int
    y: int
    hp: int
    max_hp: int
    attack: int = 0
    attack_range: int = 0
    vision: int = 2
    alive: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.structure_type,
            "team": self.team,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "attack_range": self.attack_range,
            "vision": self.vision,
            "alive": self.alive
        }

    def take_damage(self, amount: int) -> int:
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual_damage

