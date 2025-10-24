from __future__ import annotations
import os, csv
from typing import List, Tuple, Optional
from datetime import datetime
from utils import fmt_money, fmt_row

def print_table(headers: List[str], rows: List[List[str]]) -> None:
    col_widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    print(fmt_row(headers, col_widths))
    print("-" * (sum(col_widths) + 3 * (len(col_widths)-1)))
    for r in rows:
        print(fmt_row([str(c) for c in r], col_widths))

def export_expenses_csv(filepath: str, expenses: List[Tuple]) -> str:
    """
    expenses columns: id, date, amount, description, category
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "amount", "description", "category"])
        for row in expenses:
            writer.writerow(row)
    return filepath

def timestamped_export_path() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join("exports", f"expenses_{ts}.csv")

def print_monthly_summary(totals: List[Tuple[str, float]]) -> None:
    total_sum = sum(v for _, v in totals) if totals else 0.0
    rows = [[name, fmt_money(val)] for name, val in totals]
    print_table(["Category", "Total"], rows)
    print("-" * 32)
    print(f"Overall: {fmt_money(total_sum)}")
