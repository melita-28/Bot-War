# PROXY BOT WARS - Official Tournament Rules & Mechanics

## 1. Grid & Coordinates
- Grid: 30 × 30 cells. Coordinate origin `(0, 0)` is top-left, `(29, 29)` is bottom-right.
- Distance metric: Chebyshev distance `max(|x1 - x2|, |y1 - y2|)` allowing 8-directional tactical movement.

## 2. Bases & Economy
- Blue Base: `(3, 3)`
- Red Base: `(26, 26)`
- Base HP: 500, Attack: 15, Range: 2, Vision: 6
- Starting Resources: 100
- Base Passive Income: +5 resources per turn
- Mining Income: Miners collect 10 resources per turn from adjacent deposit (`dist <= 1`).

## 3. Production Costs
- Scout: 30 resources
- Miner: 40 resources
- Soldier: 50 resources
- Engineer: 60 resources
- Tank: 100 resources

## 4. Structures
- **Barricade:** Cost 25, HP 150. Blocks movement.
- **Turret:** Cost 75, HP 120, Attack 15, Range 2. Automatically fires at nearest enemy in range.

## 5. Control Zones
- 3 Symmetrical zones (Center at `(15, 15)`, two flanking zones).
- Capturing requires 3 consecutive uncontested turns with units present in the zone.
- Holding a captured zone awards +2 territory points per turn.

## 6. Execution Constraints
- Timeout: 1.0 second per turn per bot.
- Communication budget: 100 bytes per turn broadcast.
- Sandbox: Standalone subprocess isolation; prohibited system calls or network sockets result in disqualification.

