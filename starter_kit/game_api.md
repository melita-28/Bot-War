# PROXY BOT WARS - Bot API Reference

## Observation Schema (JSON sent to bot stdin each turn)

```json
{
  "turn": 10,
  "max_turns": 150,
  "team": "blue",
  "resources": 150,
  "base": {
    "id": "base_blue",
    "x": 3,
    "y": 3,
    "hp": 500,
    "max_hp": 500,
    "attack": 15,
    "attack_range": 2,
    "vision": 6
  },
  "units": [
    {
      "id": 1,
      "type": "scout",
      "team": "blue",
      "x": 5,
      "y": 7,
      "hp": 40,
      "max_hp": 40,
      "attack": 5,
      "speed": 4,
      "vision": 10,
      "attack_range": 1,
      "carried_resources": 0
    }
  ],
  "visible_enemies": [],
  "visible_structures": [],
  "visible_resources": [
    {
      "id": 1,
      "x": 5,
      "y": 3,
      "amount": 480,
      "max_amount": 500
    }
  ],
  "control_zones": [
    {
      "id": 1,
      "x": 15,
      "y": 15,
      "radius": 1,
      "owner": "blue",
      "progress": 3
    }
  ],
  "known_obstacles": [[4, 8], [5, 8]],
  "team_message": "Strategic broadcast from previous turn",
  "map_width": 30,
  "map_height": 30
}
```

---

## Action Output Schema (JSON emitted to stdout by bot)

Your bot prints a single JSON line to stdout:

```json
{
  "actions": [
    {
      "unit_id": 1,
      "action": "move",
      "dx": 1,
      "dy": 0
    },
    {
      "unit_id": 2,
      "action": "gather",
      "deposit_id": 1
    },
    {
      "unit_id": 3,
      "action": "attack",
      "target_id": 102,
      "target_type": "unit"
    },
    {
      "unit_id": 4,
      "action": "build",
      "structure_type": "turret",
      "target_x": 4,
      "target_y": 4
    },
    {
      "unit_id": 4,
      "action": "repair",
      "target_id": 3,
      "target_type": "unit"
    },
    {
      "action": "train",
      "unit_type": "soldier"
    }
  ],
  "message": "Optional broadcast string up to 100 bytes"
}
```

---

## Legal Action List

1. **`move`**: `unit_id`, `dx`, `dy`. Maximum Chebyshev distance `max(|dx|, |dy|) <= speed`.
2. **`attack`**: `unit_id`, `target_id`, `target_type` ("unit" or "structure"). Distance `<= attack_range`.
3. **`gather`**: `unit_id` (Miner only), `deposit_id`. Distance `<= 1` cell.
4. **`build`**: `unit_id` (Engineer only), `structure_type` ("barricade" or "turret"), `target_x`, `target_y` (adjacent empty cell).
5. **`repair`**: `unit_id` (Engineer only), `target_id`, `target_type` (friendly unit or structure).
6. **`train`**: `unit_type` ("scout", "soldier", "tank", "miner", "engineer"). Spawns adjacent to base if resources suffice.
7. **`wait`**: `unit_id`. Unit remains idle.

