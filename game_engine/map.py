"""
Map representation, generation, and serialization for PROXY BOT WARS.
Implements reproducible, seed-based, balanced symmetrical maps inspired by tactical RTS arenas.
"""
import random
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional, Any
from game_engine.config import (
    DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT,
    RESOURCE_DEPOSIT_DEFAULT_CAPACITY,
    TEAM_BLUE, TEAM_RED
)

CELL_EMPTY = 0
CELL_OBSTACLE = 1
CELL_RESOURCE = 2
CELL_CONTROL_ZONE = 3

@dataclass
class ResourceDeposit:
    id: int
    x: int
    y: int
    amount: int
    max_amount: int
    deposit_type: str = "tempest_crystal" # 'tempest_crystal', 'ore_node'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "amount": self.amount,
            "max_amount": self.max_amount,
            "deposit_type": self.deposit_type
        }

@dataclass
class ControlZone:
    id: int
    x: int
    y: int
    radius: int = 1
    owner: Optional[str] = None
    progress: int = 0
    contender: Optional[str] = None
    name: str = "Control Zone"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "owner": self.owner,
            "progress": self.progress,
            "contender": self.contender,
            "name": self.name
        }

@dataclass
class GameMap:
    width: int
    height: int
    seed: int
    map_theme: str = "tempest_outpost"
    obstacles: Set[Tuple[int, int]] = field(default_factory=set)
    resource_deposits: Dict[int, ResourceDeposit] = field(default_factory=dict)
    control_zones: Dict[int, ControlZone] = field(default_factory=dict)
    base_positions: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    initial_unit_spawns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    terrain_decorations: List[Dict[str, Any]] = field(default_factory=list)

    def is_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_passable(self, x: int, y: int) -> bool:
        if not self.is_in_bounds(x, y):
            return False
        if (x, y) in self.obstacles:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "seed": self.seed,
            "map_theme": self.map_theme,
            "obstacles": list(self.obstacles),
            "resource_deposits": [r.to_dict() for r in self.resource_deposits.values()],
            "control_zones": [z.to_dict() for z in self.control_zones.values()],
            "base_positions": self.base_positions,
            "initial_unit_spawns": self.initial_unit_spawns,
            "terrain_decorations": self.terrain_decorations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameMap':
        gmap = cls(
            width=data["width"],
            height=data["height"],
            seed=data.get("seed", 0),
            map_theme=data.get("map_theme", "tempest_outpost"),
            obstacles=set(tuple(p) for p in data.get("obstacles", [])),
            base_positions=data.get("base_positions", {}),
            initial_unit_spawns=data.get("initial_unit_spawns", {}),
            terrain_decorations=data.get("terrain_decorations", [])
        )
        for r in data.get("resource_deposits", []):
            deposit = ResourceDeposit(
                id=r["id"],
                x=r["x"],
                y=r["y"],
                amount=r["amount"],
                max_amount=r["max_amount"],
                deposit_type=r.get("deposit_type", "tempest_crystal")
            )
            gmap.resource_deposits[deposit.id] = deposit

        for z in data.get("control_zones", []):
            zone = ControlZone(
                id=z["id"],
                x=z["x"],
                y=z["y"],
                radius=z.get("radius", 1),
                owner=z.get("owner"),
                progress=z.get("progress", 0),
                contender=z.get("contender"),
                name=z.get("name", "Control Zone")
            )
            gmap.control_zones[zone.id] = zone

        return gmap


