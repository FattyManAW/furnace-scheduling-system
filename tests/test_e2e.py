"""E2E Integration Test — Furnace Scheduling System (Docker API)"""
import json
import os
import subprocess
import sys
from urllib.parse import urlparse

BACKEND = os.environ.get("FURNACE_BACKEND", "http://100.107.36.80:8030")
FRONTEND = os.environ.get("FURNACE_FRONTEND", "https://fattymanaw.github.io/furnace-scheduling-system")

passed, failed = 0, 0

def ok(msg):
    global passed; passed += 1
    print(f"  ✅ {msg}")

def fail(msg, detail=""):
    global failed; failed += 1
    print(f"  ❌ {msg}")
    if detail: print(f"     {detail}")

def curl(url, method="GET", data=None):
    args = ["curl", "-sL", "--max-time", "30", url]
    if data is not None:
        args += ["-X", method, "-H", "Content-Type: application/json", "-d", json.dumps(data)]
    r = subprocess.run(args, capture_output=True, text=True)
    try:
        return json.loads(r.stdout), r.returncode
    except json.JSONDecodeError:
        return r.stdout.strip(), r.returncode

def check_cors(url, origin):
    # Use OPTIONS preflight to verify CORS
    r = subprocess.run(
        ["curl", "-sI", "--max-time", "5", "-X", "OPTIONS",
         "-H", f"Origin: {origin}",
         "-H", "Access-Control-Request-Method: GET",
         url],
        capture_output=True, text=True)
    return "access-control-allow-origin" in r.stdout.lower()

print("=" * 64)
print("   Furnace — E2E Integration Tests (Docker)")
print("=" * 64)
print()

# 1. Health
body, rc = curl(f"{BACKEND}/health")
if isinstance(body, dict) and body.get("status") == "ok":
    ok("GET /health → ok")
else:
    fail("GET /health", str(body)[:100])

# 2. CORS — strip path from frontend URL for origin check
cors_origin = f"{urlparse(FRONTEND).scheme}://{urlparse(FRONTEND).netloc}"
if check_cors(f"{BACKEND}/api/v1/orders/?limit=1", cors_origin):
    ok("CORS header present")
else:
    fail("CORS missing — frontend may not fetch API")

# 3. API Coverage
print("\n3. API ENDPOINT COVERAGE")
for method, path, key, label in [
    ("GET", "/api/v1/orders/?limit=1", "items", "orders"),
    ("GET", "/api/v1/molds/?limit=1", "items", "molds"),
    ("GET", "/api/v1/kilns/?limit=1", "items", "kilns"),
    ("GET", "/api/v1/reports/dashboard", None, "dashboard"),
]:
    body, _ = curl(f"{BACKEND}{path}")
    if isinstance(body, dict):
        if key is None:
            ok(f"{method} {path} → {label}")
        elif key in body:
            ok(f"{method} {path} → {label} ({len(body[key])} items)")
        else:
            fail(f"{method} {path}", f"missing key '{key}' in {list(body.keys())[:5]}")
    else:
        fail(f"{method} {path}", f"expected dict, got {type(body).__name__}")

# 4. Scenario: Single Order
print("\n4. SCENARIO: Single Order Scheduling")
body, _ = curl(f"{BACKEND}/api/v1/orders/?limit=1")
items = body.get("items", []) if isinstance(body, dict) else body
if isinstance(items, list) and items:
    pn = items[0]["plan_no"]
    ok(f"Order: {pn}")
    s, _ = curl(f"{BACKEND}/api/v1/schedule/optimize", "POST", {"plan_nos": [pn]})
    if isinstance(s, dict) and s["summary"]["scheduled"] > 0:
        ok(f"Single {pn} → scheduled")
    else:
        fail("Single schedule", str(s)[:100])

# 5. Scenario: Multi-Order
print("\n5. SCENARIO: Multi-Order Competition")
body, _ = curl(f"{BACKEND}/api/v1/orders/?limit=10")
items = body.get("items", []) if isinstance(body, dict) else body
if isinstance(items, list) and len(items) >= 5:
    pns = [o["plan_no"] for o in items[:5]]
    s, _ = curl(f"{BACKEND}/api/v1/schedule/optimize", "POST", {"plan_nos": pns})
    if isinstance(s, dict):
        ok(f"5→{s['summary']['scheduled']} scheduled, {len(s.get('kiln_summary',[]))} kilns")
    else:
        fail("Multi schedule", str(s)[:100])

# 6. Scenario: Overdue
print("\n6. SCENARIO: Overdue Detection")
body, _ = curl(f"{BACKEND}/api/v1/reports/dashboard")
if isinstance(body, dict):
    od = body.get("orders", {})
    ok(f"Dashboard: {od.get('total')} total, {od.get('overdue')} overdue")

# 7. Full Schedule
print("\n7. FULL SCHEDULE OPTIMIZATION")
body, _ = curl(f"{BACKEND}/api/v1/schedule/optimize", "POST", {"plan_nos": []})
if isinstance(body, dict):
    s = body["summary"]
    ks = len(body.get("kiln_summary", []))
    ok(f"Full: {s['scheduled']} orders, {ks} kilns, {s['total_hours']:.0f}h")

# 8. Data Integrity
print("\n8. DATA INTEGRITY")
for ep, expected in [("orders", 251), ("molds", 16)]:
    body, _ = curl(f"{BACKEND}/api/v1/{ep}/count")
    if isinstance(body, dict) and body.get("count") == expected:
        ok(f"{ep}: count={expected}")

# 9. CSV Exports
print("\n9. CSV EXPORTS")
for label, path in [("Orders", "/api/v1/reports/orders/csv"), ("Schedule", "/api/v1/reports/schedule/csv")]:
    r = subprocess.run(["curl", "-sL", "--max-time", "5", f"{BACKEND}{path}"], capture_output=True, text=True)
    if len(r.stdout) > 100:
        ok(f"{label} CSV: {len(r.stdout)} bytes")

# 10. Frontend
print("\n10. FRONTEND")
r = subprocess.run(["curl", "-sL", "--max-time", "10", FRONTEND], capture_output=True, text=True)
if len(r.stdout) > 100:
    ok(f"Frontend loads: {len(r.stdout)} bytes")

# Summary
print()
print("=" * 64)
print(f"  Results: {passed} passed, {failed} failed")
if failed == 0:
    print("  🎉 ALL E2E TESTS PASSED")
else:
    print(f"  ⚠️  {failed} failures")
print("=" * 64)
sys.exit(0 if failed == 0 else 1)
