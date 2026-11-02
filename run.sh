#!/bin/bash
# Convenience script to run automation with correct environment

cd "$(dirname "$0")"
source venv/bin/activate
python scripts/run_automation.py
