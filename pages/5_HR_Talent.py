import streamlit as st

st.set_page_config(page_title="HR & Talent | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, section_header,
    kpi_card, download_df, insight_card, persona_banner, rag_badge,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    BORDER, MUTED, DIM,
    PLOTLY_LAYOUT,
)
from lib.data import (
    load_venues, load_headcount, load_succession_map, load_hiring,
    load_daily_ops, get_scope_venue_ids, filter_by_scope,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("HR & Talent", f"Scope: {scope_desc(scope)}")

persona_banner(
    "HR & Talent",
    "CHRO, HR Director, Talent Acquisition Lead",
    ["Are we fully staffed?", "What's blocking new openings?",
     "Who are our succession risks?", "How fast are we hiring?",
     "Where is labour cost highest?", "Which roles are critical?"],
)

headcount = filter_by_scope(load_headcount(), venue_ids)
succession = filter_by_scope(load_succession_map(), venue_ids)
hiring = filter_by_scope(load_hiring(), venue_ids)

if headcount.empty:
    empty_state()
    st.stop()

tab_overview, tab_hiring, tab_succession, tab_labor = st.tabs([
    "👥 Headcount Overview", "📋 Hiring Pipeline", "🔄 Succession Planning", "💰 Labour Cost"
])

# ── Tab 1: Headcount Overview ──────────────────────────────────

with tab_overview:
    section_header("Headcount Summary", "Current staffing levels vs budget across the portfolio")

    latest_month = headcount["month"].max()
    latest_hc = headcount[headcount["month"] == latest_month]
    total_fte = latest_hc["headcount"].sum()
    total_budgeted = latest_hc["budgeted_headcount"].sum()
    fill_rate = total_fte / total_budgeted * 100 if total_budgeted else 0
    vacancy = total_budgeted - total_fte
    open_roles = len(hiring[hiring["status"] == "Open"])
    critical_open = len(hiring[(hiring["status"] == "Open") &
                                ((hiring["criticality"] == "Critical") | (hiring["blocks_opening"] == "Yes"))])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        kpi_card("Total FTE", f"{total_fte:,.0f}", icon="👥", border_color=GOLD)
    with c2:
        kpi_card("Budgeted", f"{total_budgeted:,.0f}", icon="📋")
    with c3:
        fill_color = GREEN if fill_rate >= 95 else (AMBER if fill_rate >= 85 else RED)
        kpi_card("Fill Rate", f"{fill_rate:.1f}%", icon="📊", border_color=fill_color)
    with c4:
        kpi_card("Vacancies", str(vacancy), icon="🔍",
                 border_color=RED if vacancy > 20 else (AMBER if vacancy > 10 else GREEN))
    with c5:
        kpi_card("Open Roles", str(open_roles), icon="📝")
    with c6:
        kpi_card("Critical/Blocking", str(critical_open), icon="🚨",
                 border_color=RED if critical_open > 0 else GREEN)

    # RAG status
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        rag_badge("Fill Rate", "green" if fill_rate >= 95 else ("amber" if fill_rate >= 85 else "red"),
                  f"{fill_rate:.0f}%")
    with r2:
        rag_badge("Critical Hires", "green" if critical_open == 0 else ("amber" if critical_open <= 2 else "red"),
                  f"{critical_open} open")
    with r3:
        # Succession readiness
        no_succ = len(succession[succession["readiness"] == "No Successor"]) if not succession.empty else 0
        rag_badge("Succession Risk", "green" if no_succ == 0 else ("amber" if no_succ <= 3 else "red"),
                  f"{no_succ} gaps")
    with r4:
        filled = hiring[hiring["status"] == "Filled"]
        avg_ttf = filled["days_open"].mean() if not filled.empty else 0
        rag_badge("Time to Fill", "green" if avg_ttf < 45 else ("amber" if avg_ttf < 75 else "red"),
                  f"{avg_ttf:.0f} days avg")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        section_header("FTE by Role Category", "Actual vs budgeted headcount by function")
        role_hc = latest_hc.groupby("role_category").agg(
            actual=("headcount", "sum"),
            budgeted=("budgeted_headcount", "sum"),
        ).reset_index()

        fig_role = go.Figure()
        fig_role.add_trace(go.Bar(
            x=role_hc["role_category"], y=role_hc["actual"],
            name="Actual", marker_color=GOLD,
        ))
        fig_role.add_trace(go.Bar(
            x=role_hc["role_category"], y=role_hc["budgeted"],
            name="Budgeted", marker_color="#2A3950",
        ))
        fig_role.update_layout(**PLOTLY_LAYOUT, height=340, barmode="group")
        fig_role.update_layout(legend=dict(orientation="h", y=1.12))
        fig_role.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_role, use_container_width=True)

        # Role gaps
        role_hc["gap"] = role_hc["budgeted"] - role_hc["actual"]
        biggest_gap = role_hc.loc[role_hc["gap"].idxmax()]
        if biggest_gap["gap"] > 0:
            insight_card("⚠", f"Biggest Gap: {biggest_gap['role_category']}",
                         f"{biggest_gap['gap']:.0f} unfilled positions ({biggest_gap['actual']:.0f}/{biggest_gap['budgeted']:.0f})",
                         AMBER)

    with col_r:
        section_header("Headcount Trend", "18-month actual vs budgeted trajectory")
        monthly_hc = headcount.groupby("month")["headcount"].sum().reset_index()
        monthly_budget = headcount.groupby("month")["budgeted_headcount"].sum().reset_index()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=monthly_hc["month"], y=monthly_hc["headcount"],
            mode="lines+markers", name="Actual",
            line=dict(color=GOLD, width=2),
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly_budget["month"], y=monthly_budget["budgeted_headcount"],
            mode="lines", name="Budgeted",
            line=dict(color="#9BA8B8", width=1.5, dash="dash"),
        ))
        fig_trend.update_layout(**PLOTLY_LAYOUT, height=340)
        fig_trend.update_layout(legend=dict(orientation="h", y=1.12))
        fig_trend.update_yaxes(gridcolor="#2A3950")
        fig_trend.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_trend, use_container_width=True)

    # FTE by venue
    st.divider()
    section_header("FTE by Venue", "Staff deployment across locations")
    venue_hc = latest_hc.groupby("venue_id").agg(
        actual=("headcount", "sum"),
        budgeted=("budgeted_headcount", "sum"),
    ).reset_index()
    venue_hc = venue_hc.merge(venues[["venue_id", "sub_brand", "vertical"]], on="venue_id", how="left")
    venue_hc["fill_rate"] = (venue_hc["actual"] / venue_hc["budgeted"].clip(lower=1) * 100).round(1)
    venue_hc = venue_hc.sort_values("actual", ascending=False)

    display_hc = venue_hc[["sub_brand", "vertical", "actual", "budgeted", "fill_rate"]].rename(columns={
        "sub_brand": "Venue", "vertical": "Vertical", "actual": "Actual FTE",
        "budgeted": "Budgeted", "fill_rate": "Fill Rate %",
    })
    st.dataframe(display_hc, use_container_width=True, hide_index=True, height=300)

