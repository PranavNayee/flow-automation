#!/usr/bin/env python3
"""Test that all new features can be imported."""
import sys

print("Testing imports...")
print("-" * 50)

try:
    from src.recovery_service import GenerationRecoveryService
    print("✅ recovery_service imported")
except Exception as e:
    print(f"❌ recovery_service failed: {e}")
    sys.exit(1)

try:
    from src.notifications import NotificationService
    print("✅ notifications imported")
except Exception as e:
    print(f"❌ notifications failed: {e}")
    sys.exit(1)

try:
    from src.script_writer import ScriptWriter
    from src.utils import Config
    writer = ScriptWriter(Config())
    print(f"✅ script_writer with multi-provider support")
    print(f"   Available providers: {writer.provider_order}")
except Exception as e:
    print(f"❌ script_writer failed: {e}")

try:
    from src.flow_driver import FlowDriver
    print("✅ flow_driver with recovery integration")
except Exception as e:
    print(f"❌ flow_driver failed: {e}")
    sys.exit(1)

print("-" * 50)
print("✅ All imports successful!")
print("")
print("Your system is ready. Next steps:")
print("1. Install FFmpeg: brew install ffmpeg")
print("2. Add LLM key to .env (copy from .env.example)")
print("3. Update selectors.yaml with Flow UI selectors")
print("4. Run: python scripts/test_single_job.py")
