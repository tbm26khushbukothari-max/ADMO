import streamlit as st

st.set_page_config(page_title="Verticals | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, section_header,
    kpi_card, download_df, stat_callout, insight_card, persona_banner,
    target_vs_actual, rag_badge,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, CARD_BG, BORDER, MUTED, DIM,
    RED, AMBER, GREEN,
    PLOTLY_LAYOUT, VERTICAL_COLORS,
)
from lib.data import (
    load_monthly_summary, load_venues, load_daily_ops, load_brand_health,
    load_savings, load_plan_targets, load_headcount, load_hiring,
    get_scope_venue_ids, filter_by_scope, compute_growth_pct,
    compute_budget_variance, compute_revpash,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Verticals", f"Scope: {scope_desc(scope)}")

persona_banner(
    "Verticals",
    "Group CEO, Board, Investment Committee",
    ["Which unit is leading?", "Where to invest next?", "What's dragging the portfolio?",
     "How do verticals compare on efficiency?", "Where are the savings?"],
)

summary = load_monthly_summary()
health = load_brand_health()
savings = load_savings()
daily_ops = load_daily_ops()
targets = load_plan_targets()

verticals = sorted(venues["vertical"].dropna().unique())

# ── Portfolio-level summary KPIs ──────────────────────────────

section_header("Portfolio Summary", "Across all verticals in scope")

total_rev = summary[summary["venue_id"].isin(venue_ids)]["revenue_aed"].sum()
total_covers = summary[summary["venue_id"].isin(venue_ids)]["covers"].sum()
avg_check = total_rev / total_covers if total_covers else 0
n_verticals = len(verticals)
n_venues = len(venue_ids)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Total Revenue", fmt_currency(total_rev, ccy), icon="💰", border_color=GOLD)
with c2:
    kpi_card("Total Covers", f"{total_covers:,.0f}", icon="🍽")
with c3:
    kpi_card("Avg Check", fmt_currency(avg_check, ccy), icon="🧾")
with c4:
    kpi_card("Verticals", str(n_verticals), icon="🏢")
with c5:
    kpi_card("Venues", str(n_venues), icon="📍")

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ── Tabbed sections ───────────────────────────────────────────

tab_cards, tab_compare, tab_efficiency, tab_savings, tab_data = st.tabs([
    "📊 Scorecards", "⚖️ Comparative Analysis", "🏭 Efficiency & Targets",
    "💰 Savings by Vertical", "📋 Raw Data"
])

# ── Tab 1: Scorecards ────────────────────────────────────────

with tab_cards:
    section_header("Vertical Scorecards",
                    "Revenue, growth, health score, efficiency and venue count per business unit")

    cols = st.columns(min(len(verticals), 5))

    vert_data = []
    for i, vert in enumerate(verticals):
        vert_venues = set(venues[venues["vertical"] == vert]["venue_id"])
        vert_summary = summary[summary["venue_id"].isin(vert_venues)]
        rev = vert_summary["revenue_aed"].sum()
        covers = vert_summary["covers"].sum()
        growth = compute_growth_pct(summary, vert_venues)
        avg_chk = rev / covers if covers else 0
        avg_sat = vert_summary["avg_satisfaction"].mean() if not vert_summary.empty else 0

        # Operational metrics
        vert_ops = daily_ops[daily_ops["venue_id"].isin(vert_venues)]
        avg_occ = vert_ops["occupancy_pct"].mean() if not vert_ops.empty else 0
        avg_nps = vert_ops["nps_score"].mean() if not vert_ops.empty else 0
        avg_food_cost = vert_ops["food_cost_pct"].mean() if not vert_ops.empty else 0
        avg_labor_cost = vert_ops["labor_cost_pct"].mean() if not vert_ops.empty else 0

        # RevPASH
        revpash = compute_revpash(daily_ops, venues, vert_venues)

        # Health
        latest_health = health[health["brand"].isin(
            venues[venues["vertical"] == vert]["brand"].unique()
        )]
        h_score = 0
        if not latest_health.empty:
            h_score = latest_health.groupby("month")["health_score"].mean().iloc[-1]

        # Budget variance
        _, tgt_rev, var_pct = compute_budget_variance(vert_summary, targets, vert_venues)

        n_v = len(vert_venues)
        color = VERTICAL_COLORS.get(vert, GOLD)
        h_color = GREEN if h_score >= 75 else (AMBER if h_score >= 60 else RED)
        g_color = GREEN if growth >= 0 else RED
        occ_color = GREEN if avg_occ >= 0.7 else (AMBER if avg_occ >= 0.5 else RED)

        vert_data.append({
            "vertical": vert, "revenue": rev, "covers": covers, "growth": growth,
            "avg_check": avg_chk, "avg_sat": avg_sat, "avg_occ": avg_occ,
            "avg_nps": avg_nps, "food_cost": avg_food_cost, "labor_cost": avg_labor_cost,
            "health": h_score, "n_venues": n_v, "revpash": revpash, "var_pct": var_pct,
        })

        with cols[i % len(cols)]:
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{CARD_BG} 0%,#162236 100%); "
                f"border-top:3px solid {color}; border:1px solid {BORDER}; "
                f"border-radius:10px; padding:18px; margin-bottom:12px;'>"
                f"<div style='color:{color}; font-weight:700; font-size:1.05rem; "
                f"margin-bottom:10px;'>{vert}</div>"
                f"<div style='color:{MUTED}; font-size:0.75rem; text-transform:uppercase; "
                f"letter-spacing:0.06em;'>Revenue</div>"
                f"<div style='color:{OFF_WHITE}; font-size:1.15rem; font-weight:600; "
                f"margin-bottom:6px;'>{fmt_currency(rev, ccy)}</div>"
                f"<div style='display:flex; justify-content:space-between; margin-top:4px;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Covers</span>"
                f"<span style='color:{OFF_WHITE}; font-size:0.85rem;'>{covers:,.0f}</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Avg Check</span>"
                f"<span style='color:{OFF_WHITE}; font-size:0.85rem;'>{fmt_currency(avg_chk, ccy)}</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Occupancy</span>"
                f"<span style='color:{occ_color}; font-size:0.85rem;'>{avg_occ:.0%}</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>NPS</span>"
                f"<span style='color:{OFF_WHITE}; font-size:0.85rem;'>{avg_nps:.0f}</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Growth</span>"
                f"<span style='color:{g_color}; font-size:0.85rem; font-weight:600;'>"
                f"{growth:+.1f}%</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Health</span>"
                f"<span style='color:{h_color}; font-size:0.85rem; font-weight:600;'>"
                f"{h_score:.0f}/100</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Food Cost</span>"
                f"<span style='color:{OFF_WHITE}; font-size:0.85rem;'>{avg_food_cost:.1%}</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>Labour Cost</span>"
                f"<span style='color:{OFF_WHITE}; font-size:0.85rem;'>{avg_labor_cost:.1%}</span></div>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{MUTED}; font-size:0.78rem;'>RevPASH</span>"
                f"<span style='color:{GOLD}; font-size:0.85rem;'>{fmt_currency(revpash, ccy)}</span></div>"
                f"<div style='color:{DIM}; font-size:0.72rem; margin-top:8px; "
                f"text-align:center; border-top:1px solid {BORDER}; padding-top:6px;'>"
                f"{n_v} venue(s) &bull; Plan variance: {var_pct:+.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Auto-insights row
    st.divider()
    section_header("Vertical Insights", "Auto-detected patterns across business units")

    if vert_data:
        vdf = pd.DataFrame(vert_data)
        best_growth = vdf.loc[vdf["growth"].idxmax()]
        worst_growth = vdf.loc[vdf["growth"].idxmin()]
        best_eff = vdf.loc[vdf["revpash"].idxmax()]

        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            insight_card("🚀", "Fastest Growing",
                         f"{best_growth['vertical']} at {best_growth['growth']:+.1f}% QoQ",
                         GREEN if best_growth["growth"] > 0 else AMBER)
        with col_i2:
            insight_card("⚠", "Needs Attention" if worst_growth["growth"] < 0 else "Slowest Growth",
                         f"{worst_growth['vertical']} at {worst_growth['growth']:+.1f}% QoQ",
                         RED if worst_growth["growth"] < 0 else AMBER)
        with col_i3:
            insight_card("🏆", "Most Efficient",
                         f"{best_eff['vertical']} — RevPASH {fmt_currency(best_eff['revpash'], ccy)}",
                         GOLD)

# ── Tab 2: Comparative Analysis ─────────────────────────────

with tab_compare:
    section_header("Head-to-Head Comparison",
                    "Which vertical leads on revenue? Which has the happiest guests?")

    metric_choice = st.radio(
        "Compare by", ["Revenue", "NPS", "Occupancy", "Food Cost %", "Labour Cost %",
                        "Avg Check", "Satisfaction"],
        horizontal=True, key="vert_compare_metric",
    )

    ops = daily_ops.merge(venues[["venue_id", "vertical"]], on="venue_id", how="left")

    metric_map = {
        "Revenue": ("revenue_aed", summary, "vertical", "sum"),
        "NPS": ("nps_score", ops, "vertical", "mean"),
        "Occupancy": ("occupancy_pct", ops, "vertical", "mean"),
        "Food Cost %": ("food_cost_pct", ops, "vertical", "mean"),
        "Labour Cost %": ("labor_cost_pct", ops, "vertical", "mean"),
        "Avg Check": ("avg_check", summary, "vertical", "mean"),
        "Satisfaction": ("avg_satisfaction", ops if "avg_satisfaction" in ops.columns else summary, "vertical", "mean"),
    }
    col_name, df_src, grp_col, agg_fn = metric_map[metric_choice]

    if agg_fn == "sum":
        chart_data = df_src.groupby(grp_col)[col_name].sum().reset_index()
    else:
        chart_data = df_src.groupby(grp_col)[col_name].mean().reset_index()

    chart_data = chart_data.sort_values(col_name, ascending=True)

    tick_fmt = ".0%" if "cost" in metric_choice.lower() or "occupancy" in metric_choice.lower() else None

    fig = px.bar(
        chart_data, x=col_name, y=grp_col, orientation="h",
        color=grp_col, color_discrete_map=VERTICAL_COLORS,
        labels={col_name: metric_choice, grp_col: ""},
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False,
                       title=f"{metric_choice} by Vertical")
    if tick_fmt:
        fig.update_xaxes(gridcolor="#2A3950", tickformat=tick_fmt)
    else:
        fig.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig, use_container_width=True)

    # Trend over time
    section_header("Monthly Trend", "How has each vertical evolved over the analysis period?")
    if metric_choice == "Revenue":
        trend_data = summary.groupby(["month", "vertical"])["revenue_aed"].sum().reset_index()
        y_col = "revenue_aed"
    else:
        ops_monthly = ops.copy()
        ops_monthly["month"] = ops_monthly["date"].dt.to_period("M").dt.to_timestamp()
        trend_data = ops_monthly.groupby(["month", "vertical"])[col_name].mean().reset_index()
        y_col = col_name

    fig_trend = px.line(
        trend_data, x="month", y=y_col, color="vertical",
        color_discrete_map=VERTICAL_COLORS,
        labels={y_col: metric_choice, "month": "", "vertical": "Vertical"},
    )
    fig_trend.update_layout(**PLOTLY_LAYOUT, height=300)
    if tick_fmt:
        fig_trend.update_yaxes(gridcolor="#2A3950", tickformat=tick_fmt)
    else:
        fig_trend.update_yaxes(gridcolor="#2A3950")
    fig_trend.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_trend, use_container_width=True)

    # Radar chart for multi-dimensional comparison
    st.divider()
    section_header("Multi-Dimensional Radar", "Compare verticals across all key metrics simultaneously")

    if vert_data:
        vdf = pd.DataFrame(vert_data)
        categories = ["Revenue Share", "NPS", "Occupancy", "Satisfaction", "Growth"]

        # Normalise each metric to 0-100 for radar
        max_rev = vdf["revenue"].max() if vdf["revenue"].max() > 0 else 1
        # Map hex colors to rgba for fill
        def hex_to_rgba(hex_color, alpha=0.1):
            h = hex_color.lstrip("#")
            if len(h) == 6:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                return f"rgba({r},{g},{b},{alpha})"
            return f"rgba(201,169,97,{alpha})"

        fig_radar = go.Figure()
        for _, row in vdf.iterrows():
            vals = [
                row["revenue"] / max_rev * 100,
                min(row["avg_nps"], 100),
                row["avg_occ"] * 100,
                row["avg_sat"] * 10,
                max(0, min(100, 50 + row["growth"])),
            ]
            vc = VERTICAL_COLORS.get(row["vertical"], GOLD)
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=categories + [categories[0]],
                name=row["vertical"],
                line=dict(color=vc, width=2),
                fill="toself",
                fillcolor=hex_to_rgba(vc),
            ))
        fig_radar.update_layout(
            **PLOTLY_LAYOUT, height=400,
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2A3950"),
                angularaxis=dict(gridcolor="#2A3950"),
            ),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ── Tab 3: Efficiency & Targets ──────────────────────────────

