"""從 JSON 假資料匯入初始資料到 SQLite 資料庫"""
import json, os, sys
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import Order, Mold, Kiln, ProcessStep
from date_utils import excel_to_date

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ 資料表建立完成")


def seed_orders(db: Session) -> int:
    with open(os.path.join(DATA_DIR, "orders.json")) as f:
        raw = json.load(f)
    count = 0
    for od in raw:
        po = str(od.get("plan_no", ""))
        if not po:
            continue
        existing = db.query(Order).filter(Order.plan_no == po).first()
        if existing:
            continue
        db.add(Order(
            plan_no=po,
            contract_no=str(od.get("contract_no", "") or ""),
            voltage_kv=float(od.get("voltage_kv", 0) or 0),
            current_a=float(od.get("current_a", 0) or 0),
            qty=int(float(od.get("qty", 0) or 0)),
            delivery_date=excel_to_date(od.get("delivery_date", "")),
            product_from=str(od.get("product_from", "") or ""),
            product_to=str(od.get("product_to", "") or ""),
            status="pending",
        ))
        count += 1
    db.commit()
    print(f"✅ 匯入訂單: {count} 筆")
    return count


def seed_molds(db: Session) -> int:
    with open(os.path.join(DATA_DIR, "molds.json")) as f:
        raw = json.load(f)
    count = 0
    for mk, md in raw.items():
        existing = db.query(Mold).filter(Mold.mold_no == mk).first()
        if existing:
            continue
        db.add(Mold(
            mold_no=mk,
            outer_dia=float(md.get("od", 0) or 0),
            inner_dia=float(md.get("id", 0) or 0),
            length=float(md.get("len", 0) or 0),
            stock_qty=int(md.get("qty", 0) or 0),
        ))
        count += 1
    db.commit()
    print(f"✅ 匯入模具: {count} 筆")
    return count


def seed_kilns(db: Session) -> int:
    with open(os.path.join(DATA_DIR, "kilns.json")) as f:
        raw = json.load(f)
    count = 0
    for kk, kd in raw.items():
        existing = db.query(Kiln).filter(Kiln.kiln_no == kk).first()
        if existing:
            continue
        db.add(Kiln(
            kiln_no=kk,
            name=kd.get("name", ""),
            inner_dia=float(kd.get("inner_dia", 0) or 0),
            height=float(kd.get("height", 0) or 0),
            schemes_json=json.dumps(kd.get("schemes", {})),
        ))
        count += 1
    db.commit()
    print(f"✅ 匯入干燥罐: {count} 筆")
    return count


def seed_processes(db: Session) -> int:
    with open(os.path.join(DATA_DIR, "processes.json")) as f:
        raw = json.load(f)
    count = 0
    for rd in raw:
        step = rd.get("step", "")
        if not step:
            continue
        db.add(ProcessStep(
            step_no=count + 1,
            step_name=step,
            department=rd.get("dept", ""),
            team=rd.get("team", ""),
            process_type=rd.get("process", ""),
            calc_basis=rd.get("calc", ""),
            h10=float(rd.get("h10", 0) or 0),
            h24=float(rd.get("h24", 0) or 0),
            h36=float(rd.get("h36", 0) or 0),
            h40=float(rd.get("h40", 0) or 0),
        ))
        count += 1
    db.commit()
    print(f"✅ 匯入製程: {count} 筆")
    return count


def seed_all():
    init_db()
    db = SessionLocal()
    try:
        seed_orders(db)
        seed_molds(db)
        seed_kilns(db)
        seed_processes(db)
    finally:
        db.close()
    print("\n🎉 所有初始資料匯入完成！")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        seed_all()
    else:
        init_db()
        print("使用 --init 參數執行完整匯入")
