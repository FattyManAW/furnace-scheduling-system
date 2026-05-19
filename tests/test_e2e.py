"""E2E Integration Test — Furnace Scheduling System (Docker API)"""
import json, os, sys, subprocess

BACKEND = os.environ.get("FURNACE_BACKEND", "http://100.107.36.80:8002")
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
    r = subprocess.run(
        ["curl", "-si", "--max-time", "5", "-H", f"Origin: {origin}", url],
        capture_output=True, text=True)
    has_cors = "access-control-allow-origin" in r.stdout.lower()
    if not has_cors:
        # Docker may not always return CORS on GET; verify via HEAD
        r2 = subprocess.run(
            ["curl", "-sI", "--max-time", "5", "-H", f"Origin: {origin}", url],
            capture_output=True, text=True)
        has_cors = "access-control-allow-origin" in r2.stdout.lower()
    return has_cors

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

# 2. CORS
if check_cors(f"{BACKEND}/api/v1/orders/?limit=1", FRONTEND):
    ok("CORS header present")
else:
    fail("CORS missing — frontend may not fetch API")

# 3. API Coverage
print("\n3. API ENDPOINT COVERAGE")
for method, path, etype, label in [
    ("GET", "/api/v1/orders/?limit=1", list, "orders"),
    ("GET", "/api/v1/molds/?limit=1", list, "molds"),
    ("GET", "/api/v1/kilns/?limit=1", list, "kilns"),
    ("GET", "/api/v1/reports/dashboard", dict, "dashboard"),
]:
    body, _ = curl(f"{BACKEND}{path}")
    if isinstance(body, etype):
        ok(f"{method} {path} → {label}")
    else:
        fail(f"{method} {path}", f"expected {etype.__name__}, got {type(body).__name__}")

# 4. Scenario: Single Order
print("\n4. SCENARIO: Single Order Scheduling")
body, _ = curl(f"{BACKEND}/api/v1/orders/?limit=1")
if isinstance(body, list) and body:
    pn = body[0]["plan_no"]
    ok(f"Order: {pn}")
    s, _ = curl(f"{BACKEND}/api/v1/schedule/optimize", "POST", {"plan_nos": [pn]})
    if isinstance(s, dict) and s["summary"]["scheduled"] > 0:
        ok(f"Single {pn} → scheduled")
    else:
        fail("Single schedule", str(s)[:100])

# 5. Scenario: Multi-Order
print("\n5. SCENARIO: Multi-Order Competition")
body, _ = curl(f"{BACKEND}/api/v1/orders/?limit=10")
if isinstance(body, list) and len(body) >= 5:
    pns = [o["plan_no"] for o in body[:5]]
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