#!/usr/bin/env python3

from __future__ import annotations
import os
from typing import Optional
from datetime import datetime
from utils import ask, parse_iso_date, parse_amount, yn, fmt_money
import storage
import reports

BANNER = r"""
==============================
       Expense Tracker
==============================
"""

def ensure_db():
    con = storage.connect()
    storage.init_db(con)
    return con

def menu():
    print(BANNER)
    print("1) Add category")
    print("2) List categories")
    print("3) Add expense")
    print("4) List expenses (with filters)")
    print("5) Monthly summary (per category)")
    print("6) Update expense")
    print("7) Delete expense")
    print("8) Export expenses to CSV")
    print("9) Seed demo data")
    print("0) Exit")

def choose_category(con) -> Optional[int]:
    cats = storage.list_categories(con)
    if not cats:
        print("No categories yet. Add one first.")
        return None
    print("Available categories:")
    for cid, name in cats:
        print(f"  [{cid}] {name}")
    while True:
        raw = ask("Enter category id (or empty for none): ").strip()
        if raw == "":
            return None
        if raw.isdigit():
            cid = int(raw)
            if any(c[0] == cid for c in cats):
                return cid
        print("Invalid category id.")

def action_add_category(con):
    name = ask("Category name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    try:
        storage.add_category(con, name)
        print("Category added.")
    except Exception as e:
        print(f"Error: {e} (maybe the category already exists)")

def action_list_categories(con):
    cats = storage.list_categories(con)
    if not cats:
        print("No categories found.")
        return
    rows = [[cid, name] for cid, name in cats]
    reports.print_table(["ID", "Name"], rows)

def action_add_expense(con):
    date = None
    while not date:
        date = parse_iso_date(ask("Date (YYYY-MM-DD): "))
        if not date:
            print("Invalid date, please try again.")
    amount = None
    while amount is None:
        amount = parse_amount(ask("Amount (e.g., 12.50): "))
        if amount is None:
            print("Invalid amount, must be positive number.")
    desc = ask("Description (optional): ").strip()
    cat_id = choose_category(con)
    eid = storage.add_expense(con, date, amount, desc, cat_id)
    print(f"Expense #{eid} added.")

def action_list_expenses(con):
    df = ask("From date (YYYY-MM-DD) or empty: ").strip()
    dt = ask("To date (YYYY-MM-DD) or empty: ").strip()
    df = parse_iso_date(df) if df else None
    dt = parse_iso_date(dt) if dt else None
    if df is None and dt is None and (df != "" and dt != ""):
        pass  # at least both empty or valid
    cat_prompt = yn("Filter by a category?", False)
    cat_id = choose_category(con) if cat_prompt else None
    rows = storage.list_expenses(con, df, dt, cat_id)
    if not rows:
        print("No expenses found.")
        return
    display = []
    for (eid, date, amt, desc, cat) in rows:
        display.append([eid, date, f"{amt:.2f}", desc, cat])
    reports.print_table(["ID", "Date", "Amount", "Description", "Category"], display)
    print(f"Total items: {len(rows)} | Sum: {fmt_money(sum(float(r[2]) for r in display))}")

def action_monthly_summary(con):
    # Ask year and month
    while True:
        raw_y = ask("Year (e.g., 2025): ").strip()
        if raw_y.isdigit() and 1900 <= int(raw_y) <= 9999:
            year = int(raw_y)
            break
        print("Invalid year.")
    while True:
        raw_m = ask("Month (1-12): ").strip()
        if raw_m.isdigit() and 1 <= int(raw_m) <= 12:
            month = int(raw_m)
            break
        print("Invalid month.")
    totals = storage.monthly_totals_by_category(con, year, month)
    if not totals:
        print("No data for that period.")
        return
    reports.print_monthly_summary(totals)

def action_update_expense(con):
    raw_id = ask("Expense ID to update: ").strip()
    if not raw_id.isdigit():
        print("Invalid id.")
        return
    eid = int(raw_id)
    print("Leave a field empty to keep current value.")
    date = ask("New date (YYYY-MM-DD): ").strip()
    date = parse_iso_date(date) if date else None
    amount = ask("New amount: ").strip()
    amount = parse_amount(amount) if amount else None
    desc = ask("New description: ").strip()
    if desc == "":
        desc = None  # keep current
    change_cat = yn("Change category?", False)
    cat_id = choose_category(con) if change_cat else None
    updated = storage.update_expense(con, eid, date=date, amount=amount, description=desc, category_id=cat_id)
    print("Updated." if updated else "No update performed (check id).")

def action_delete_expense(con):
    raw_id = ask("Expense ID to delete: ").strip()
    if not raw_id.isdigit():
        print("Invalid id.")
        return
    eid = int(raw_id)
    if yn(f"Are you sure you want to delete expense #{eid}?", False):
        ok = storage.delete_expense(con, eid)
        print("Deleted." if ok else "Not found.")

def action_export_csv(con):
    rows = storage.list_expenses(con)
    if not rows:
        print("No expenses to export.")
        return
    path = reports.timestamped_export_path()
    out = reports.export_expenses_csv(path, rows)
    print(f"Exported to: {out}")

def action_seed_demo(con):
    # Create some categories if missing
    defaults = ["Food", "Transport", "Entertainment", "Bills", "Health", "Other"]
    existing = {name for _, name in storage.list_categories(con)}
    for name in defaults:
        if name not in existing:
            storage.add_category(con, name)
    # Add expenses for the current and previous month
    from random import choice, randint
    cats = storage.list_categories(con)
    cat_ids = [cid for cid, _ in cats]
    today = datetime.today()
    def add_random(month_offset=0):
        y = today.year
        m = today.month + month_offset
        if m <= 0:
            m += 12
            y -= 1
        d = randint(1, 28)
        date = f"{y:04d}-{m:02d}-{d:02d}"
        amount = round(randint(200, 5000) / 100.0, 2)  # 2.00 .. 50.00
        desc = choice(["Lunch", "Bus ticket", "Streaming", "Groceries", "Coffee", "Pharmacy", "Electricity"])
        storage.add_expense(con, date, amount, desc, choice(cat_ids))
    for _ in range(20):
        add_random(0)
    for _ in range(15):
        add_random(-1)
    print("Seeded demo data.")

def main():
    con = ensure_db()
    while True:
        try:
            menu()
            choice = ask("Select option: ").strip()
            if choice == "1":
                action_add_category(con)
            elif choice == "2":
                action_list_categories(con)
            elif choice == "3":
                action_add_expense(con)
            elif choice == "4":
                action_list_expenses(con)
            elif choice == "5":
                action_monthly_summary(con)
            elif choice == "6":
                action_update_expense(con)
            elif choice == "7":
                action_delete_expense(con)
            elif choice == "8":
                action_export_csv(con)
            elif choice == "9":
                action_seed_demo(con)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")
            input("\nPress Enter to continue...")
            os.system('cls' if os.name == 'nt' else 'clear')
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            break

if __name__ == "__main__":
    main()
