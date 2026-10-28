from pathlib import Path
from typing import Any

import yaml


def load_profile(profile_path: str | Path) -> dict[str, Any]:
    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_insurer_query(
    conn,
    as_of: str,
    profile_dir: Path | str | None = None,
) -> dict[str, Any]:
    base_dir = (
        Path(profile_dir) if profile_dir else Path(__file__).resolve().parent.parent
    )
    profile_cfg = load_profile(base_dir / "profiles" / "insurer" / "profile.yaml")

    open_sql_path = base_dir / profile_cfg["queries"]["open_findings"]
    comp_sql_path = base_dir / profile_cfg["queries"]["completed_remediations"]

    with open(open_sql_path, "r", encoding="utf-8") as f:
        open_sql = f.read()

    with open(comp_sql_path, "r", encoding="utf-8") as f:
        comp_sql = f.read()

    open_findings = []
    completed_remediations = []

    with conn.cursor() as cur:

        def _strip_comments(sql: str) -> str:
            lines = [
                line for line in sql.splitlines() if not line.strip().startswith("--")
            ]
            return "\n".join(lines).upper()

        forbidden_wall_clock = [
            "CURRENT_DATE",
            "NOW()",
            "CURRENT_TIMESTAMP",
            "LOCALTIME",
            "LOCALTIMESTAMP",
        ]
        open_upper = _strip_comments(open_sql)
        comp_upper = _strip_comments(comp_sql)
        for term in forbidden_wall_clock:
            if term in open_upper or term in comp_upper:
                raise ValueError(
                    f"Wall-clock function '{term}' is not permitted in deterministic query definitions."
                )

        cur.execute(open_sql, {"as_of": as_of})
        for row in cur.fetchall():
            open_findings.append(
                {
                    "building": row["building"],
                    "asset": row["asset"],
                    "conducted_on": row["conducted_on"],
                    "finding_id": row["finding_id"],
                    "finding_statement": row["finding_statement"],
                    "due_on": row["due_on"],
                    "completed_on": row["completed_on"],
                    "overdue": bool(row["overdue"]),
                }
            )

        cur.execute(comp_sql, {"as_of": as_of})
        for row in cur.fetchall():
            completed_remediations.append(
                {
                    "building": row["building"],
                    "asset": row["asset"],
                    "conducted_on": row["conducted_on"],
                    "finding_id": row["finding_id"],
                    "finding_statement": row["finding_statement"],
                    "due_on": row["due_on"],
                    "completed_on": row["completed_on"],
                    "overdue": bool(row["overdue"]),
                }
            )

    return {
        "open_findings": open_findings,
        "completed_remediations": completed_remediations,
    }
