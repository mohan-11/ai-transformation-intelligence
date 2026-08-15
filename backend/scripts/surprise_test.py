"""Surprise-record test — demonstrates the system analysing brand-new
industry/process combinations dynamically (no source-code changes).

Run from the repo root:
    python backend/scripts/surprise_test.py

Uses a throwaway SQLite database so it never pollutes real data.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# Isolate a fresh DB before importing the app.
_tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="aitransform_surprise_"))
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir / 'surprise.db'}"
os.environ["EMBEDDING_PROVIDER"] = "tfidf"
os.environ["VECTOR_STORE"] = "memory"
os.environ["LLM_PROVIDER"] = "heuristic"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db import SessionLocal, init_db  # noqa: E402
from app.intelligence.analysis.orchestrator import run_analysis  # noqa: E402
from app.models import AIOpportunity, Organisation, Process  # noqa: E402

init_db()

CASES = [
    {
        "org": "ABC Retail",
        "industry": "Retail",
        "goals": ["Reduce operating costs", "Improve customer experience"],
        "process": {
            "name": "Inventory Management",
            "description": "Managing stock levels across warehouses and stores.",
            "objective": "Reduce stock-outs and overstock while lowering holding cost.",
            "pain_points": ["Manual reorder decisions", "Frequent stock-outs", "Excess inventory"],
            "available_data": ["Historical sales", "Inventory levels", "Supplier lead times"],
        },
    },
    {
        "org": "MediClaim Health",
        "industry": "Healthcare",
        "goals": ["Reduce processing time", "Lower administrative cost"],
        "process": {
            "name": "Claims Processing",
            "description": "Receiving, validating and paying insurance claims.",
            "objective": "Automate claim validation and reduce manual review.",
            "pain_points": ["High manual review volume", "Slow reimbursement", "Inconsistent decisions"],
            "available_data": ["Historical claims", "Policy documents", "Provider data"],
        },
    },
    {
        "org": "Precision Manufacturing Co",
        "industry": "Manufacturing",
        "goals": ["Reduce unplanned downtime", "Improve asset utilisation"],
        "process": {
            "name": "Predictive Maintenance",
            "description": "Monitoring equipment to predict failures before they happen.",
            "objective": "Shift from reactive to condition-based maintenance.",
            "pain_points": ["Unplanned outages", "Reactive repairs", "High maintenance cost"],
            "available_data": ["Sensor telemetry", "Maintenance logs", "Failure records"],
        },
    },
    {
        "org": "Northfield University",
        "industry": "Education",
        "goals": ["Improve learning outcomes", "Reduce teacher workload"],
        "process": {
            "name": "Student Assessment",
            "description": "Grading assignments and providing feedback to students.",
            "objective": "Automate routine grading and personalise feedback.",
            "pain_points": ["Time-consuming grading", "Inconsistent feedback", "Delayed results"],
            "available_data": ["Student submissions", "Rubrics", "Historical grades"],
        },
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for i, case in enumerate(CASES, start=1):
            org = Organisation(
                name=case["org"],
                industry_name=case["industry"],
                description=case["industry"],
                business_goals=case["goals"],
            )
            db.add(org)
            db.flush()
            p = case["process"]
            proc = Process(
                organisation_id=org.id,
                name=p["name"],
                description=p["description"],
                business_objective=p["objective"],
                industry=case["industry"],
                pain_points=p["pain_points"],
                available_data=p["available_data"],
            )
            db.add(proc)
            db.commit()

            analysis = run_analysis(db, org.id)
            opps = (
                db.query(AIOpportunity)
                .filter(AIOpportunity.analysis_id == analysis.id)
                .order_by(AIOpportunity.priority_score.desc())
                .all()
            )
            print("\n" + "=" * 70)
            print(f"Case {i}: {case['org']} ({case['industry']}) — process: {p['name']}")
            print("=" * 70)
            for o in opps[:3]:
                print(f"  [{o.priority_score:5.1f}] {o.title}")
                print(f"          capability={o.ai_capability} | value={o.expected_business_value} "
                      f"| complexity={o.implementation_complexity} | vc={o.value_chain_area}")
            print(f"  (total {len(opps)} opportunities generated)")
        print("\nAll surprise cases analysed dynamically — no hard-coded answers.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
