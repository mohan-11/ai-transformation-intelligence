"""AI Transformation Strategy Intelligence — executive dashboard (Streamlit).

A thin presentation layer over the FastAPI backend. All intelligence, scoring
and ranking happen server-side; this app only renders real backend data.

Run:
    streamlit run frontend/app.py
"""
from __future__ import annotations

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import api_client as api

st.set_page_config(page_title="AI Transformation Intelligence", page_icon="🧠", layout="wide")

TYPE_COLORS = {
    "opportunity": "#2563eb",
    "process": "#16a34a",
    "value_chain_area": "#d97706",
    "industry": "#7c3aed",
    "role": "#0891b2",
    "skill": "#db2777",
    "data": "#dc2626",
    "technology": "#6d28d9",
    "people": "#ea580c",
    "implementation": "#4b5563",
}


# --------------------------------------------------------------------------
# Chart helpers (all render real backend data)
# --------------------------------------------------------------------------
def render_graph(graph: dict, title: str) -> go.Figure:
    g = nx.DiGraph()
    for n in graph.get("nodes", []):
        g.add_node(n["id"], label=n.get("label", n["id"]), type=n.get("type", ""))
    for e in graph.get("edges", []):
        g.add_edge(e["source"], e["target"])
    if g.number_of_nodes() == 0:
        return go.Figure()
    pos = nx.spring_layout(g, seed=42, k=1.4 / max(1, g.number_of_nodes() ** 0.3))

    edge_x, edge_y = [], []
    for s, t in g.edges():
        x0, y0 = pos[s]
        x1, y1 = pos[t]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x, node_y, labels, colors = [], [], [], []
    for n, p in pos.items():
        node_x.append(p[0])
        node_y.append(p[1])
        labels.append(g.nodes[n].get("label", n))
        colors.append(TYPE_COLORS.get(g.nodes[n].get("type", ""), "#888888"))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="#cbd5e1"), hoverinfo="none",
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=labels, textposition="top center",
        marker=dict(size=16, color=colors, line=dict(width=1, color="#ffffff")),
        hovertext=[f"{l} ({g.nodes[n].get('type','')})" for l, n in zip(labels, g.nodes())],
    ))
    fig.update_layout(
        title=title, showlegend=False, height=520,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def value_complexity_matrix(opps: list[dict]) -> go.Figure:
    df = pd.DataFrame(opps)
    if df.empty:
        return go.Figure()
    phase_map = {"quick_win": "Quick Win", "medium_term": "Medium-Term", "strategic": "Strategic"}
    df["phase_label"] = df.get("phase", "medium_term").map(lambda p: phase_map.get(p, p))
    colors = {"Quick Win": "#16a34a", "Medium-Term": "#f59e0b", "Strategic": "#2563eb"}
    fig = go.Figure()
    for phase, grp in df.groupby("phase_label"):
        fig.add_trace(go.Scatter(
            x=grp["complexity_component"], y=grp["priority_score"],
            mode="markers", name=phase,
            marker=dict(size=grp["business_value_component"] * 0.5 + 8, color=colors.get(phase, "#888"),
                        line=dict(width=1, color="#fff")),
            text=grp["title"], hovertemplate="%{text}<br>priority %{y:.0f}<br>complexity %{x:.0f}<extra></extra>",
        ))
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=100, line=dict(dash="dash", color="#999"))
    fig.update_layout(
        title="Priority vs Complexity Matrix (size = business value)", height=440,
        xaxis_title="Implementation complexity (lower = easier)",
        yaxis_title="Priority score",
    )
    return fig


def top_opportunities_bar(opps: list[dict]) -> go.Figure:
    df = pd.DataFrame(opps).sort_values("priority_score", ascending=True)
    if df.empty:
        return go.Figure()
    fig = go.Figure(go.Bar(
        x=df["priority_score"], y=df["title"], orientation="h",
        marker_color="#2563eb", text=df["priority_score"].round(0),
        textposition="outside",
    ))
    fig.update_layout(title="Top AI Opportunities", height=380, xaxis_title="Priority score",
                      yaxis=dict(autorange="reversed"))
    return fig


