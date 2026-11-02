#!/bin/bash
# Convenience script to start dashboard

cd "$(dirname "$0")"
source venv/bin/activate
streamlit run src/dashboard.py
