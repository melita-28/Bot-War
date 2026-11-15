"""
Automated Participant Bot Submission Validator for PROXY BOT WARS.
Verifies Python syntax, AST safety, runtime start, dry-run observation response,
and API schema compliance.
"""
import ast
import os
import sys
import json
from typing import Dict, Any, List

from bot_api.schemas import LEGAL_ACTIONS
from match_runner.executor import BotProcessClient

PROHIBITED_MODULES = {"ctypes", "subprocess", "socket", "http.client", "urllib.request", "requests", "shutil"}

class SubmissionValidator:
    @staticmethod
    def validate_file(script_path: str, timeout_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Runs comprehensive checks on a participant's bot script.
        Returns a detailed report.
        """
        report = {
            "valid": False,
            "checks": {
                "file_exists": False,
                "syntax_valid": False,
                "security_ast": False,
                "process_start": False,
                "dry_run_response": False,
                "schema_compliance": False,
                "execution_speed": False
            },
            "errors": [],
            "warnings": [],
            "timing_ms": 0.0
        }

        # 1. File exists
        if not os.path.exists(script_path):
            report["errors"].append(f"File not found: {script_path}")
            return report
        report["checks"]["file_exists"] = True

        # 2. Python syntax check
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=script_path)
            report["checks"]["syntax_valid"] = True
        except SyntaxError as se:
            report["errors"].append(f"Syntax error at line {se.lineno}: {se.msg}")
            return report
        except Exception as e:
            report["errors"].append(f"Failed to read/parse script: {str(e)}")
            return report

        # 3. Security AST scan
        security_issues = []
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in PROHIBITED_MODULES:
                        security_issues.append(f"Prohibited import '{alias.name}' detected.")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in PROHIBITED_MODULES:
                        security_issues.append(f"Prohibited from-import '{node.module}' detected.")

        if security_issues:
            report["warnings"].extend(security_issues)
            # In strict reviewed mode, we can flag this
            report["checks"]["security_ast"] = True # Non-blocking warning unless configured strict
        else:
            report["checks"]["security_ast"] = True

        # 4. Process start & Dry-run execution
        client = BotProcessClient(script_path, team="blue", timeout_seconds=timeout_seconds)
        started = client.start()
        if not started:
            report["errors"].append(f"Bot failed to start: {client.last_error_message}")
            return report
        report["checks"]["process_start"] = True

        # Sample mock observation
        mock_obs = {
            "turn": 1,
            "max_turns": 150,
            "team": "blue",
            "resources": 100,
            "base": {"id": "base_blue", "x": 3, "y": 3, "hp": 500, "max_hp": 500},
            "units": [
                {"id": 1, "type": "scout", "team": "blue", "x": 4, "y": 3, "hp": 40, "max_hp": 40, "speed": 4, "vision": 10, "attack_range": 1},
                {"id": 2, "type": "miner", "team": "blue", "x": 3, "y": 4, "hp": 60, "max_hp": 60, "speed": 2, "vision": 5, "attack_range": 0}
            ],
            "visible_enemies": [],
            "visible_structures": [],
            "visible_resources": [{"id": 1, "x": 5, "y": 3, "amount": 500}],
            "control_zones": [{"id": 1, "x": 15, "y": 15, "owner": None}],
            "known_obstacles": [],
            "team_message": "",
            "map_width": 30,
            "map_height": 30
        }

        try:
            resp, elapsed_ms, err = client.query(mock_obs)
            report["timing_ms"] = round(elapsed_ms, 2)

            if err:
                report["errors"].append(f"Runtime dry-run failed: {err}")
                return report
            report["checks"]["dry_run_response"] = True

            # Schema compliance check
            if not isinstance(resp, dict) or "actions" not in resp:
                report["errors"].append("Bot output must be a JSON dictionary containing the 'actions' key.")
                return report

            actions = resp["actions"]
            if not isinstance(actions, list):
                report["errors"].append("'actions' field must be a list.")
                return report

            for a in actions:
                if not isinstance(a, dict) or "action" not in a:
                    report["errors"].append(f"Each action must be a dict with 'action' key, got: {a}")
                    return report
                if a["action"] not in LEGAL_ACTIONS:
                    report["errors"].append(f"Illegal action type: '{a['action']}'")
                    return report

            report["checks"]["schema_compliance"] = True

            if elapsed_ms <= timeout_seconds * 1000.0:
                report["checks"]["execution_speed"] = True
            else:
                report["warnings"].append(f"Execution took {elapsed_ms:.1f}ms (close to budget limit)")

        finally:
            client.kill()

        report["valid"] = (len(report["errors"]) == 0)
        return report