with tab_efficiency:
    section_header("Revenue Efficiency",
                    "RevPASH (Revenue per Available Seat Hour) — the CEO's favourite efficiency metric")

    if vert_data:
        vdf = pd.DataFrame(vert_data)

        col_l, col_r = st.columns(2)
        with col_l:
            fig_revpash = px.bar(
                vdf.sort_values("revpash"), x="revpash", y="vertical", orientation="h",
                color="vertical", color_discrete_map=VERTICAL_COLORS,
                labels={"revpash": f"RevPASH ({ccy})", "vertical": ""},
            )
            fig_revpash.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False,
                                       title="RevPASH by Vertical")
            fig_revpash.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_revpash, use_container_width=True)

        with col_r:
            # Revenue per venue
            vdf["rev_per_venue"] = vdf["revenue"] / vdf["n_venues"].clip(lower=1)
            fig_rpv = px.bar(
                vdf.sort_values("rev_per_venue"), x="rev_per_venue", y="vertical", orientation="h",
                color="vertical", color_discrete_map=VERTICAL_COLORS,
                labels={"rev_per_venue": f"Revenue per Venue ({ccy})", "vertical": ""},
            )
            fig_rpv.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False,
                                   title="Avg Revenue per Venue")
            fig_rpv.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_rpv, use_container_width=True)

    # Budget vs actual per vertical
    st.divider()
    section_header("Plan vs Actual by Vertical",
                    "Are we hitting our targets? Red = more than 5% below plan")

    target_rows = []
    for vert in verticals:
        vert_vids = set(venues[venues["vertical"] == vert]["venue_id"])
        vert_sum = summary[summary["venue_id"].isin(vert_vids)]
        actual, target, var = compute_budget_variance(vert_sum, targets, vert_vids)
        target_rows.append({"Vertical": vert, "Actual": actual, "Target": target, "Variance %": var})

    tdf = pd.DataFrame(target_rows)
    if not tdf.empty:
        cols = st.columns(min(len(tdf), 5))
        for i, (_, row) in enumerate(tdf.iterrows()):
            with cols[i % len(cols)]:
                target_vs_actual(row["Vertical"], row["Actual"], row["Target"], ccy)

    # Cost efficiency
    st.divider()
    section_header("Cost Efficiency", "Food + labour cost as % of revenue — lower is better")

    if vert_data:
        vdf = pd.DataFrame(vert_data)
        vdf["total_cost_pct"] = vdf["food_cost"] + vdf["labor_cost"]

        fig_cost = go.Figure()
        fig_cost.add_trace(go.Bar(
            x=vdf["vertical"], y=vdf["food_cost"] * 100,
            name="Food Cost %", marker_color=AMBER,
        ))
        fig_cost.add_trace(go.Bar(
            x=vdf["vertical"], y=vdf["labor_cost"] * 100,
            name="Labour Cost %", marker_color="#7B8FA1",
        ))
        fig_cost.update_layout(**PLOTLY_LAYOUT, height=320, barmode="stack",
                                title="Combined Cost % by Vertical")
        fig_cost.update_layout(legend=dict(orientation="h", y=1.12))
        fig_cost.update_yaxes(gridcolor="#2A3950", title_text="% of Revenue")
        st.plotly_chart(fig_cost, use_container_width=True)

    # Headcount summary per vertical
    st.divider()
    section_header("People Summary", "FTE deployment across verticals")

    try:
        headcount = load_headcount()
        latest_m = headcount["month"].max()
        latest_hc = headcount[headcount["month"] == latest_m]
        hc_merged = latest_hc.merge(venues[["venue_id", "vertical"]], on="venue_id", how="left")
        hc_vert = hc_merged.groupby("vertical").agg(
            total_fte=("headcount", "sum"),
            budgeted=("budgeted_headcount", "sum"),
        ).reset_index()
        hc_vert["fill_rate"] = (hc_vert["total_fte"] / hc_vert["budgeted"] * 100).round(1)

        cols = st.columns(min(len(hc_vert), 5))
        for i, (_, row) in enumerate(hc_vert.iterrows()):
            with cols[i % len(cols)]:
                fill_color = GREEN if row["fill_rate"] >= 95 else (AMBER if row["fill_rate"] >= 85 else RED)
                kpi_card(row["vertical"], f"{row['total_fte']:,.0f} FTE",
                         delta=f"Fill rate: {row['fill_rate']:.0f}%",
                         delta_good=row["fill_rate"] >= 90,
                         icon="👷", border_color=fill_color)
    except Exception:
        pass

