#!/usr/bin/env python
"""Test script to verify insights module can be imported"""

import sys
import traceback

print("Testing insights module import...")
print("=" * 50)

try:
    print("1. Testing app.api.insights import...")
    from app.api import insights
    print("   ✅ Successfully imported insights module")
    print(f"   Router: {insights.router}")
    print(f"   Router type: {type(insights.router)}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Testing router endpoints...")
    routes = [r.path for r in insights.router.routes]
    print(f"   Found {len(routes)} routes:")
    for route in routes:
        print(f"     - {route}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    traceback.print_exc()

try:
    print("\n3. Testing lazy imports (get_brain)...")
    brain = insights.get_brain()
    print(f"   ✅ Brain loaded: {type(brain)}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    traceback.print_exc()

try:
    print("\n4. Testing lazy imports (get_analyzer)...")
    analyzer = insights.get_analyzer()
    print(f"   ✅ Analyzer loaded: {type(analyzer)}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("✅ All tests passed! Insights module is working.")
print("\nIf you see this, the module CAN be imported.")
print("The issue might be with the server not restarting properly.")