# ── Tab 2: Hiring Pipeline ────────────────────────────────────

with tab_hiring:
    section_header("Open Roles & Critical Flags",
                    "Active requisitions — critical and opening-blocking roles highlighted")

    open_hiring = hiring[hiring["status"] == "Open"]

    if open_hiring.empty:
        empty_state("No open roles in scope.")
    else:
        # Summary
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("Total Open", str(len(open_hiring)), icon="📋")
        with c2:
            critical = open_hiring[open_hiring["criticality"] == "Critical"]
            kpi_card("Critical", str(len(critical)), icon="🚨", border_color=RED if len(critical) > 0 else GREEN)
        with c3:
            blocking = open_hiring[open_hiring["blocks_opening"] == "Yes"]
            kpi_card("Blocks Opening", str(len(blocking)), icon="🔒",
                     border_color=RED if len(blocking) > 0 else GREEN)
        with c4:
            avg_days = open_hiring["days_open"].mean()
            kpi_card("Avg Days Open", f"{avg_days:.0f}", icon="⏱",
                     border_color=RED if avg_days > 90 else (AMBER if avg_days > 60 else GREEN))

        # Critical flags
        critical_open = open_hiring[
            (open_hiring["criticality"] == "Critical") | (open_hiring["blocks_opening"] == "Yes")
        ]
        if not critical_open.empty:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            for _, row in critical_open.sort_values("days_open", ascending=False).iterrows():
                vname = venues.loc[venues["venue_id"] == row["venue_id"], "sub_brand"].values
                venue_label = vname[0] if len(vname) else row["venue_id"]
                flags = []
                if row["criticality"] == "Critical":
                    flags.append("CRITICAL")
                if row["blocks_opening"] == "Yes":
                    flags.append("BLOCKS OPENING")
                insight_card("🚨", f"{row['role']} — {venue_label}",
                             f"{' | '.join(flags)} • {row['days_open']:.0f} days open • {row['seniority']}",
                             RED)

        st.divider()
        section_header("Full Open Roles Table")
        display = open_hiring[["position_id", "venue_id", "role", "seniority", "criticality",
                                "days_open", "blocks_opening"]].copy()
        display = display.merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")
        display = display.rename(columns={
            "position_id": "ID", "sub_brand": "Venue", "role": "Role",
            "seniority": "Seniority", "criticality": "Criticality",
            "days_open": "Days Open", "blocks_opening": "Blocks Opening",
        }).drop(columns=["venue_id"])
        st.dataframe(display.sort_values("Days Open", ascending=False),
                     use_container_width=True, hide_index=True, height=350)

    # Time-to-fill analysis
    st.divider()
    section_header("Time-to-Fill Analysis", "How fast are we closing roles?")
    filled = hiring[hiring["status"] == "Filled"]

    if filled.empty:
        empty_state("No filled roles to analyse.")
    else:
        avg_ttf = filled["days_open"].mean()
        median_ttf = filled["days_open"].median()
        total_filled = len(filled)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("Total Filled", str(total_filled), icon="✅", border_color=GREEN)
        with c2:
            kpi_card("Avg Time-to-Fill", f"{avg_ttf:.0f} days", icon="⏱",
                     border_color=GREEN if avg_ttf < 45 else (AMBER if avg_ttf < 75 else RED))
        with c3:
            kpi_card("Median Time-to-Fill", f"{median_ttf:.0f} days", icon="📊")
        with c4:
            slow_fills = len(filled[filled["days_open"] > 90])
            kpi_card("Slow Fills (>90d)", str(slow_fills), icon="🐢",
                     border_color=RED if slow_fills > 3 else AMBER)

        col_l, col_r = st.columns(2)
        with col_l:
            ttf_by_seniority = filled.groupby("seniority")["days_open"].mean().reset_index()
            fig_ttf = px.bar(
                ttf_by_seniority.sort_values("days_open"),
                x="days_open", y="seniority", orientation="h",
                color_discrete_sequence=[GOLD],
                labels={"days_open": "Avg Days", "seniority": ""},
            )
            fig_ttf.update_layout(**PLOTLY_LAYOUT, height=250, showlegend=False,
                                  title="Avg Time-to-Fill by Seniority")
            fig_ttf.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_ttf, use_container_width=True)

        with col_r:
            ttf_by_crit = filled.groupby("criticality")["days_open"].mean().reset_index()
            fig_ttc = px.bar(
                ttf_by_crit.sort_values("days_open"),
                x="days_open", y="criticality", orientation="h",
                color_discrete_sequence=[AMBER],
                labels={"days_open": "Avg Days", "criticality": ""},
            )
            fig_ttc.update_layout(**PLOTLY_LAYOUT, height=250, showlegend=False,
                                  title="Avg Time-to-Fill by Criticality")
            fig_ttc.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_ttc, use_container_width=True)

