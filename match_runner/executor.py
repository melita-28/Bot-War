"""
Subprocess bot executor with timeout enforcement, error isolation, and safety checks.
"""
import subprocess
import sys
import os
import json
import time
from typing import Dict, Any, Optional, Tuple

class BotProcessClient:
    """Manages an active external bot process over standard input/output."""

    def __init__(self, script_path: str, team: str, timeout_seconds: float = 1.0):
        self.script_path = os.path.abspath(script_path)
        self.team = team
        self.timeout_seconds = timeout_seconds
        self.process: Optional[subprocess.Popen] = None
        self.is_alive = False
        self.total_errors = 0
        self.last_error_message: Optional[str] = None

    def start(self) -> bool:
        """Starts the bot subprocess in unbuffered mode."""
        if not os.path.exists(self.script_path):
            self.last_error_message = f"Bot script not found: {self.script_path}"
            return False

        try:
            # Run with python -u (unbuffered binary stdout and stderr)
            cmd = [sys.executable, "-u", self.script_path]
            # Restrict environment variables to avoid passing sensitive host keys
            safe_env = {
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.path.abspath(os.getcwd())
            }
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=safe_env
            )
            self.is_alive = True
            return True
        except Exception as e:
            self.is_alive = False
            self.last_error_message = f"Failed to start bot process: {str(e)}"
            return False

    def query(self, observation: Dict[str, Any]) -> Tuple[Dict[str, Any], float, Optional[str]]:
        """
        Sends observation JSON line to bot stdin, waits for response line with timeout.
        Returns (response_dict, execution_time_ms, error_message)
        """
        if not self.is_alive or self.process is None or self.process.poll() is not None:
            return {"actions": []}, 0.0, "Bot process is not running"

        start_time = time.perf_counter()
        error_msg = None
        response_dict = {"actions": []}

        try:
            # Send observation
            obs_json = json.dumps(observation) + "\n"
            self.process.stdin.write(obs_json)
            self.process.stdin.flush()

            # Read response with timeout
            # Using readline()
            # On Windows/Python, standard subprocess readline with timeout can be done via threading or selector
            import threading
            line_box = []
            exc_box = []

            def reader():
                try:
                    line = self.process.stdout.readline()
                    line_box.append(line)
                except Exception as ex:
                    exc_box.append(ex)

            th = threading.Thread(target=reader, daemon=True)
            th.start()
            th.join(timeout=self.timeout_seconds)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if th.is_alive():
                # Timeout occurred!
                self.total_errors += 1
                error_msg = f"Bot timed out (> {self.timeout_seconds}s)"
                self.last_error_message = error_msg
                # Restart or terminate stuck process
                self.kill()
                self.start() # Attempt recovery for next turn
                return {"actions": []}, elapsed_ms, error_msg

            if exc_box:
                self.total_errors += 1
                error_msg = f"Reader error: {str(exc_box[0])}"
                return {"actions": []}, elapsed_ms, error_msg

            if not line_box or not line_box[0].strip():
                # Process produced empty output or terminated
                stderr_output = ""
                if self.process.stderr:
                    try:
                        stderr_output = self.process.stderr.read()
                    except Exception:
                        pass
                self.total_errors += 1
                error_msg = f"Empty output or bot crashed. Stderr: {stderr_output.strip()[:200]}"
                self.last_error_message = error_msg
                self.is_alive = False
                return {"actions": []}, elapsed_ms, error_msg

            raw_line = line_box[0].strip()
            response_dict = json.loads(raw_line)
            return response_dict, elapsed_ms, None

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.total_errors += 1
            error_msg = f"Exception communicating with bot: {str(e)}"
            self.last_error_message = error_msg
            return {"actions": []}, elapsed_ms, error_msg

    def kill(self):
        """Terminates the bot process safely."""
        self.is_alive = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=0.5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