def score_gauge(opp: dict) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=opp["priority_score"],
        gauge=dict(axis=dict(range=[0, 100]), bar=dict(color="#2563eb")),
        title=dict(text="Priority"),
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10))
    return fig


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def _split_lines(text: str) -> list[str]:
    return [x.strip() for x in text.splitlines() if x.strip()]


def page_setup():
    st.header("🏗️ Organisation Setup & Analysis")
    with st.form("org_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Organisation name", placeholder="e.g. ABC Retail")
        industry = col2.text_input("Industry", placeholder="e.g. Retail, Healthcare, Manufacturing…")
        description = st.text_area("Organisation description", placeholder="What does this organisation do?")
        goals = st.text_area("Business goals (one per line)", placeholder="Reduce operating costs\nImprove customer experience")
        submitted = st.form_submit_button("Create Organisation", type="primary")

    if submitted and name:
        try:
            org = api.create_organisation(name, industry, description, _split_lines(goals))
            st.session_state.org_id = org["id"]
            st.session_state.org_name = org["name"]
            st.success(f"Created organisation '{org['name']}' (id {org['id']})")
        except api.ApiError as e:
            st.error(str(e))

    org_id = st.session_state.get("org_id")
    if not org_id:
        st.info("Create an organisation above to begin.")
        return

    st.divider()
    st.subheader(f"➕ Add processes to '{st.session_state.get('org_name', '')}'")
    with st.form("process_form"):
        pname = st.text_input("Process name", placeholder="e.g. Demand Forecasting")
        pdesc = st.text_area("Process description", placeholder="What does this process do?")
        pobj = st.text_input("Business objective", placeholder="What should this process achieve?")
        pain = st.text_area("Pain points (one per line)", placeholder="Manual reorder decisions\nFrequent stock-outs")
        data = st.text_area("Available data (one per line)", placeholder="Historical sales\nInventory levels")
        add = st.form_submit_button("Add Process")

    if add and pname:
        try:
            api.create_process(org_id, pname, pdesc, pobj, industry, "", _split_lines(pain), _split_lines(data))
            st.success(f"Added process '{pname}'")
        except api.ApiError as e:
            st.error(str(e))

    processes = []
    try:
        processes = api.list_processes(org_id)
    except api.ApiError as e:
        st.error(str(e))

    if processes:
        st.write("**Processes in this organisation:**")
        for p in processes:
            st.markdown(f"- `{p['name']}` → value chain: *{p.get('value_chain_area') or 'not yet analysed'}*")

    st.divider()
    if st.button("🚀 Run AI Analysis", type="primary", use_container_width=True):
        with st.spinner("Analysing value chain, retrieving knowledge, generating & scoring opportunities…"):
            try:
                analysis = api.run_analysis(org_id)
                st.session_state.analysis = analysis
                st.session_state.analysis_org_id = org_id
                st.success(f"Analysis complete — {len(analysis['opportunities'])} opportunities generated.")
                st.rerun()
            except api.ApiError as e:
                st.error(str(e))


