# Security & Execution Isolation Model - PROXY BOT WARS

Autonomous programming competitions require strict isolation so participant code cannot interfere with other bots, crash the central simulator, tamper with the file system, or leak private game states.

---

## 1. Threat Model & Safeguards

| Threat Vector | Mitigation Strategy | Implementation |
| :--- | :--- | :--- |
| **Infinite Loops / Slow Code** | Strict 1.0s turn execution timeout. | `BotProcessClient` uses a threaded watchdog timer to terminate stuck processes and award empty actions for that turn. |
| **Bot Crash / Unhandled Exception** | Process error containment. | Subprocess crash does not terminate the engine. Stderr is captured, a warning logged, and match proceeds. |
| **Memory / CPU Starvation** | Safe subprocess invocation. | Separate Python processes with isolated heaps and stripped environment variables. |
| **Tampering with Opponent / State** | Complete memory decoupling. | Bots communicate purely over STDIN / STDOUT JSON streams. Engine internal objects are never accessible. |
| **Information Cheating (Map Hacking)** | Server-side Fog of War. | The engine masks the observation dictionary before writing to STDIN; hidden enemies are physically absent from the JSON. |
| **Malicious System Calls** | AST Security Validator & Module Restrictions. | AST scan rejects or flags prohibited imports (`subprocess`, `ctypes`, `socket`, `shutil`, `urllib`). |

---

## 2. Docker Execution Isolation (Optional Production Sandbox)

For air-gapped production deployment with hard Linux kernel namespace isolation, participant submissions can be executed inside ephemeral Docker containers:
```bash
docker run --rm \
  --network none \
  --memory 256m \
  --cpus 1.0 \
  --read-only \
  -v /submissions/team1.py:/app/bot.py:ro \
  python:3.11-slim python -u /app/bot.py
```

---

## 3. Safe Reviewed-Submission Fallback

When operating in environments where Docker is unavailable (such as local Windows workstations during student labs), PROXY BOT WARS uses the **Safe Reviewed-Submission Model**:
1. All submissions are run through `SubmissionValidator.validate_file()` which performs AST import tree inspection.
2. Bots execute in non-elevated subprocesses with sanitized environment variables (`SYSTEMROOT`, `PATH`, `PYTHONPATH`).
3. Outbound network sockets and shell executions are prohibited by competition rules.

