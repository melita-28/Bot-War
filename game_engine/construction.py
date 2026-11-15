"""
Construction, repair, and neutral control zone resolution for PROXY BOT WARS.
"""
from typing import Dict, List, Tuple, Any, Optional
from game_engine.config import (
    STRUCTURE_SPECS, ENGINEER_REPAIR_AMOUNT,
    CONTROL_ZONE_POINTS_PER_TURN, CONTROL_ZONE_CAPTURE_THRESHOLD
)
from game_engine.units import Structure

class ConstructionSystem:
    @staticmethod
    def resolve_construction_and_repair(game_state, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolves build and repair actions performed by Engineers.
        actions: list of action dicts
        """
        events = []
        for act in actions:
            u_id = act.get("unit_id")
            action_type = act.get("action")
            engineer = game_state.units.get(u_id)
            if not engineer or not engineer.alive:
                continue

            if engineer.unit_type != "engineer":
                events.append({
                    "type": "engineer_action_failed",
                    "unit_id": u_id,
                    "reason": "Only Engineers can build or repair"
                })
                continue

            if action_type == "build":
                struct_type = act.get("structure_type")
                if struct_type not in STRUCTURE_SPECS:
                    events.append({
                        "type": "build_failed",
                        "unit_id": u_id,
                        "reason": f"Unknown structure type: {struct_type}"
                    })
                    continue

                tx = act.get("target_x")
                ty = act.get("target_y")
                if tx is None or ty is None:
                    continue

                # Range check (Chebyshev <= 1)
                dist = max(abs(engineer.x - tx), abs(engineer.y - ty))
                if dist > 1 or (engineer.x == tx and engineer.y == ty):
                    events.append({
                        "type": "build_failed",
                        "unit_id": u_id,
                        "reason": "Target cell must be adjacent (range 1) and not current engineer cell"
                    })
                    continue

                if not game_state.game_map.is_passable(tx, ty):
                    events.append({
                        "type": "build_failed",
                        "unit_id": u_id,
                        "reason": "Target cell is blocked by obstacle or out of bounds"
                    })
                    continue

                # Check cell occupancy
                occupied = any(u.alive and u.x == tx and u.y == ty for u in game_state.units.values())
                if not occupied:
                    occupied = any(s.alive and s.x == tx and s.y == ty for s in game_state.structures.values())

                if occupied:
                    events.append({
                        "type": "build_failed",
                        "unit_id": u_id,
                        "reason": "Target cell is occupied by a unit or structure"
                    })
                    continue

                cost = STRUCTURE_SPECS[struct_type]["cost"]
                if game_state.team_resources[engineer.team] < cost:
                    events.append({
                        "type": "build_failed",
                        "unit_id": u_id,
                        "reason": f"Insufficient resources: need {cost}, have {game_state.team_resources[engineer.team]}"
                    })
                    continue

                # Deduct cost and place structure
                game_state.team_resources[engineer.team] -= cost
                game_state.stats[engineer.team]["resources_spent"] += cost
                game_state.stats[engineer.team]["structures_built"] += 1

                new_struct_id = f"{struct_type}_{game_state.next_structure_id}"
                game_state.next_structure_id += 1
                spec = STRUCTURE_SPECS[struct_type]

                new_struct = Structure(
                    id=new_struct_id,
                    structure_type=struct_type,
                    team=engineer.team,
                    x=tx,
                    y=ty,
                    hp=spec["hp"],
                    max_hp=spec["hp"],
                    attack=spec.get("attack", 0),
                    attack_range=spec.get("attack_range", 0),
                    vision=spec.get("vision", 2),
                    alive=True
                )
                game_state.structures[new_struct_id] = new_struct

                engineer.last_action = {"action": "build", "structure": struct_type, "target": [tx, ty]}

                events.append({
                    "type": "structure_built",
                    "unit_id": u_id,
                    "team": engineer.team,
                    "structure_id": new_struct_id,
                    "structure_type": struct_type,
                    "x": tx,
                    "y": ty,
                    "cost": cost
                })

            elif action_type == "repair":
                target_id = act.get("target_id")
                target_type = act.get("target_type", "unit")

                if target_type == "unit":
                    target = game_state.units.get(target_id)
                    if not target or not target.alive or target.team != engineer.team:
                        events.append({
                            "type": "repair_failed",
                            "unit_id": u_id,
                            "reason": "Target unit invalid, dead, or not on friendly team"
                        })
                        continue

                    dist = max(abs(engineer.x - target.x), abs(engineer.y - target.y))
                    if dist > 1:
                        events.append({
                            "type": "repair_failed",
                            "unit_id": u_id,
                            "reason": f"Target unit out of repair range ({dist} > 1)"
                        })
                        continue

                    repaired = target.heal(ENGINEER_REPAIR_AMOUNT)
                    engineer.last_action = {"action": "repair", "target_id": target_id, "amount": repaired}
                    events.append({
                        "type": "unit_repaired",
                        "engineer_id": u_id,
                        "target_id": target.id,
                        "amount": repaired,
                        "current_hp": target.hp
                    })

                elif target_type == "structure":
                    struct_key = str(target_id)
                    target_struct = game_state.structures.get(struct_key)
                    if not target_struct or not target_struct.alive or target_struct.team != engineer.team:
                        events.append({
                            "type": "repair_failed",
                            "unit_id": u_id,
                            "reason": "Target structure invalid, destroyed, or not friendly"
                        })
                        continue

                    dist = max(abs(engineer.x - target_struct.x), abs(engineer.y - target_struct.y))
                    if dist > 1:
                        events.append({
                            "type": "repair_failed",
                            "unit_id": u_id,
                            "reason": f"Target structure out of repair range ({dist} > 1)"
                        })
                        continue

                    heal_amt = min(target_struct.max_hp - target_struct.hp, ENGINEER_REPAIR_AMOUNT)
                    target_struct.hp += heal_amt
                    engineer.last_action = {"action": "repair", "target_id": struct_key, "amount": heal_amt}
                    events.append({
                        "type": "structure_repaired",
                        "engineer_id": u_id,
                        "structure_id": struct_key,
                        "amount": heal_amt,
                        "current_hp": target_struct.hp
                    })

        return events

    @staticmethod
    def resolve_control_zones(game_state) -> List[Dict[str, Any]]:
        """
        Updates neutral control zone capture progress and awards territory points.
        """
        events = []
        for zone in game_state.game_map.control_zones.values():
            blue_presence = 0
            red_presence = 0

            for unit in game_state.units.values():
                if not unit.alive:
                    continue
                d = max(abs(unit.x - zone.x), abs(unit.y - zone.y))
                if d <= zone.radius:
                    if unit.team == "blue":
                        blue_presence += 1
                    elif unit.team == "red":
                        red_presence += 1

            if blue_presence > 0 and red_presence == 0:
                contender = "blue"
            elif red_presence > 0 and blue_presence == 0:
                contender = "red"
            else:
                contender = None # Contested or empty

            if contender:
                if zone.owner == contender:
                    zone.progress = CONTROL_ZONE_CAPTURE_THRESHOLD
                else:
                    if zone.contender == contender:
                        zone.progress += 1
                        if zone.progress >= CONTROL_ZONE_CAPTURE_THRESHOLD:
                            zone.owner = contender
                            events.append({
                                "type": "zone_captured",
                                "zone_id": zone.id,
                                "team": contender
                            })
                    else:
                        zone.contender = contender
                        zone.progress = 1
            else:
                # Contested or empty: decays slowly
                if zone.progress > 0 and not zone.owner:
                    zone.progress -= 1

            # Award territory points if owned
            if zone.owner:
                game_state.stats[zone.owner]["control_points"] += CONTROL_ZONE_POINTS_PER_TURN
                game_state.stats[zone.owner]["territory_turns"] += 1
                events.append({
                    "type": "zone_points_awarded",
                    "zone_id": zone.id,
                    "team": zone.owner,
                    "points": CONTROL_ZONE_POINTS_PER_TURN
                })

        return events

