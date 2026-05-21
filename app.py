"""
oven_scheduler/app.py
Flask backend for the Best-Fit Furnace Scheduling System.
"""
import csv
import io
from datetime import datetime

from flask import Flask, jsonify, make_response, render_template, request

from data_loader import load_all, load_orders
from optimizer import _init as opt_init
from optimizer import get_data_summary, get_mold_for_product, schedule

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# ─── Preload data on startup ──────────────────────────────────────────────
_data = load_all()
opt_init()
_PRODUCTS = _data["products"]
_DRYERS = _data["dryers"]
_MOLDS = _data["mold_inventory"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    return jsonify(get_data_summary())


@app.route("/api/products")
def api_products():
    prods = {}
    for (v, a), p in _PRODUCTS.items():
        prods[f"{v}kV/{a}A"] = p
    return jsonify(prods)


@app.route("/api/orders")
def api_orders():
    orders = load_orders()
    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        orders = [o for o in orders if o["delivery_date"] >= start]
    if end:
        orders = [o for o in orders if o["delivery_date"] <= end]
    return jsonify(orders)


@app.route("/api/dryers")
def api_dryers():
    return jsonify(_DRYERS)


@app.route("/api/molds")
def api_molds():
    return jsonify(_MOLDS)


@app.route("/api/process-steps")
def api_process_steps():
    return jsonify(_data["process_steps"])


@app.route("/api/mold-match", methods=["POST"])
def api_mold_match():
    body = request.get_json()
    kv = body.get("voltage_kv", 0)
    amp = body.get("current_a", 0)
    spec = get_mold_for_product(kv, amp)
    return jsonify({"mold_spec": {"od": spec[0], "id": spec[1], "length": spec[2]}} if spec else None)


@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    body = request.get_json() or {}
    order_ids = body.get("order_ids", [])
    selected_furnaces = body.get("furnaces", None)
    all_orders = load_orders()
    orders = all_orders
    if order_ids:
        orders = [o for o in all_orders if o["order_id"] in order_ids]
    orders = [o for o in orders if o.get("qty", 0) > 0]
    result = schedule(orders=orders, selected_furnaces=selected_furnaces)
    for batch in result.get("batches", []):
        for m in batch.get("molds", []):
            kv = m.get("voltage_kv", 0)
            amp = m.get("current_a", 0)
            spec = get_mold_for_product(kv, amp)
            m["mold_spec"] = {"od": spec[0], "id": spec[1], "length": spec[2]} if spec else None
    return jsonify(result)


@app.route("/api/export/csv", methods=["POST"])
def api_export_csv():
    body = request.get_json() or {}
    batches = body.get("batches", [])
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["批次", "乾燥罐", "方案", "模具外徑", "模具內徑", "模具長度", "訂單編號", "電壓kV", "電流A", "數量"])
    for b in batches:
        for m in b.get("molds", []):
            ms = b.get("mold_spec", {})
            w.writerow([
                b["batch_id"], b["furnace"], b["plan"],
                ms.get("od", ""), ms.get("id", ""), ms.get("length", ""),
                m["order_id"], m["voltage_kv"], m["current_a"], m["qty"],
            ])
    resp = make_response(out.getvalue())
    resp.headers["Content-Type"] = "text/csv; charset=utf-8-sig"
    resp.headers["Content-Disposition"] = f'attachment; filename="排爐計劃_{datetime.now().strftime("%Y%m%d")}.csv"'
    return resp


if __name__ == "__main__":
    print(f"Dryers: {len(_DRYERS)} | Products: {len(_PRODUCTS)} | Orders: {len(load_orders())}")
    print("Starting on http://localhost:5555")
    app.run(debug=True, port=5555, use_reloader=False)