# ── Tab 3: Succession Planning ─────────────────────────────────

with tab_succession:
    section_header("Succession Map",
                    "Key leadership positions and successor readiness across the portfolio")

    if succession.empty:
        empty_state("No succession data in scope.")
    else:
        # Summary KPIs
        ready_now = len(succession[succession["readiness"] == "Ready Now"])
        in_progress = len(succession[succession["readiness"] == "1-2 Years"])
        no_successor = len(succession[succession["readiness"] == "No Successor"])
        critical_risk = len(succession[succession["risk_level"] == "Critical"])
        high_risk = len(succession[succession["risk_level"] == "High"])

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Ready Now", str(ready_now), icon="✅", border_color=GREEN)
        with c2:
            kpi_card("1-2 Years", str(in_progress), icon="🔄", border_color=AMBER)
        with c3:
            kpi_card("No Successor", str(no_successor), icon="🚨", border_color=RED)
        with c4:
            kpi_card("Critical Risk", str(critical_risk), icon="⚠",
                     border_color=RED if critical_risk > 0 else GREEN)
        with c5:
            kpi_card("High Risk", str(high_risk), icon="📊",
                     border_color=AMBER if high_risk > 0 else GREEN)

        # Critical risk callouts
        if critical_risk > 0 or high_risk > 0:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            critical_rows = succession[succession["risk_level"].isin(["Critical", "High"])]
            for _, row in critical_rows.iterrows():
                vname = venues.loc[venues["venue_id"] == row["venue_id"], "sub_brand"].values
                venue_label = vname[0] if len(vname) else row["venue_id"]
                color = RED if row["risk_level"] == "Critical" else AMBER
                insight_card(
                    "🚨" if row["risk_level"] == "Critical" else "⚠",
                    f"{row['role']} — {venue_label}",
                    f"Incumbent: {row['incumbent_name']} | "
                    f"Readiness: {row['readiness']} | Risk: {row['risk_level']}",
                    color
                )

        st.divider()

        # Readiness distribution
        col_l, col_r = st.columns(2)
        with col_l:
            section_header("Readiness Distribution")
            readiness_dist = succession["readiness"].value_counts().reset_index()
            readiness_dist.columns = ["Readiness", "Count"]
            fig_rd = px.pie(readiness_dist, values="Count", names="Readiness",
                            color_discrete_map={"Ready Now": GREEN, "1-2 Years": AMBER,
                                                "No Successor": RED}, hole=0.45)
            fig_rd.update_layout(**PLOTLY_LAYOUT, height=280)
            fig_rd.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_rd, use_container_width=True)

        with col_r:
            section_header("Risk Distribution")
            risk_dist = succession["risk_level"].value_counts().reset_index()
            risk_dist.columns = ["Risk", "Count"]
            fig_rk = px.pie(risk_dist, values="Count", names="Risk",
                            color_discrete_map={"Low": GREEN, "Medium": AMBER,
                                                "High": RED, "Critical": "#8B0000"}, hole=0.45)
            fig_rk.update_layout(**PLOTLY_LAYOUT, height=280)
            fig_rk.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_rk, use_container_width=True)

        # Full table
        st.divider()
        section_header("Full Succession Table")
        succ_display = succession.merge(
            venues[["venue_id", "sub_brand", "vertical"]], on="venue_id", how="left"
        )[["sub_brand", "vertical", "role", "incumbent_name",
           "successor_name", "readiness", "risk_level"]].rename(
            columns={
                "sub_brand": "Venue", "vertical": "Vertical", "role": "Role",
                "incumbent_name": "Incumbent", "successor_name": "Successor",
                "readiness": "Readiness", "risk_level": "Risk",
            }
        )
        st.dataframe(succ_display.sort_values("Risk", key=lambda s: s.map(
            {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        )), use_container_width=True, hide_index=True, height=400)
        download_df(succ_display, "admo_succession.csv", "📥 Download Succession Data")

# ── Tab 4: Labour Cost ────────────────────────────────────────

with tab_labor:
    section_header("Labour Cost vs Portfolio Benchmark",
                    "Identify venues where labour costs exceed the portfolio median by 3+pp")

    daily_ops = load_daily_ops()

    if not daily_ops.empty:
        portfolio_median = daily_ops["labor_cost_pct"].median()
        scoped_ops = filter_by_scope(daily_ops, venue_ids)

        if not scoped_ops.empty:
            avg_labor = scoped_ops["labor_cost_pct"].mean()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                kpi_card("Scoped Avg Labour", f"{avg_labor:.1%}", icon="💰",
                         border_color=GREEN if avg_labor < 0.25 else (AMBER if avg_labor < 0.30 else RED))
            with c2:
                kpi_card("Portfolio Median", f"{portfolio_median:.1%}", icon="📊")
            with c3:
                above_threshold = len(scoped_ops.groupby("venue_id")["labor_cost_pct"].mean().reset_index().query(
                    f"labor_cost_pct > {portfolio_median + 0.03}"
                ))
                kpi_card("Venues Above +3pp", str(above_threshold), icon="⚠",
                         border_color=RED if above_threshold > 3 else (AMBER if above_threshold > 0 else GREEN))
            with c4:
                # Labour cost per cover
                total_rev = scoped_ops["revenue_total_aed"].sum()
                total_covers = scoped_ops["covers_total"].sum()
                labor_per_cover = total_rev * avg_labor / total_covers if total_covers else 0
                kpi_card("Labour / Cover", fmt_currency(labor_per_cover, ccy), icon="🧾")

            st.divider()

            venue_labor = scoped_ops.merge(
                venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
            ).groupby("sub_brand")["labor_cost_pct"].mean().reset_index()

            df_labor = venue_labor.sort_values("labor_cost_pct").copy()
            df_labor["flag"] = df_labor["labor_cost_pct"].apply(
                lambda x: "Above" if x > portfolio_median + 0.03 else "Normal"
            )
            fig_labor = px.bar(
                df_labor, x="labor_cost_pct", y="sub_brand", orientation="h",
                color="flag",
                color_discrete_map={"Above": RED, "Normal": GOLD},
                labels={"labor_cost_pct": "Labour Cost %", "sub_brand": ""},
            )
            fig_labor.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
            fig_labor.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
            fig_labor.add_vline(x=portfolio_median, line_dash="dash", line_color="#9BA8B8",
                                annotation_text=f"Median {portfolio_median:.0%}")
            st.plotly_chart(fig_labor, use_container_width=True)

            # Trend
            st.divider()
            section_header("Labour Cost Trend", "Is labour cost improving or deteriorating?")
            labor_trend = scoped_ops.copy()
            labor_trend["month"] = labor_trend["date"].dt.to_period("M").dt.to_timestamp()
            labor_monthly = labor_trend.groupby("month")["labor_cost_pct"].mean().reset_index()
            fig_lt = go.Figure()
            fig_lt.add_trace(go.Scatter(
                x=labor_monthly["month"], y=labor_monthly["labor_cost_pct"],
                mode="lines+markers", name="Labour Cost %",
                line=dict(color=GOLD, width=2),
            ))
            fig_lt.add_hline(y=portfolio_median, line_dash="dash", line_color=MUTED,
                             annotation_text="Portfolio Median")
            fig_lt.update_layout(**PLOTLY_LAYOUT, height=280)
            fig_lt.update_yaxes(gridcolor="#2A3950", tickformat=".0%")
            fig_lt.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_lt, use_container_width=True)
