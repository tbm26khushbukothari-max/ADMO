import streamlit as st

st.set_page_config(
    page_title="ADMO Lifestyle Dashboard",
    page_icon="♦",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, render_hero, page_header, metric_card_css, empty_state,
    alert_card, stat_callout, section_header, kpi_card, download_df,
    insight_card, persona_banner, target_vs_actual, rag_badge,
    fmt_currency, fmt_delta, scope_desc,
    GOLD, OFF_WHITE, CARD_BG, BORDER, MUTED, DIM, RED, AMBER, GREEN,
    PLOTLY_LAYOUT, VERTICAL_COLORS, SEVERITY_COLORS,
)
from lib.data import (
    load_monthly_summary, load_venues, load_alerts, load_guests,
    load_transactions, load_daily_ops, load_brand_health, load_plan_targets,
    load_events, load_hiring, load_headcount,
    get_scope_venue_ids, filter_by_scope, compute_growth_pct,
    compute_budget_variance, compute_revpash,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

# ── Hero ───────────────────────────────────────────────────────
render_hero()

persona_banner(
    "Executive Overview",
    "Group CEO, Board Members, Investors",
    ["Are we on track vs plan?", "What needs my attention?", "Where's the growth?",
     "How healthy is the portfolio?", "What's the guest base doing?"],
)

summary = filter_by_scope(load_monthly_summary(), venue_ids)
alerts = filter_by_scope(load_alerts(), venue_ids)
targets = load_plan_targets()

if summary.empty:
    empty_state()
    st.stop()

# ── Compute KPIs with period-over-period deltas ────────────────

monthly_rev = summary.groupby("month")["revenue_aed"].sum().sort_index()
total_rev = summary["revenue_aed"].sum()
total_covers = summary["covers"].sum()
avg_check = total_rev / total_covers if total_covers else 0
active_venues = summary["venue_id"].nunique()
avg_satisfaction = summary["avg_satisfaction"].mean()
growth = compute_growth_pct(load_monthly_summary(), venue_ids)

# Budget variance
actual_rev, target_rev, budget_var = compute_budget_variance(summary, targets, venue_ids)

# Recent 3 months vs prior 3 months for deltas
if len(monthly_rev) >= 6:
    recent_rev = monthly_rev.iloc[-3:].sum()
    prior_rev = monthly_rev.iloc[-6:-3].sum()
    rev_delta, rev_good = fmt_delta(recent_rev, prior_rev)
else:
    rev_delta, rev_good = None, True

monthly_covers = summary.groupby("month")["covers"].sum().sort_index()
if len(monthly_covers) >= 6:
    cov_delta, cov_good = fmt_delta(monthly_covers.iloc[-3:].sum(), monthly_covers.iloc[-6:-3].sum())
else:
    cov_delta, cov_good = None, True

# ── Pulse KPIs — what the CEO sees first ───────────────────────

section_header("Portfolio Pulse", "The numbers that matter most — updated in real-time")

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    kpi_card("Portfolio Revenue", fmt_currency(total_rev, ccy),
             delta=rev_delta, delta_good=rev_good, icon="💰", border_color=GOLD)
with c2:
    kpi_card("Total Covers", f"{total_covers:,.0f}",
             delta=cov_delta, delta_good=cov_good, icon="🍽")
with c3:
    kpi_card("Avg Check", fmt_currency(avg_check, ccy), icon="🧾")
with c4:
    kpi_card("Active Venues", str(active_venues), icon="📍")
with c5:
    sat_color = GREEN if avg_satisfaction >= 8 else (AMBER if avg_satisfaction >= 7 else RED)
    kpi_card("Avg Satisfaction", f"{avg_satisfaction:.1f}/10", icon="⭐", border_color=sat_color)
with c6:
    growth_color = GREEN if growth >= 0 else RED
    kpi_card("QoQ Growth", f"{growth:+.1f}%",
             border_color=growth_color, icon="📈")

# ── Budget vs Actual row ────────────────────────────────────────

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

c_b1, c_b2, c_b3, c_b4 = st.columns(4)
with c_b1:
    target_vs_actual("Revenue vs Plan", actual_rev, target_rev, ccy)
with c_b2:
    # NPS vs target
    daily_ops = load_daily_ops()
    scoped_ops = filter_by_scope(daily_ops, venue_ids)
    avg_nps = scoped_ops["nps_score"].mean() if not scoped_ops.empty else 0
    nps_target = targets[targets["venue_id"].isin(venue_ids)]["nps_target"].mean() if not targets.empty else 70
    target_vs_actual("NPS vs Target", avg_nps, nps_target, ccy,
                     fmt_fn=lambda v: f"{v:.0f}")
with c_b3:
    # Covers vs target
    total_cov_target = targets[targets["venue_id"].isin(venue_ids)]["covers_target"].sum()
    target_vs_actual("Covers vs Plan", total_covers, total_cov_target, ccy,
                     fmt_fn=lambda v: f"{v:,.0f}")
with c_b4:
    # RevPASH — use target_vs_actual with a benchmark of AED 60
    revpash = compute_revpash(daily_ops, venues, venue_ids)
    target_vs_actual("RevPASH", revpash, 60, ccy)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── Tabbed main content ──────────────────────────────────────────

tab_overview, tab_risk, tab_snapshot, tab_actions = st.tabs([
    "📊 Revenue & Trends", "🚨 Alerts & Risk", "📋 Portfolio Snapshot", "🎯 CEO Action Items"
])

# ── Tab 1: Revenue & Trends ────────────────────────────────────

with tab_overview:
    col_chart, col_insight = st.columns([3, 1])

    with col_chart:
        section_header("Monthly Revenue by Vertical",
                        "Stacked area shows revenue contribution and trajectory per vertical")
        monthly = summary.groupby(["month", "vertical"])["revenue_aed"].sum().reset_index()
        if ccy == "USD":
            monthly["revenue_aed"] *= 1 / 3.67
        fig = px.area(
            monthly, x="month", y="revenue_aed", color="vertical",
            color_discrete_map=VERTICAL_COLORS,
            labels={"revenue_aed": f"Revenue ({ccy})", "month": "", "vertical": "Vertical"},
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=380)
        fig.update_yaxes(gridcolor="#2A3950", gridwidth=0.5)
        fig.update_xaxes(gridcolor="#2A3950", gridwidth=0.5)
        st.plotly_chart(fig, use_container_width=True)

    with col_insight:
        section_header("Quick Insights", "Auto-detected highlights")

        # Top performing vertical
        vert_totals = summary.groupby("vertical")["revenue_aed"].sum()
        if not vert_totals.empty:
            top_vert = vert_totals.idxmax()
            top_pct = vert_totals.max() / vert_totals.sum() * 100
            insight_card("🏆", "Top Vertical", f"{top_vert} — {top_pct:.0f}% of portfolio revenue", GREEN)

        # Growth signal
        if growth >= 5:
            insight_card("📈", "Strong Growth", f"QoQ Revenue: {growth:+.1f}%", GREEN)
        elif growth >= 0:
            insight_card("📊", "Moderate Growth", f"QoQ Revenue: {growth:+.1f}%", AMBER)
        else:
            insight_card("📉", "Declining", f"QoQ Revenue: {growth:+.1f}%", RED)

        # Alert count
        open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]
        red_count = len(open_alerts[open_alerts["severity"] == "Red"])
        amber_count = len(open_alerts[open_alerts["severity"] == "Amber"])
        if red_count > 0:
            insight_card("🚨", f"{red_count} Red Alert(s)", f"+ {amber_count} Amber — see Alerts tab", RED)
        elif amber_count > 0:
            insight_card("⚠", f"{amber_count} Amber Alert(s)", "No red alerts — monitoring", AMBER)
        else:
            insight_card("✅", "All Clear", "No active alerts in scope", GREEN)

        # Budget tracking
        if budget_var >= 0:
            insight_card("🎯", "On Track", f"Revenue {budget_var:+.1f}% vs plan", GREEN)
        elif budget_var >= -5:
            insight_card("🎯", "Near Plan", f"Revenue {budget_var:+.1f}% vs plan", AMBER)
        else:
            insight_card("🎯", "Below Plan", f"Revenue {budget_var:+.1f}% vs plan — review needed", RED)

        # Satisfaction insight
        if avg_satisfaction >= 8.0:
            insight_card("⭐", "Guest Delight", f"Avg satisfaction {avg_satisfaction:.1f}/10 — above threshold", GREEN)
        elif avg_satisfaction >= 7.0:
            insight_card("⭐", "Satisfaction OK", f"Avg {avg_satisfaction:.1f}/10 — room to improve", AMBER)
        else:
            insight_card("⭐", "Satisfaction Risk", f"Avg {avg_satisfaction:.1f}/10 — below 7.0 threshold", RED)

    # Revenue breakdown: Vertical vs Region side by side
    col_l, col_r = st.columns(2)

    with col_l:
        section_header("Revenue by Vertical", "Who's contributing what to the portfolio?")
        vert_rev = summary.groupby("vertical")["revenue_aed"].sum().sort_values(ascending=True).reset_index()
        if ccy == "USD":
            vert_rev["revenue_aed"] *= 1 / 3.67
        fig2 = px.bar(
            vert_rev, x="revenue_aed", y="vertical", orientation="h",
            color="vertical", color_discrete_map=VERTICAL_COLORS,
            labels={"revenue_aed": f"Revenue ({ccy})", "vertical": ""},
        )
        fig2.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
        fig2.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        section_header("Revenue by Region", "Geographic concentration and diversification")
        region_rev = summary.groupby("region")["revenue_aed"].sum().sort_values(ascending=False).reset_index()
        if ccy == "USD":
            region_rev["revenue_aed"] *= 1 / 3.67
        fig3 = px.bar(
            region_rev, x="region", y="revenue_aed",
            color_discrete_sequence=[GOLD],
            labels={"revenue_aed": f"Revenue ({ccy})", "region": ""},
        )
        fig3.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
        fig3.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig3, use_container_width=True)

    # Satisfaction & NPS trend
    st.divider()
    section_header("Operational Trends", "Satisfaction and NPS trajectory across the portfolio")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        if not scoped_ops.empty:
            sat_trend = scoped_ops.copy()
            sat_trend["month"] = sat_trend["date"].dt.to_period("M").dt.to_timestamp()
            sat_monthly = sat_trend.groupby("month")["avg_satisfaction"].mean().reset_index()
            fig_sat = go.Figure()
            fig_sat.add_trace(go.Scatter(
                x=sat_monthly["month"], y=sat_monthly["avg_satisfaction"],
                mode="lines+markers", name="Satisfaction",
                line=dict(color=GOLD, width=2),
                fill="tozeroy", fillcolor="rgba(201,169,97,0.08)",
            ))
            fig_sat.update_layout(**PLOTLY_LAYOUT, height=260, title="Monthly Avg Satisfaction")
            fig_sat.update_yaxes(gridcolor="#2A3950", range=[6, 10])
            fig_sat.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_sat, use_container_width=True)

    with col_s2:
        if not scoped_ops.empty:
            nps_trend = scoped_ops.copy()
            nps_trend["month"] = nps_trend["date"].dt.to_period("M").dt.to_timestamp()
            nps_monthly = nps_trend.groupby("month")["nps_score"].mean().reset_index()
            fig_nps = go.Figure()
            fig_nps.add_trace(go.Scatter(
                x=nps_monthly["month"], y=nps_monthly["nps_score"],
                mode="lines+markers", name="NPS",
                line=dict(color=GREEN, width=2),
                fill="tozeroy", fillcolor="rgba(90,125,60,0.08)",
            ))
            fig_nps.update_layout(**PLOTLY_LAYOUT, height=260, title="Monthly Avg NPS")
            fig_nps.update_yaxes(gridcolor="#2A3950")
            fig_nps.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_nps, use_container_width=True)

