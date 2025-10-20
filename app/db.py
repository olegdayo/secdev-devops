import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SqlParams = Tuple[Any, ...]

DB_PATH = Path(__file__).resolve().parents[1] / "app.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: SqlParams) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def query_one(sql: str, params: SqlParams) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None
