"""Dependency engine + roadmap tests (pure, deterministic)."""
from __future__ import annotations

from app.engine.dependency import build_graph, find_conflicts, serialize_graph, topological_order
from app.engine.roadmap import build_roadmap


def _opps():
    return [
        {
            "id": 1, "title": "AI Support", "process": "Customer Support",
            "value_chain_area": "Service",
            "priority_score": 78, "complexity_component": 35,
            "affected_roles": ["Support Agent"], "required_skills": ["NLP"],
            "dependencies": [
                {"type": "data", "target": "Customer Data", "description": ""},
                {"type": "technology", "target": "API Integration", "description": ""},
            ],
        },
        {
            "id": 2, "title": "AI Forecasting", "process": "Demand Planning",
            "value_chain_area": "Operations",
            "priority_score": 50, "complexity_component": 60,
            "affected_roles": ["Planner"], "required_skills": ["ML"],
            "dependencies": [{"type": "data", "target": "Customer Data", "description": ""}],
        },
    ]


def test_build_graph_has_nodes_and_edges():
    g = build_graph(_opps())
    assert g.number_of_nodes() > 0
    assert g.number_of_edges() > 0


def test_shared_dependency_detected_as_conflict():
    g = build_graph(_opps())
    conflicts = find_conflicts(g)
    # Both opportunities depend on 'Customer Data'
    targets = [c["target"] for c in conflicts]
    assert any("Customer Data" in t for t in targets)


def test_topological_order_is_deterministic():
    g = build_graph(_opps())
    order1 = topological_order(g)
    order2 = topological_order(g)
    assert order1 == order2


def test_serialize_graph_shape():
    data = serialize_graph(build_graph(_opps()))
    assert "nodes" in data and "edges" in data
    assert all("id" in n for n in data["nodes"])
    assert all("source" in e and "target" in e for e in data["edges"])


def test_roadmap_quick_win_bucket():
    roadmap = build_roadmap(_opps(), weights={})
    # id 1 = high priority, low complexity -> quick win
    assert any(i.opportunity_id == 1 and i.phase == "quick_win" for i in roadmap.quick_wins)
    # id 2 = medium -> not a quick win
    assert not any(i.opportunity_id == 2 and i.phase == "quick_win" for i in roadmap.quick_wins)


def test_roadmap_orders_by_priority():
    roadmap = build_roadmap(_opps(), weights={})
    quick = roadmap.quick_wins
    priorities = [i.priority_score for i in quick]
    assert priorities == sorted(priorities, reverse=True)