class MapGenerator:
    """Generates fair, rotationally symmetric RTS maps with fortified bases and infested zones."""

    @staticmethod
    def generate(width: int = DEFAULT_MAP_WIDTH, height: int = DEFAULT_MAP_HEIGHT, seed: int = 42) -> GameMap:
        return MapGenerator.generate_tempest_outpost(width=width, height=height, seed=seed)

    @staticmethod
    def generate_tempest_outpost(width: int = DEFAULT_MAP_WIDTH, height: int = DEFAULT_MAP_HEIGHT, seed: int = 42) -> GameMap:
        rng = random.Random(seed)
        gmap = GameMap(width=width, height=height, seed=seed, map_theme="tempest_outpost")

        # 1. Base locations (symmetrical around center)
        # Blue at (3, 3), Red at (width - 4, height - 4)
        blue_base = (3, 3)
        red_base = (width - 4, height - 4)
        gmap.base_positions[TEAM_BLUE] = blue_base
        gmap.base_positions[TEAM_RED] = red_base

        reserved_cells: Set[Tuple[int, int]] = set()
        for bx, by in [blue_base, red_base]:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    reserved_cells.add((bx + dx, by + dy))

        # 2. Fortified Military Perimeter Walls with Blast Gates (like Tempest Rising base enclosure)
        # Blue base perimeter wall (from x=1..5, y=1..5), with gate at (5, 3) and (3, 5)
        blue_walls = [
            (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
            (1, 2),                         (5, 2),
            (1, 3),                                  # (5, 3) is East Blast Gate
            (1, 4),                         (5, 4),
            (1, 5), (2, 5),        (4, 5), (5, 5)   # (3, 5) is South Blast Gate
        ]
        for wx, wy in blue_walls:
            gmap.obstacles.add((wx, wy))
            # Symmetrical Red perimeter wall
            rwx = width - 1 - wx
            rwy = height - 1 - wy
            gmap.obstacles.add((rwx, rwy))

        # 3. Control Zones
        center_x, center_y = width // 2, height // 2
        gmap.control_zones[1] = ControlZone(id=1, x=center_x, y=center_y, radius=1, name="Central Radar Relay")
        reserved_cells.add((center_x, center_y))

        # Flanking energy pylon control zones
        flank1_x, flank1_y = width // 4, 3 * height // 4
        flank2_x, flank2_y = width - 1 - flank1_x, height - 1 - flank1_y
        gmap.control_zones[2] = ControlZone(id=2, x=flank1_x, y=flank1_y, radius=1, name="West Creep Extractor")
        gmap.control_zones[3] = ControlZone(id=3, x=flank2_x, y=flank2_y, radius=1, name="East Creep Extractor")
        reserved_cells.update([(flank1_x, flank1_y), (flank2_x, flank2_y)])

        # 4. Resource Deposits (Crimson Tempest Crystals & Mining Nodes)
        deposit_id = 1
        # Inside/near base secure mineral nodes
        base_resources = [
            (blue_base[0] - 1, blue_base[1] - 1), # inside perimeter
            (blue_base[0] + 3, blue_base[1] + 1), # outside east gate
            (blue_base[0] + 1, blue_base[1] + 3), # outside south gate
        ]
        for rx, ry in base_resources:
            gmap.resource_deposits[deposit_id] = ResourceDeposit(
                id=deposit_id, x=rx, y=ry,
                amount=RESOURCE_DEPOSIT_DEFAULT_CAPACITY,
                max_amount=RESOURCE_DEPOSIT_DEFAULT_CAPACITY,
                deposit_type="ore_node"
            )
            reserved_cells.add((rx, ry))
            deposit_id += 1

            # Rotational Red equivalent
            rrx, rry = width - 1 - rx, height - 1 - ry
            gmap.resource_deposits[deposit_id] = ResourceDeposit(
                id=deposit_id, x=rrx, y=rry,
                amount=RESOURCE_DEPOSIT_DEFAULT_CAPACITY,
                max_amount=RESOURCE_DEPOSIT_DEFAULT_CAPACITY,
                deposit_type="ore_node"
            )
            reserved_cells.add((rrx, rry))
            deposit_id += 1

        # Midfield High-Density Crimson "Tempest" Infested Crystal Fields
        tempest_fields = [
            (center_x - 3, center_y - 2),
            (center_x + 3, center_y + 2),
            (center_x - 4, center_y + 4),
            (center_x + 4, center_y - 4),
        ]
        for tx, ty in tempest_fields:
            if (tx, ty) not in reserved_cells:
                gmap.resource_deposits[deposit_id] = ResourceDeposit(
                    id=deposit_id, x=tx, y=ty,
                    amount=RESOURCE_DEPOSIT_DEFAULT_CAPACITY * 2,
                    max_amount=RESOURCE_DEPOSIT_DEFAULT_CAPACITY * 2,
                    deposit_type="tempest_crystal"
                )
                reserved_cells.add((tx, ty))
                deposit_id += 1

        # 5. Tactical Chokepoints, Bunkers & Sandbag revetments
        # Central fortified corridors
        bunker_clusters = [
            (center_x - 5, center_y), (center_x - 5, center_y + 1),
            (center_x + 5, center_y), (center_x + 5, center_y - 1),
            (center_x, center_y - 5), (center_x + 1, center_y - 5),
            (center_x, center_y + 5), (center_x - 1, center_y + 5),
        ]
        for bx, by in bunker_clusters:
            if (bx, by) not in reserved_cells:
                gmap.obstacles.add((bx, by))

        # Flanking rocky crags
        crag_seeds = [
            (8, 14), (8, 15), (8, 16),
            (14, 8), (15, 8), (16, 8)
        ]
        for cx, cy in crag_seeds:
            gmap.obstacles.add((cx, cy))
            rcx, rcy = width - 1 - cx, height - 1 - cy
            gmap.obstacles.add((rcx, rcy))

        # Terrain aesthetic metadata (alien creep tendrils & scorched asphalt)
        gmap.terrain_decorations.append({
            "type": "tempest_infestation_zone",
            "center": [center_x - 4, center_y + 4],
            "radius": 4,
            "color": "crimson"
        })
        gmap.terrain_decorations.append({
            "type": "tempest_infestation_zone",
            "center": [center_x + 4, center_y - 4],
            "radius": 4,
            "color": "crimson"
        })

        # 6. Initial Unit Spawns (Inside/At gates of base)
        gmap.initial_unit_spawns[TEAM_BLUE] = [
            {"type": "scout", "x": blue_base[0] + 1, "y": blue_base[1]},
            {"type": "miner", "x": blue_base[0], "y": blue_base[1] + 1},
            {"type": "soldier", "x": blue_base[0] + 1, "y": blue_base[1] + 1},
            {"type": "engineer", "x": blue_base[0] - 1, "y": blue_base[1] + 1}
        ]
        gmap.initial_unit_spawns[TEAM_RED] = [
            {"type": "scout", "x": red_base[0] - 1, "y": red_base[1]},
            {"type": "miner", "x": red_base[0], "y": red_base[1] - 1},
            {"type": "soldier", "x": red_base[0] - 1, "y": red_base[1] - 1},
            {"type": "engineer", "x": red_base[0] + 1, "y": red_base[1] - 1}
        ]

        return gmap
