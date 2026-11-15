"""
Movement resolution system for PROXY BOT WARS.
Handles step constraints, boundary checks, obstacle collisions, and deterministic resolution.
"""
from typing import Dict, List, Tuple, Any, Optional

class MovementSystem:
    @staticmethod
    def resolve_movement(game_state, moves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolves a list of move action requests deterministically.
        moves: [{'unit_id': int, 'dx': int, 'dy': int, 'team': str}]
        Returns movement events for logging and visualizer animation.
        """
        events = []
        # Current unit positions
        unit_positions = {u.id: (u.x, u.y) for u in game_state.units.values() if u.alive}
        occupied_cells = set(unit_positions.values())

        # Base and structure positions also block unit movement
        for struct in game_state.structures.values():
            if struct.alive:
                occupied_cells.add((struct.x, struct.y))

        # Proposed new positions: {unit_id: (target_x, target_y)}
        proposed: Dict[int, Tuple[int, int]] = {}

        for move in moves:
            u_id = move["unit_id"]
            unit = game_state.units.get(u_id)
            if not unit or not unit.alive:
                continue

            dx = move.get("dx", 0)
            dy = move.get("dy", 0)

            # Check speed limit (Chebyshev distance: max(|dx|, |dy|) <= speed)
            dist = max(abs(dx), abs(dy))
            if dist == 0:
                continue
            if dist > unit.speed:
                # Clamp or reject; per spec reject illegal actions safely
                events.append({
                    "type": "move_failed",
                    "unit_id": u_id,
                    "reason": f"Distance {dist} exceeds unit speed {unit.speed}"
                })
                continue

            target_x = unit.x + dx
            target_y = unit.y + dy

            # Check map boundary
            if not game_state.game_map.is_in_bounds(target_x, target_y):
                events.append({
                    "type": "move_failed",
                    "unit_id": u_id,
                    "reason": "Target cell out of map bounds"
                })
                continue

            # Check obstacles
            if (target_x, target_y) in game_state.game_map.obstacles:
                events.append({
                    "type": "move_failed",
                    "unit_id": u_id,
                    "reason": "Target cell blocked by obstacle"
                })
                continue

            # Check non-passable structures (e.g. enemy bases, barricades)
            blocking_struct = None
            for s in game_state.structures.values():
                if s.alive and s.x == target_x and s.y == target_y:
                    blocking_struct = s
                    break
            if blocking_struct:
                events.append({
                    "type": "move_failed",
                    "unit_id": u_id,
                    "reason": f"Target cell blocked by structure {blocking_struct.structure_type}"
                })
                continue

            proposed[u_id] = (target_x, target_y)

        # Conflict resolution for cells targeted by multiple units simultaneously
        target_claims: Dict[Tuple[int, int], List[int]] = {}
        for u_id, tgt in proposed.items():
            target_claims.setdefault(tgt, []).append(u_id)

        # Cells that have collisions: all claiming units bounce back safely
        valid_moves: Dict[int, Tuple[int, int]] = {}
        for tgt, claimants in target_claims.items():
            if len(claimants) > 1:
                for c_id in claimants:
                    events.append({
                        "type": "move_collision",
                        "unit_id": c_id,
                        "target": tgt,
                        "reason": "Simultaneous movement collision with other units"
                    })
            else:
                valid_moves[claimants[0]] = tgt

        # Also check if destination is currently occupied by a unit that is not moving away
        final_moves: Dict[int, Tuple[int, int]] = {}
        for u_id, tgt in valid_moves.items():
            # Check if tgt is occupied by another unit that isn't moving
            occupant_id = None
            for other_id, pos in unit_positions.items():
                if other_id != u_id and pos == tgt:
                    occupant_id = other_id
                    break

            if occupant_id is not None and occupant_id not in valid_moves:
                events.append({
                    "type": "move_blocked",
                    "unit_id": u_id,
                    "target": tgt,
                    "reason": f"Target cell occupied by stationary unit {occupant_id}"
                })
            else:
                final_moves[u_id] = tgt

        # Apply final movements
        for u_id, (nx, ny) in final_moves.items():
            unit = game_state.units[u_id]
            from_x, from_y = unit.x, unit.y
            unit.x = nx
            unit.y = ny
            unit.last_action = {"action": "move", "from": [from_x, from_y], "to": [nx, ny]}
            events.append({
                "type": "unit_moved",
                "unit_id": u_id,
                "team": unit.team,
                "from": [from_x, from_y],
                "to": [nx, ny]
            })

        return events

