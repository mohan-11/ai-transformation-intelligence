"""Dependency & relationship engine (NetworkX).

Builds a directed graph of an analysis: opportunities, processes, value-chain
areas, roles, skills and dependency targets (data / technology / people /
implementation). Provides topological ordering, dependency depth and conflict
detection — all deterministic.
"""
from __future__ import annotations

from typing import Any

import networkx as nx

# Types of nodes we recognise.
OPPORTUNITY = "opportunity"
PROCESS = "process"
VALUE_CHAIN = "value_chain_area"
ROLE = "role"
SKILL = "skill"


def _node_id(prefix: str, label: str) -> str:
    return f"{prefix}:{label}"


def build_graph(opportunities: list[dict[str, Any]]) -> nx.DiGraph:
    """Build a directed graph from a list of scored opportunity records."""
    g = nx.DiGraph()

    for opp in opportunities:
        oid = _node_id(OPPORTUNITY, str(opp.get("id", opp.get("title"))))
        g.add_node(oid, type=OPPORTUNITY, label=opp.get("title", ""), meta=opp)

        # Process link
        process = opp.get("process", "")
        if process:
            pid = _node_id(PROCESS, process)
            g.add_node(pid, type=PROCESS, label=process)
            g.add_edge(pid, oid, type="produces")

        # Value chain link
        vc = opp.get("value_chain_area", "")
        if vc:
            vid = _node_id(VALUE_CHAIN, vc)
            g.add_node(vid, type=VALUE_CHAIN, label=vc)
            g.add_edge(vid, oid, type="contains")

        # Roles + skills
        for role in opp.get("affected_roles", []) or []:
            rid = _node_id(ROLE, role)
            g.add_node(rid, type=ROLE, label=role)
            g.add_edge(oid, rid, type="affects")
        for skill in opp.get("required_skills", []) or []:
            sid = _node_id(SKILL, skill)
            g.add_node(sid, type=SKILL, label=skill)
            g.add_edge(oid, sid, type="requires")

        # Explicit dependencies (data / technology / people / implementation)
        for dep in opp.get("dependencies", []) or []:
            if isinstance(dep, str):
                dep = {"type": "data", "target": dep, "description": ""}
            dep_type = dep.get("type", "data")
            target = dep.get("target", "")
            if not target:
                continue
            tid = _node_id(dep_type, target)
            g.add_node(tid, type=dep_type, label=target)
            g.add_edge(oid, tid, type="depends_on", description=dep.get("description", ""))

    return g


def topological_order(g: nx.DiGraph) -> list[str]:
    """Return node ids in dependency order (dependencies first)."""
    try:
        return list(nx.topological_sort(g))
    except nx.NetworkXUnfeasible:
        # Cycles present — fall back to a deterministic order.
        return list(g.nodes())


def dependency_depth(g: nx.DiGraph, node_id: str) -> int:
    """Number of edges in the longest chain of dependencies below a node."""
    if not g.has_node(node_id):
        return 0
    sub = nx.ego_graph(g, node_id, radius=len(g), center=False)
    try:
        longest = nx.dag_longest_path_length(sub)
    except Exception:  # noqa: BLE001
        longest = 0
    return int(longest)


def find_conflicts(g: nx.DiGraph) -> list[dict[str, Any]]:
    """Two opportunities sharing the same dependency target = a potential
    resource/data conflict worth flagging."""
    conflicts: list[dict[str, Any]] = []
    dependents: dict[str, list[str]] = {}
    for src, tgt in g.edges():
        if g.edges[src, tgt].get("type") == "depends_on":
            dependents.setdefault(tgt, []).append(src)
    for tgt, sources in dependents.items():
        if len(sources) > 1:
            conflicts.append({"target": tgt, "opportunities": sorted(set(sources))})
    return conflicts


def serialize_graph(g: nx.DiGraph) -> dict[str, Any]:
    nodes = [
        {"id": n, "label": g.nodes[n].get("label", n), "type": g.nodes[n].get("type", ""),
         "meta": g.nodes[n].get("meta", {})}
        for n in g.nodes()
    ]
    edges = [
        {"source": s, "target": t, "type": g.edges[s, t].get("type", ""),
         "label": g.edges[s, t].get("description", "")}
        for s, t in g.edges()
    ]
    return {"nodes": nodes, "edges": edges}
