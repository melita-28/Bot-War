#!/usr/bin/env python3
"""
Root entry point to run matches in PROXY BOT WARS.
Usage:
    python run_match.py --blue bots/starter_bot.py --red bots/baseline_bot.py
"""
import sys
from match_runner.runner import main

if __name__ == "__main__":
    main()