# ── Tab 2: Alerts & Risk ──────────────────────────────────────

with tab_risk:
    section_header("Exception Alerts",
                    "Active issues requiring attention — sorted by severity")

    open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]

    # Summary strip
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Total Active", str(len(open_alerts)))
    col_r2.metric("Red", str(len(open_alerts[open_alerts["severity"] == "Red"])))
    col_r3.metric("Amber", str(len(open_alerts[open_alerts["severity"] == "Amber"])))
    col_r4.metric("Investigating", str(len(open_alerts[open_alerts["status"] == "Investigating"])))

    st.divider()

    if open_alerts.empty:
        empty_state("No active alerts in scope. All clear.")
    else:
        # Group by severity
        for severity in ["Red", "Amber", "Green"]:
            sev_alerts = open_alerts[open_alerts["severity"] == severity]
            if not sev_alerts.empty:
                st.markdown(
                    f"<div style='color:{SEVERITY_COLORS.get(severity, MUTED)}; font-weight:600; "
                    f"font-size:0.9rem; margin:12px 0 6px 0;'>"
                    f"● {severity} Alerts ({len(sev_alerts)})</div>",
                    unsafe_allow_html=True,
                )
                for _, a in sev_alerts.iterrows():
                    vname = venues.loc[venues["venue_id"] == a["venue_id"], "sub_brand"].values
                    alert_card(
                        a["severity"], a["headline"],
                        venue_name=vname[0] if len(vname) else a["venue_id"],
                        description=a.get("description", ""),
                        owner=a["owner"], status=a["status"],
                    )

    # Operational risk summary
    st.divider()
    section_header("Operational Risk Heatmap",
                    "Venues with food cost or labor cost above portfolio threshold")

    if not scoped_ops.empty:
        all_ops = load_daily_ops()
        food_med = all_ops["food_cost_pct"].median()
        labor_med = all_ops["labor_cost_pct"].median()

        venue_risk = scoped_ops.merge(
            venues[["venue_id", "sub_brand", "vertical"]], on="venue_id", how="left"
        ).groupby(["sub_brand", "vertical"]).agg(
            food_cost=("food_cost_pct", "mean"),
            labor_cost=("labor_cost_pct", "mean"),
            nps=("nps_score", "mean"),
            occupancy=("occupancy_pct", "mean"),
        ).reset_index()

        venue_risk["food_flag"] = venue_risk["food_cost"] > food_med + 0.03
        venue_risk["labor_flag"] = venue_risk["labor_cost"] > labor_med + 0.03
        venue_risk["nps_flag"] = venue_risk["nps"] < 30
        venue_risk["risk_count"] = venue_risk[["food_flag", "labor_flag", "nps_flag"]].sum(axis=1)

        flagged = venue_risk[venue_risk["risk_count"] > 0].sort_values("risk_count", ascending=False)
        if not flagged.empty:
            for _, row in flagged.iterrows():
                flags = []
                if row["food_flag"]:
                    flags.append(f"Food cost {row['food_cost']:.1%}")
                if row["labor_flag"]:
                    flags.append(f"Labor cost {row['labor_cost']:.1%}")
                if row["nps_flag"]:
                    flags.append(f"NPS {row['nps']:.0f}")
                alert_card("Amber" if row["risk_count"] == 1 else "Red",
                           row["sub_brand"],
                           description=" | ".join(flags),
                           venue_name=row["vertical"])
        else:
            insight_card("✅", "All Within Threshold",
                         "No venues flagged for cost or NPS risk", GREEN)

