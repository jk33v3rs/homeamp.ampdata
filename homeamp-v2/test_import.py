#!/usr/bin/env python3
"""Test imports to diagnose startup issues."""

import sys
import traceback

print("Testing imports...")
print(f"Python: {sys.version}")
print(f"Path: {sys.path}\n")

try:
    print("1. Testing homeamp_v2 base import...")
    import homeamp_v2
    print(f"   ✓ Success: {homeamp_v2.__file__}\n")
except Exception as e:
    print(f"   ✗ Failed: {e}\n")
    traceback.print_exc()
    sys.exit(1)

try:
    print("2. Testing homeamp_v2.api.main import...")
    from homeamp_v2.api.main import create_app
    print(f"   ✓ Success\n")
except Exception as e:
    print(f"   ✗ Failed: {e}\n")
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Creating FastAPI app...")
    app = create_app()
    print(f"   ✓ Success: {app.title}\n")
except Exception as e:
    print(f"   ✗ Failed: {e}\n")
    traceback.print_exc()
    sys.exit(1)

print("All imports successful!")
print("\nStarting test server on http://0.0.0.0:8077...")

import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8077, log_level="info")