# ── Tab 4: Savings ─────────────────────────────────────────────

with tab_savings:
    section_header("Savings Pipeline by Vertical",
                    "How procurement savings are distributed across the business")

    savings_rows = []
    for _, s in savings.iterrows():
        if s["venue_ids"] == "all":
            for vert in verticals:
                savings_rows.append({"vertical": vert, "status": s["status"],
                                     "savings": s["annual_savings_aed"] / len(verticals),
                                     "category": s["category"]})
        else:
            sv_ids = str(s["venue_ids"]).split(";")
            matched_verts = venues[venues["venue_id"].isin(sv_ids)]["vertical"].unique()
            for vert in matched_verts:
                savings_rows.append({"vertical": vert, "status": s["status"],
                                     "savings": s["annual_savings_aed"] / max(1, len(matched_verts)),
                                     "category": s["category"]})

    if savings_rows:
        sdf = pd.DataFrame(savings_rows)
        sdf_agg = sdf.groupby(["vertical", "status"])["savings"].sum().reset_index()

        total_captured = sdf[sdf["status"] == "Captured"]["savings"].sum()
        total_pipeline = sdf[sdf["status"] == "Pipeline"]["savings"].sum()
        total_identified = sdf[sdf["status"] == "Identified"]["savings"].sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("Captured", fmt_currency(total_captured, ccy), border_color=GREEN, icon="✅")
        with c2:
            kpi_card("Pipeline", fmt_currency(total_pipeline, ccy), border_color=AMBER, icon="🔄")
        with c3:
            kpi_card("Identified", fmt_currency(total_identified, ccy), border_color=MUTED, icon="🔍")
        with c4:
            total_all = total_captured + total_pipeline + total_identified
            kpi_card("Total Opportunity", fmt_currency(total_all, ccy), border_color=GOLD, icon="💎")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        fig3 = px.bar(
            sdf_agg, x="vertical", y="savings", color="status",
            barmode="stack",
            color_discrete_map={"Captured": GREEN, "Pipeline": AMBER, "Identified": "#9BA8B8"},
            labels={"savings": f"Annual Savings ({ccy})", "vertical": "", "status": "Status"},
        )
        fig3.update_layout(**PLOTLY_LAYOUT, height=360)
        fig3.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig3, use_container_width=True)

        # Savings by category
        st.divider()
        section_header("Savings by Category", "Consolidation, renegotiation, or substitution?")
        cat_sav = sdf.groupby("category")["savings"].sum().reset_index()
        fig_cat = px.pie(
            cat_sav, values="savings", names="category",
            color_discrete_sequence=[GOLD, AMBER, GREEN],
            hole=0.45,
        )
        fig_cat.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_cat.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        empty_state("No savings data available.")

# ── Tab 5: Raw Data ────────────────────────────────────────────

with tab_data:
    section_header("Venue Data Table", "Full sortable list — download for offline analysis")
    venue_table = venues[venues["venue_id"].isin(venue_ids)][
        ["sub_brand", "vertical", "concept_brand", "city", "country", "venue_type", "seat_capacity"]
    ].copy()
    venue_table.columns = ["Venue", "Vertical", "Brand", "City", "Country", "Type", "Capacity"]
    st.dataframe(venue_table.sort_values("Vertical"), use_container_width=True,
                 hide_index=True, height=400)
    download_df(venue_table, "admo_venues.csv", "📥 Download Venue List")