def page_dashboard():
    st.header("📊 Executive Dashboard")

    orgs = api.get_organisations()
    if not orgs:
        st.info("No organisations yet — create one under 'Setup & Analyse'.")
        return

    org_names = {o["name"]: o["id"] for o in orgs}
    selected = st.selectbox("Organisation", list(org_names.keys()))
    org_id = org_names[selected]

    analyses = api.list_analyses(org_id)
    completed = [a for a in analyses if a["status"] == "completed"]
    if not completed:
        st.warning("No completed analysis for this organisation. Run one under 'Setup & Analyse'.")
        return

    analysis = api.get_analysis(completed[0]["id"])
    opps = analysis["opportunities"]
    if not opps:
        st.warning("No opportunities found.")
        return

    # Phase tagging for charts.
    roadmap = api.get_roadmap(org_id)
    phase_by_id = {}
    for group in ("quick_wins", "medium_term", "strategic"):
        for item in roadmap[group]:
            phase_by_id[item["opportunity_id"]] = group
    for o in opps:
        o["phase"] = phase_by_id.get(o["id"], "strategic")

    # 1. Executive summary + headline metrics.
    st.subheader("1 · Executive Summary")
    st.write(analysis["summary"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Opportunities", len(opps))
    c2.metric("Top priority", f"{max(o['priority_score'] for o in opps):.0f}/100")
    c3.metric("Quick wins", len(roadmap["quick_wins"]))
    c4.metric("Avg. confidence", f"{sum(o['confidence_score'] for o in opps) / len(opps):.0f}/100")

    # 2. Top opportunities + matrix.
    st.subheader("2 · Top AI Opportunities")
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.plotly_chart(top_opportunities_bar(opps), use_container_width=True)
    with col_b:
        st.plotly_chart(value_complexity_matrix(opps), use_container_width=True)

    # 3. Opportunity ranking table.
    st.subheader("3 · Opportunity Ranking")
    table = pd.DataFrame([{
        "Rank": i + 1, "Opportunity": o["title"], "Process": o["process"],
        "Value chain": o["value_chain_area"], "Capability": o["ai_capability"],
        "Value": o["expected_business_value"], "Complexity": o["implementation_complexity"],
        "Priority": o["priority_score"], "Confidence": o["confidence_score"],
    } for i, o in enumerate(opps)])
    st.dataframe(table.sort_values("Priority", ascending=False), use_container_width=True, hide_index=True)

    # 4. Roadmap.
    st.subheader("4 · Transformation Roadmap")
    rcol1, rcol2, rcol3 = st.columns(3)
    for col, key, label, emoji in [
        (rcol1, "quick_wins", "Quick Wins (0–3 months)", "⚡"),
        (rcol2, "medium_term", "Medium-Term (3–6 months)", "📈"),
        (rcol3, "strategic", "Strategic (6–12+ months)", "🎯"),
    ]:
        with col:
            st.markdown(f"**{emoji} {label}**")
            items = roadmap[key]
            if not items:
                st.caption("None")
            for it in items:
                st.markdown(f"- **{it['title']}**  \n  `{it['priority_score']:.0f}/100` — {it['timeframe']}")

    # 5. Dependency graph + value chain graph.
    st.subheader("5 · Dependencies & Value Chain")
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        deps = api.get_dependencies(org_id)
        st.plotly_chart(render_graph(deps["graph"], "Dependency Graph"), use_container_width=True)
        if deps.get("conflicts"):
            st.caption("⚠️ Shared-dependency conflicts: " +
                       ", ".join(c["target"].split(":")[-1] for c in deps["conflicts"]))
    with gcol2:
        vc = api.get_value_chain(org_id)
        st.plotly_chart(render_graph(vc, "Value-Chain Graph"), use_container_width=True)

    # 6. Data readiness.
    st.subheader("6 · Data Readiness")
    dr = pd.DataFrame([{
        "Opportunity": o["title"], "Availability": o["data_availability"],
        "Readiness": o["data_readiness_component"], "Priority": o["priority_score"],
    } for o in opps]).sort_values("Readiness", ascending=False)
    st.bar_chart(dr.set_index("Opportunity")[["Readiness"]], height=300)

    # 7. Opportunity deep-dives (explainability + evidence).
    st.subheader("7 · Explain Recommendation")
    st.caption("Every recommendation shows FACT (input/retrieved evidence) vs INFERENCE (AI reasoning) vs RECOMMENDATION.")
    for o in opps:
        with st.expander(f"{o['title']} — priority {o['priority_score']:.0f}/100"):
            gcol = st.columns([1, 3])
            with gcol[0]:
                st.plotly_chart(score_gauge(o), use_container_width=True)
                st.markdown(f"**Value**: {o['expected_business_value']} · **Complexity**: {o['implementation_complexity']}")
                st.markdown(f"**Data availability**: {o['data_availability']}")
            with gcol[1]:
                st.markdown(o["explanation"])
            st.markdown("**Required data:** " + ", ".join(o["data_requirements"]))
            st.markdown("**Affected roles:** " + ", ".join(o["affected_roles"]))
            st.markdown("**Required skills:** " + ", ".join(o["required_skills"]))
            if o.get("evidence"):
                st.markdown("**Evidence / sources:**")
                for e in o["evidence"]:
                    st.markdown(f"- *{e.get('source') or e.get('title')}* — {e.get('excerpt', '')[:180]}")


def page_add_process():
    st.header("➕ Add Process (dynamic — no code changes)")
    orgs = api.get_organisations()
    if not orgs:
        st.info("Create an organisation first.")
        return
    org_names = {o["name"]: o["id"] for o in orgs}
    selected = st.selectbox("Organisation", list(org_names.keys()))
    org_id = org_names[selected]
    org = api.get_organisation(org_id)

    with st.form("add_proc"):
        name = st.text_input("Process name", placeholder="e.g. Claims Processing")
        desc = st.text_area("Process description")
        obj = st.text_input("Business objective")
        industry = st.text_input("Industry", value=org.get("industry_name", ""))
        tech = st.text_input("Current technology", placeholder="e.g. spreadsheets, legacy ERP")
        pain = st.text_area("Pain points (one per line)")
        data = st.text_area("Available data (one per line)")
        submit = st.form_submit_button("➕ Add & Analyse Process", type="primary")

    if submit and name:
        try:
            proc = api.create_process(org_id, name, desc, obj, industry, tech,
                                      _split_lines(pain), _split_lines(data))
            with st.spinner("Analysing process…"):
                analysis = api.analyse_process(proc["id"])
            st.session_state.analysis = analysis
            st.session_state.analysis_org_id = org_id
            st.success(f"Analysed '{name}' → {len(analysis['opportunities'])} opportunities.")
            for o in analysis["opportunities"]:
                st.markdown(f"- **{o['title']}** (`{o['priority_score']:.0f}/100`) — {o['ai_capability']}")
        except api.ApiError as e:
            st.error(str(e))


def page_knowledge():
    st.header("📚 Knowledge Base & Sources")
    st.markdown("Upload documents to extend the knowledge base. Retrieval uses these "
                "documents plus the seeded reference knowledge.")

    up = st.file_uploader("Upload a document (.txt, .md, .pdf, .docx)", type=["txt", "md", "pdf", "docx"])
    industry = st.text_input("Industry context (optional)")
    if up is not None and st.button("Upload & Ingest"):
        try:
            doc = api.upload_document(up.getvalue(), up.name, industry=industry)
            st.success(f"Ingested '{doc['filename']}' — {doc['title']} (chunks embedded into the vector store).")
        except api.ApiError as e:
            st.error(str(e))

    st.divider()
    st.subheader("Research preview")
    q = st.text_input("Query (e.g. a process or problem)")
    if st.button("Search knowledge"):
        try:
            findings = api.research(q, industry, 5)
            if not findings:
                st.caption("No matching knowledge found.")
            for f in findings:
                st.markdown(f"**[{f['evidence_level']}] {f['title']}** ({f['source_type']})  \n{f['summary'][:300]}")
        except api.ApiError as e:
            st.error(str(e))


# --------------------------------------------------------------------------
# App shell
# --------------------------------------------------------------------------
def main():
    st.sidebar.title("🧠 AI Transformation\nStrategy Intelligence")
    st.sidebar.caption("Enterprise AI opportunity analysis")

    try:
        h = api.health()
        st.sidebar.success(f"Backend: {h['app']} ✓")
    except api.ApiError:
        st.sidebar.error("Backend not reachable.\nStart it with:\n`uvicorn app.main:app --reload`")

    page = st.sidebar.radio(
        "Navigation",
        ["Setup & Analyse", "Dashboard", "Add Process", "Knowledge Base"],
    )

    try:
        if page == "Setup & Analyse":
            page_setup()
        elif page == "Dashboard":
            page_dashboard()
        elif page == "Add Process":
            page_add_process()
        elif page == "Knowledge Base":
            page_knowledge()
    except api.ApiError as e:
        st.error(str(e))

    st.sidebar.divider()
    st.sidebar.caption("Scoring is deterministic and configurable.\n"
                       "LLM provider: auto → heuristic (offline).\n"
                       "Embeddings: TF-IDF → semantic (optional).")


if __name__ == "__main__":
    main()