# ── Tab 3: Portfolio Snapshot ──────────────────────────────────

with tab_snapshot:
    section_header("Portfolio at a Glance",
                    "Every venue in scope with key metrics — sortable, downloadable")

    # Build a per-venue summary table
    venue_stats = summary.groupby("venue_id").agg(
        revenue=("revenue_aed", "sum"),
        covers=("covers", "sum"),
        avg_check=("avg_check", "mean"),
        avg_satisfaction=("avg_satisfaction", "mean"),
    ).reset_index()
    venue_stats = venue_stats.merge(
        venues[["venue_id", "sub_brand", "vertical", "city", "country", "seat_capacity"]],
        on="venue_id", how="left",
    )

    # Add operational metrics
    if not scoped_ops.empty:
        ops_avg = scoped_ops.groupby("venue_id").agg(
            avg_nps=("nps_score", "mean"),
            avg_occupancy=("occupancy_pct", "mean"),
            avg_food_cost=("food_cost_pct", "mean"),
            avg_labor_cost=("labor_cost_pct", "mean"),
        ).reset_index()
        venue_stats = venue_stats.merge(ops_avg, on="venue_id", how="left")

    venue_stats["avg_check"] = venue_stats["avg_check"].round(0)
    venue_stats["avg_satisfaction"] = venue_stats["avg_satisfaction"].round(1)

    display_cols = ["sub_brand", "vertical", "city", "country", "revenue",
                    "covers", "avg_check", "avg_satisfaction", "seat_capacity"]
    col_names = {"sub_brand": "Venue", "vertical": "Vertical", "city": "City",
                 "country": "Country", "revenue": f"Revenue ({ccy})",
                 "covers": "Covers", "avg_check": "Avg Check",
                 "avg_satisfaction": "Satisfaction", "seat_capacity": "Capacity"}

    if "avg_nps" in venue_stats.columns:
        display_cols.extend(["avg_nps", "avg_occupancy", "avg_food_cost", "avg_labor_cost"])
        col_names.update({
            "avg_nps": "NPS", "avg_occupancy": "Occupancy %",
            "avg_food_cost": "Food Cost %", "avg_labor_cost": "Labor Cost %",
        })
        venue_stats["avg_nps"] = venue_stats["avg_nps"].round(0)
        venue_stats["avg_occupancy"] = (venue_stats["avg_occupancy"] * 100).round(1)
        venue_stats["avg_food_cost"] = (venue_stats["avg_food_cost"] * 100).round(1)
        venue_stats["avg_labor_cost"] = (venue_stats["avg_labor_cost"] * 100).round(1)

    display_df = venue_stats[display_cols].rename(columns=col_names)
    if ccy == "USD":
        display_df[f"Revenue ({ccy})"] = (display_df[f"Revenue ({ccy})"] / 3.67).round(0)

    st.dataframe(
        display_df.sort_values(f"Revenue ({ccy})", ascending=False),
        use_container_width=True, hide_index=True, height=460,
    )
    download_df(display_df, "admo_portfolio_snapshot.csv", "📥 Download Portfolio Data")

