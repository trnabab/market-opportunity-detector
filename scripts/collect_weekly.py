#!/usr/bin/env python3
"""
Weekly data collection script.

Run this weekly to collect historical data
for future ML training.

Usage:
    python scripts/collect_weekly.py

Cron example (every Sunday at 9am):
    0 9 * * 0 cd /path/to/project && python scripts/collect_weekly.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pipeline.orchestrator import run_pipeline


if __name__ == "__main__":
    run_pipeline()
