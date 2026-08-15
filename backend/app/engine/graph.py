"""Value-chain relationship graph.

Represents the hierarchy: Industry -> Value Chain -> Process -> Activity ->
AI Opportunity -> Role -> Skill. Built dynamically from what was analysed —
never hard-coded per industry.
"""
from __future__ import annotations

from typing import Any

import networkx as nx

from .dependency import OPPORTUNITY, PROCESS, ROLE, SKILL, VALUE_CHAIN, _node_id


def build_value_chain_graph(
    industry: str,
    value_chain_area: str,
    processes: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
) -> nx.DiGraph:
    g = nx.DiGraph()

    ind = _node_id("industry", industry or "Unknown")
    g.add_node(ind, type="industry", label=industry or "Unknown")

    vc = _node_id(VALUE_CHAIN, value_chain_area or "Operations")
    g.add_node(vc, type=VALUE_CHAIN, label=value_chain_area or "Operations")
    g.add_edge(ind, vc, type="has")

    for proc in processes:
        pid = _node_id(PROCESS, proc.get("name", ""))
        g.add_node(pid, type=PROCESS, label=proc.get("name", ""))
        g.add_edge(vc, pid, type="has")

    for opp in opportunities:
        oid = _node_id(OPPORTUNITY, str(opp.get("id", opp.get("title"))))
        g.add_node(oid, type=OPPORTUNITY, label=opp.get("title", ""), meta=opp)
        proc_name = opp.get("process", "")
        if proc_name:
            g.add_edge(_node_id(PROCESS, proc_name), oid, type="produces")
        else:
            g.add_edge(vc, oid, type="produces")

        for role in opp.get("affected_roles", []) or []:
            rid = _node_id(ROLE, role)
            g.add_node(rid, type=ROLE, label=role)
            g.add_edge(oid, rid, type="affects")
        for skill in opp.get("required_skills", []) or []:
            sid = _node_id(SKILL, skill)
            g.add_node(sid, type=SKILL, label=skill)
            g.add_edge(oid, sid, type="requires")

    return g