# ── Tab 4: CEO Action Items ──────────────────────────────────

with tab_actions:
    section_header("CEO Action Items",
                    "Auto-generated priorities based on portfolio data — what needs your attention now")

    action_items = []

    # 1. Budget miss
    if budget_var < -5:
        action_items.append(("🔴", "Revenue Below Plan",
                             f"Portfolio revenue is {budget_var:.1f}% below plan. "
                             f"Actual: {fmt_currency(actual_rev, ccy)} vs Target: {fmt_currency(target_rev, ccy)}. "
                             f"Review underperforming verticals.", RED))

    # 2. Red alerts
    open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]
    red_alerts = open_alerts[open_alerts["severity"] == "Red"]
    if len(red_alerts) > 0:
        action_items.append(("🚨", f"{len(red_alerts)} Red Alert(s) Active",
                             "Escalated issues requiring Board-level awareness. "
                             "See Alerts & Risk tab for details.", RED))

    # 3. Critical hiring
    try:
        hiring = load_hiring()
        scoped_hiring = filter_by_scope(hiring, venue_ids)
        critical_open = scoped_hiring[
            (scoped_hiring["status"] == "Open") &
            ((scoped_hiring["criticality"] == "Critical") | (scoped_hiring["blocks_opening"] == "Yes"))
        ]
        if len(critical_open) > 0:
            max_days = critical_open["days_open"].max()
            action_items.append(("👷", f"{len(critical_open)} Critical Hire(s) Pending",
                                 f"Roles blocking operations or openings. Longest open: {max_days:.0f} days. "
                                 f"See HR & Talent page.", AMBER))
    except Exception:
        pass

    # 4. Satisfaction drop
    if avg_satisfaction < 7.0:
        action_items.append(("⭐", "Satisfaction Below Threshold",
                             f"Portfolio avg satisfaction is {avg_satisfaction:.1f}/10, "
                             f"below the 7.0 minimum. Guest experience review needed.", RED))

    # 5. Growth stall
    if -5 < growth < 0:
        action_items.append(("📉", "Revenue Contraction",
                             f"QoQ growth is {growth:+.1f}%. Investigate venue-level drivers.", AMBER))
    elif growth < -5:
        action_items.append(("📉", "Significant Revenue Decline",
                             f"QoQ growth is {growth:+.1f}%. Urgent review required.", RED))

    # 6. Brand health issues
    try:
        health = load_brand_health()
        latest_m = health["month"].max()
        latest_health = health[health["month"] == latest_m]
        struggling = latest_health[latest_health["health_score"] < 65]
        if len(struggling) > 0:
            brands_list = ", ".join(struggling["brand"].tolist())
            action_items.append(("🏥", "Brand Health Warning",
                                 f"{brands_list} scored below 65/100 on composite health. "
                                 f"See Brands page for sub-score breakdown.", AMBER))
    except Exception:
        pass

    if not action_items:
        insight_card("✅", "No Urgent Actions", "Portfolio is performing within expected parameters.", GREEN)
    else:
        for icon, title, body, color in action_items:
            insight_card(icon, title, body, color)

    # Quick RAG status summary
    st.divider()
    section_header("Portfolio RAG Status", "Traffic-light summary across key dimensions")
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        rag_badge("Revenue", "green" if budget_var >= 0 else ("amber" if budget_var >= -5 else "red"),
                  f"{budget_var:+.1f}% vs plan")
    with r2:
        rag_badge("Growth", "green" if growth >= 5 else ("amber" if growth >= 0 else "red"),
                  f"{growth:+.1f}% QoQ")
    with r3:
        rag_badge("Satisfaction", "green" if avg_satisfaction >= 8 else ("amber" if avg_satisfaction >= 7 else "red"),
                  f"{avg_satisfaction:.1f}/10")
    with r4:
        rag_badge("Alerts", "green" if len(red_alerts) == 0 else ("amber" if len(red_alerts) <= 2 else "red"),
                  f"{len(red_alerts)} red, {len(open_alerts[open_alerts['severity'] == 'Amber'])} amber")
    with r5:
        rag_badge("NPS", "green" if avg_nps >= 50 else ("amber" if avg_nps >= 30 else "red"),
                  f"Avg {avg_nps:.0f}")

st.divider()

# ── Cross-brand intelligence callout ──────────────────────────

guests = load_guests()
multi = guests[guests["brands_visited_count"] >= 2]
multi_pct_base = len(multi) / len(guests) * 100 if len(guests) else 0
multi_ltv = multi["lifetime_spend_aed"].sum()
total_ltv = guests["lifetime_spend_aed"].sum()
multi_pct_rev = multi_ltv / total_ltv * 100 if total_ltv else 0

stat_callout(
    "Cross-Brand Intelligence",
    f"{multi_pct_base:.0f}% of guests visit 2+ brands → {multi_pct_rev:.0f}% of revenue",
    sub_text=f"{len(multi):,} multi-brand guests out of {len(guests):,} total"
)
