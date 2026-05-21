"""
oven_scheduler/seed.py
Import Excel data into SQLite database.
"""
import json
import os

from sqlalchemy.orm import Session

from data_loader import (
    load_all,
)
from database import (
    Base,
    Dryer,
    DryerPlan,
    MoldType,
    Order,
    ProcessStep,
    ProductSpec,
)


def seed_dryers(session: Session, dryers: list):
    for d_data in dryers:
        dryer = Dryer(
            name=d_data["name"],
            inner_diameter=d_data["inner_d"],
            height=d_data["height"],
        )
        session.add(dryer)
        session.flush()
        for p_data in d_data.get("plans", []):
            plan = DryerPlan(
                dryer_id=dryer.id,
                plan_label=p_data["plan"],
                upper_qty=p_data["upper"]["qty"],
                upper_od=p_data["upper"]["od"],
                upper_id=p_data["upper"]["id"],
                upper_length=p_data["upper"]["length"],
                lower_qty=p_data["lower"]["qty"],
                lower_od=p_data["lower"]["od"],
                lower_id=p_data["lower"]["id"],
                lower_length=p_data["lower"]["length"],
            )
            session.add(plan)


def seed_molds(session: Session, molds: list):
    for m in molds:
        mt = MoldType(
            outer_diameter=m["od"],
            inner_diameter=m["id_inner"],
            length=m["length"],
            quantity=m["qty"],
        )
        session.add(mt)


def seed_products(session: Session, products: dict):
    for (kv, amp), p in products.items():
        label = f"{kv}kV/{amp}A"
        ps = ProductSpec(
            voltage_kv=kv,
            current_a=amp,
            mold_od=p["mold_od"],
            mold_id=p["mold_id"],
            mold_length=p["mold_length"],
            units_per_bundle=p["units_per_bundle"],
            label=label,
        )
        session.add(ps)


def seed_process_steps(session: Session, steps: list):
    for i, s in enumerate(steps):
        ps = ProcessStep(
            step_name=s["step"],
            flow=s.get("flow", ""),
            sub_flow=s.get("sub", ""),
            calc_method=s.get("calc", ""),
            per_voltage_hours=json.dumps(s.get("per_voltage_h", {})),
            sort_order=i,
        )
        session.add(ps)


def seed_orders(session: Session, orders: list):
    for o in orders:
        orm_order = Order(
            order_id=o["order_id"],
            contract_no=o.get("contract", ""),
            voltage_kv=o["voltage_kv"],
            current_a=o["current_a"],
            unit=o.get("unit", ""),
            quantity=o["qty"],
            delivery_date=o["delivery_date"],
            product_start=o.get("product_start", 0),
            product_end=o.get("product_end", 0),
        )
        session.add(orm_order)


def run(engine):
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Check if already seeded
    if session.query(Dryer).count() > 0:
        print("Database already seeded. Skipping.")
        return

    data = load_all()
    seed_dryers(session, data["dryers"])
    seed_molds(session, data["mold_inventory"])
    seed_products(session, data["products"])
    seed_process_steps(session, data["process_steps"])
    seed_orders(session, data["orders"])

    session.commit()
    print(f"Seeded: {session.query(Dryer).count()} dryers, "
          f"{session.query(DryerPlan).count()} plans, "
          f"{session.query(MoldType).count()} mold types, "
          f"{session.query(ProductSpec).count()} products, "
          f"{session.query(ProcessStep).count()} steps, "
          f"{session.query(Order).count()} orders")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    run(engine)
    print(f"DB: {db_path}")
