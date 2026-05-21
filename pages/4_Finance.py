import streamlit as st

st.set_page_config(page_title="Finance | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, section_header,
    kpi_card, download_df, stat_callout, insight_card, persona_banner,
    target_vs_actual,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN,
    CARD_BG, BORDER, MUTED, DIM,
    PLOTLY_LAYOUT,
)
from lib.data import (
    load_monthly_summary, load_venues, load_daily_ops, load_events,
    load_savings, load_plan_targets,
    get_scope_venue_ids, filter_by_scope, compute_budget_variance,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Finance", f"Scope: {scope_desc(scope)}")

persona_banner(
    "Finance",
    "CFO, Finance Director, Controller",
    ["What's the P&L?", "Are we on budget?", "Where are cost overruns?",
     "What's the gross margin?", "Where are savings opportunities?",
     "What's our FX exposure?"],
)

summary = filter_by_scope(load_monthly_summary(), venue_ids)
daily_ops = filter_by_scope(load_daily_ops(), venue_ids)
events = filter_by_scope(load_events(), venue_ids)
savings = load_savings()
targets = load_plan_targets()

if summary.empty:
    empty_state()
    st.stop()

tab_pl, tab_budget, tab_costs, tab_savings, tab_fx = st.tabs([
    "📊 P&L Overview", "🎯 Budget vs Actual", "📉 Cost Analysis",
    "💰 Savings Tracker", "💱 Currency Exposure"
])

# ── Tab 1: P&L ────────────────────────────────────────────────

with tab_pl:
    total_rev = summary["revenue_aed"].sum()
    food_rev = summary["food_revenue_aed"].sum()
    bev_rev = summary["beverage_revenue_aed"].sum()

    avg_food_cost_pct = daily_ops["food_cost_pct"].mean() if not daily_ops.empty else 0
    avg_labor_cost_pct = daily_ops["labor_cost_pct"].mean() if not daily_ops.empty else 0
    food_cost = total_rev * avg_food_cost_pct
    labor_cost = total_rev * avg_labor_cost_pct
    gross_margin = total_rev - food_cost - labor_cost
    gm_pct = gross_margin / total_rev * 100 if total_rev else 0
    events_rev = events["total_revenue_aed"].sum() if not events.empty else 0

    # Estimated GOP (Gross Operating Profit)
    # Assume other costs ~15% of revenue (utilities, marketing, maintenance)
    other_costs_pct = 0.15
    other_costs = total_rev * other_costs_pct
    gop = gross_margin - other_costs
    gop_pct = gop / total_rev * 100 if total_rev else 0

    section_header("Profit & Loss Summary",
                    "Revenue, costs, margins and estimated GOP for the selected scope")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Revenue", fmt_currency(total_rev, ccy), icon="💰", border_color=GOLD)
    with c2:
        kpi_card("Food Cost", fmt_currency(food_cost, ccy),
                 delta=f"{avg_food_cost_pct:.1%} of rev", delta_good=avg_food_cost_pct < 0.30,
                 icon="🥘", border_color=AMBER if avg_food_cost_pct >= 0.30 else GREEN)
    with c3:
        kpi_card("Labour Cost", fmt_currency(labor_cost, ccy),
                 delta=f"{avg_labor_cost_pct:.1%} of rev", delta_good=avg_labor_cost_pct < 0.25,
                 icon="👷", border_color=AMBER if avg_labor_cost_pct >= 0.25 else GREEN)
    with c4:
        gm_color = GREEN if gm_pct >= 50 else (AMBER if gm_pct >= 40 else RED)
        kpi_card("Gross Margin", fmt_currency(gross_margin, ccy),
                 delta=f"{gm_pct:.1f}%", delta_good=gm_pct >= 45,
                 icon="📈", border_color=gm_color)
    with c5:
        gop_color = GREEN if gop_pct >= 35 else (AMBER if gop_pct >= 25 else RED)
        kpi_card("Est. GOP", fmt_currency(gop, ccy),
                 delta=f"{gop_pct:.1f}%", delta_good=gop_pct >= 30,
                 icon="🏦", border_color=gop_color)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        food_pct = food_rev / total_rev * 100 if total_rev else 0
        kpi_card("Food Revenue", fmt_currency(food_rev, ccy),
                 delta=f"{food_pct:.0f}% of total", icon="🍴")
    with c6:
        bev_pct = bev_rev / total_rev * 100 if total_rev else 0
        kpi_card("Beverage Revenue", fmt_currency(bev_rev, ccy),
                 delta=f"{bev_pct:.0f}% of total", icon="🍷")
    with c7:
        kpi_card("Events Revenue", fmt_currency(events_rev, ccy),
                 delta=f"{events_rev/total_rev*100:.1f}% of total" if total_rev else "",
                 icon="🎉")
    with c8:
        kpi_card("Avg Check", fmt_currency(
            total_rev / summary["covers"].sum() if summary["covers"].sum() else 0, ccy),
                 icon="🧾")

    # P&L waterfall chart
    st.divider()
    section_header("P&L Waterfall", "Visual breakdown from revenue to GOP")
    fig_wf = go.Figure(go.Waterfall(
        name="P&L",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Revenue", "Food Cost", "Labour Cost", "Other Costs", "GOP"],
        y=[total_rev, -food_cost, -labor_cost, -other_costs, gop],
        connector={"line": {"color": MUTED}},
        increasing={"marker": {"color": GREEN}},
        decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": GOLD}},
        text=[fmt_currency(total_rev, ccy), fmt_currency(-food_cost, ccy),
              fmt_currency(-labor_cost, ccy), fmt_currency(-other_costs, ccy),
              fmt_currency(gop, ccy)],
        textposition="outside",
        textfont=dict(color=OFF_WHITE, size=10),
    ))
    fig_wf.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
    fig_wf.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_wf, use_container_width=True)

    # Revenue trend
    st.divider()
    section_header("Monthly Revenue Trend")
    monthly = summary.groupby("month")["revenue_aed"].sum().reset_index()
    if ccy == "USD":
        monthly["revenue_aed"] *= 1 / 3.67
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        x=monthly["month"], y=monthly["revenue_aed"],
        marker_color=GOLD, name="Revenue",
    ))
    fig_rev.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
    fig_rev.update_yaxes(gridcolor="#2A3950")
    fig_rev.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_rev, use_container_width=True)

# ── Tab 2: Budget vs Actual ──────────────────────────────────

with tab_budget:
    section_header("Revenue: Plan vs Actual",
                    "Monthly actuals vs targets — are we tracking to plan?")

    # Monthly comparison
    monthly_actual = summary.groupby("month")["revenue_aed"].sum().reset_index()
    monthly_actual.columns = ["month", "actual"]

    scoped_targets = targets[targets["venue_id"].isin(venue_ids)]
    if not scoped_targets.empty:
        scoped_targets["month"] = pd.to_datetime(scoped_targets["month"])
        monthly_target = scoped_targets.groupby("month")["revenue_target_aed"].sum().reset_index()
        monthly_target.columns = ["month", "target"]

        budget_df = monthly_actual.merge(monthly_target, on="month", how="outer").fillna(0)
        budget_df["variance"] = budget_df["actual"] - budget_df["target"]
        budget_df["variance_pct"] = (budget_df["variance"] / budget_df["target"].clip(lower=1) * 100)

        # Summary KPIs
        total_actual = budget_df["actual"].sum()
        total_target = budget_df["target"].sum()
        total_var = (total_actual - total_target) / total_target * 100 if total_target else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            target_vs_actual("Total Revenue", total_actual, total_target, ccy)
        with c2:
            # Covers vs target
            actual_covers = summary["covers"].sum()
            target_covers = scoped_targets["covers_target"].sum()
            target_vs_actual("Total Covers", actual_covers, target_covers, ccy,
                             fmt_fn=lambda v: f"{v:,.0f}")
        with c3:
            # Months on/above plan
            months_on_plan = len(budget_df[budget_df["variance_pct"] >= -2])
            total_months = len(budget_df[budget_df["target"] > 0])
            kpi_card("Months On Plan", f"{months_on_plan}/{total_months}",
                     delta="Within 2% of target", delta_good=months_on_plan > total_months * 0.6,
                     icon="🎯", border_color=GREEN if months_on_plan > total_months * 0.7 else AMBER)
        with c4:
            # Consecutive misses
            recent_miss = budget_df[budget_df["target"] > 0].tail(3)
            misses = len(recent_miss[recent_miss["variance_pct"] < -5])
            kpi_card("Recent Misses", f"{misses} of last 3 months",
                     delta="Below 5% threshold", delta_good=misses == 0,
                     icon="⚠", border_color=RED if misses >= 2 else (AMBER if misses == 1 else GREEN))

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        # Chart
        fig_budget = go.Figure()
        fig_budget.add_trace(go.Bar(
            x=budget_df["month"], y=budget_df["actual"],
            name="Actual", marker_color=GOLD,
        ))
        fig_budget.add_trace(go.Scatter(
            x=budget_df["month"], y=budget_df["target"],
            mode="lines+markers", name="Target",
            line=dict(color=RED, width=2, dash="dash"),
            marker=dict(size=6),
        ))
        fig_budget.update_layout(**PLOTLY_LAYOUT, height=340)
        fig_budget.update_layout(legend=dict(orientation="h", y=1.12))
        fig_budget.update_yaxes(gridcolor="#2A3950")
        fig_budget.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_budget, use_container_width=True)

        # Variance heatmap by month
        st.divider()
        section_header("Monthly Variance Detail", "Red = over 5% below plan")
        var_display = budget_df[budget_df["target"] > 0][["month", "actual", "target", "variance", "variance_pct"]].copy()
        var_display.columns = ["Month", f"Actual ({ccy})", f"Target ({ccy})", f"Variance ({ccy})", "Variance %"]
        var_display["Month"] = var_display["Month"].dt.strftime("%b %Y")
        var_display[f"Actual ({ccy})"] = var_display[f"Actual ({ccy})"].apply(lambda x: f"{x:,.0f}")
        var_display[f"Target ({ccy})"] = var_display[f"Target ({ccy})"].apply(lambda x: f"{x:,.0f}")
        var_display[f"Variance ({ccy})"] = var_display[f"Variance ({ccy})"].apply(lambda x: f"{x:+,.0f}")
        var_display["Variance %"] = var_display["Variance %"].apply(lambda x: f"{x:+.1f}%")
        st.dataframe(var_display, use_container_width=True, hide_index=True)
    else:
        empty_state("No target data available for scope.")

# ── Tab 3: Cost Analysis ──────────────────────────────────────

with tab_costs:
    section_header("Cost Structure vs Portfolio Benchmark",
                    "Red = above median+3pp — flag venues with cost discipline issues")

    if not daily_ops.empty:
        all_ops = load_daily_ops()
        portfolio_food_median = all_ops["food_cost_pct"].median()
        portfolio_labor_median = all_ops["labor_cost_pct"].median()

        venue_costs = daily_ops.merge(
            venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
        ).groupby("sub_brand").agg(
            food_cost=("food_cost_pct", "mean"),
            labor_cost=("labor_cost_pct", "mean"),
        ).reset_index()
        venue_costs["prime_cost"] = venue_costs["food_cost"] + venue_costs["labor_cost"]

        # Summary
        above_food = len(venue_costs[venue_costs["food_cost"] > portfolio_food_median + 0.03])
        above_labor = len(venue_costs[venue_costs["labor_cost"] > portfolio_labor_median + 0.03])
        avg_prime = venue_costs["prime_cost"].mean()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Portfolio Food Median", f"{portfolio_food_median:.1%}")
        c2.metric("Venues Above (Food)", str(above_food))
        c3.metric("Portfolio Labour Median", f"{portfolio_labor_median:.1%}")
        c4.metric("Venues Above (Labour)", str(above_labor))
        c5.metric("Avg Prime Cost", f"{avg_prime:.1%}")

        # Prime cost insight
        if avg_prime > 0.55:
            insight_card("🚨", "Prime Cost Warning",
                         f"Average prime cost is {avg_prime:.1%} — above the 55% threshold. "
                         f"Review venues flagged below.", RED)
        elif avg_prime > 0.50:
            insight_card("⚠", "Prime Cost Monitoring",
                         f"Average prime cost is {avg_prime:.1%} — approaching 55% threshold.", AMBER)
        else:
            insight_card("✅", "Prime Cost Healthy",
                         f"Average prime cost is {avg_prime:.1%} — within acceptable range.", GREEN)

        st.divider()
        col_l, col_r = st.columns(2)

        with col_l:
            df_food = venue_costs.sort_values("food_cost").copy()
            df_food["flag"] = df_food["food_cost"].apply(
                lambda x: "Above" if x > portfolio_food_median + 0.03 else "Normal"
            )
            fig_food = px.bar(
                df_food, x="food_cost", y="sub_brand", orientation="h",
                color="flag",
                color_discrete_map={"Above": RED, "Normal": GOLD},
                labels={"food_cost": "Food Cost %", "sub_brand": ""},
            )
            fig_food.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False, title="Food Cost %")
            fig_food.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
            fig_food.add_vline(x=portfolio_food_median, line_dash="dash", line_color="#9BA8B8",
                               annotation_text=f"Median {portfolio_food_median:.0%}")
            st.plotly_chart(fig_food, use_container_width=True)

        with col_r:
            df_labor = venue_costs.sort_values("labor_cost").copy()
            df_labor["flag"] = df_labor["labor_cost"].apply(
                lambda x: "Above" if x > portfolio_labor_median + 0.03 else "Normal"
            )
            fig_labor = px.bar(
                df_labor, x="labor_cost", y="sub_brand", orientation="h",
                color="flag",
                color_discrete_map={"Above": RED, "Normal": GOLD},
                labels={"labor_cost": "Labour Cost %", "sub_brand": ""},
            )
            fig_labor.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False, title="Labour Cost %")
            fig_labor.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
            fig_labor.add_vline(x=portfolio_labor_median, line_dash="dash", line_color="#9BA8B8",
                                annotation_text=f"Median {portfolio_labor_median:.0%}")
            st.plotly_chart(fig_labor, use_container_width=True)

        # Cost trend
        st.divider()
        section_header("Cost Trend Over Time", "Are costs improving or deteriorating?")
        cost_trend = daily_ops.copy()
        cost_trend["month"] = cost_trend["date"].dt.to_period("M").dt.to_timestamp()
        cost_monthly = cost_trend.groupby("month").agg(
            food_cost=("food_cost_pct", "mean"),
            labor_cost=("labor_cost_pct", "mean"),
        ).reset_index()
        cost_monthly["prime_cost"] = cost_monthly["food_cost"] + cost_monthly["labor_cost"]

        fig_ct = go.Figure()
        fig_ct.add_trace(go.Scatter(x=cost_monthly["month"], y=cost_monthly["food_cost"],
                                     mode="lines", name="Food Cost %", line=dict(color=AMBER, width=2)))
        fig_ct.add_trace(go.Scatter(x=cost_monthly["month"], y=cost_monthly["labor_cost"],
                                     mode="lines", name="Labour Cost %", line=dict(color="#7B8FA1", width=2)))
        fig_ct.add_trace(go.Scatter(x=cost_monthly["month"], y=cost_monthly["prime_cost"],
                                     mode="lines", name="Prime Cost %", line=dict(color=RED, width=2, dash="dot")))
        fig_ct.update_layout(**PLOTLY_LAYOUT, height=300)
        fig_ct.update_layout(legend=dict(orientation="h", y=1.12))
        fig_ct.update_yaxes(gridcolor="#2A3950", tickformat=".0%")
        fig_ct.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_ct, use_container_width=True)
    else:
        empty_state("No operational data for cost analysis.")

# ── Tab 4: Savings ─────────────────────────────────────────────

with tab_savings:
    section_header("Procurement Savings Tracker",
                    "Captured savings, active pipeline, and identified opportunities")

    captured = savings[savings["status"] == "Captured"]["annual_savings_aed"].sum()
    pipeline = savings[savings["status"] == "Pipeline"]["annual_savings_aed"].sum()
    identified = savings[savings["status"] == "Identified"]["annual_savings_aed"].sum()
    total_savings = captured + pipeline + identified

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Captured", fmt_currency(captured, ccy), border_color=GREEN, icon="✅")
    with c2:
        kpi_card("Pipeline", fmt_currency(pipeline, ccy), border_color=AMBER, icon="🔄")
    with c3:
        kpi_card("Identified", fmt_currency(identified, ccy), border_color=MUTED, icon="🔍")
    with c4:
        kpi_card("Total Opportunity", fmt_currency(total_savings, ccy), border_color=GOLD, icon="💎")

    # Savings as % of revenue
    savings_pct = captured / total_rev * 100 if total_rev else 0
    potential_pct = total_savings / total_rev * 100 if total_rev else 0
    insight_card("📊", "Savings Impact",
                 f"Captured savings = {savings_pct:.2f}% of revenue. "
                 f"Full pipeline would be {potential_pct:.2f}%.",
                 GREEN if savings_pct > 0.5 else AMBER)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        status_summary = savings.groupby("status")["annual_savings_aed"].sum().reset_index()
        fig_sav = px.bar(
            status_summary, x="status", y="annual_savings_aed",
            color="status",
            color_discrete_map={"Captured": GREEN, "Pipeline": AMBER, "Identified": "#9BA8B8"},
            labels={"annual_savings_aed": f"Annual Savings ({ccy})", "status": ""},
        )
        fig_sav.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                               title="Savings by Status")
        fig_sav.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_sav, use_container_width=True)

    with col_r:
        cat_summary = savings.groupby("category")["annual_savings_aed"].sum().reset_index()
        fig_cat = px.pie(
            cat_summary, values="annual_savings_aed", names="category",
            color_discrete_sequence=[GOLD, AMBER, GREEN], hole=0.45,
        )
        fig_cat.update_layout(**PLOTLY_LAYOUT, height=280, title="Savings by Category")
        fig_cat.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_cat, use_container_width=True)

    section_header("Savings Detail Table")
    sav_display = savings[[
        "savings_id", "category", "description", "annual_savings_aed", "status"
    ]].rename(columns={
        "savings_id": "ID", "category": "Category", "description": "Description",
        "annual_savings_aed": "Annual Savings (AED)", "status": "Status",
    })
    st.dataframe(sav_display.sort_values("Annual Savings (AED)", ascending=False),
                 use_container_width=True, hide_index=True, height=360)
    download_df(sav_display, "admo_savings.csv", "📥 Download Savings Data")

# ── Tab 5: Currency Exposure ──────────────────────────────────

with tab_fx:
    section_header("Currency Exposure",
                    "Revenue split by local operating currency — FX risk view for the CFO")

    scoped_venues = venues[venues["venue_id"].isin(venue_ids)]
    ccy_rev = summary.merge(
        scoped_venues[["venue_id", "local_currency"]], on="venue_id", how="left"
    ).groupby("local_currency")["revenue_aed"].sum().reset_index()

    if not ccy_rev.empty:
        ccy_rev["pct"] = ccy_rev["revenue_aed"] / ccy_rev["revenue_aed"].sum() * 100

        col_l, col_r = st.columns([1, 1])
        with col_l:
            fig_ccy = px.pie(
                ccy_rev, values="revenue_aed", names="local_currency",
                color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C", "#9BA8B8",
                                         "#7B8FA1", "#4A5568"],
                hole=0.45,
            )
            fig_ccy.update_layout(**PLOTLY_LAYOUT, height=320)
            fig_ccy.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_ccy, use_container_width=True)

        with col_r:
            ccy_table = ccy_rev.copy()
            ccy_table.columns = ["Currency", "Revenue (AED)", "% of Total"]
            ccy_table["Revenue (AED)"] = ccy_table["Revenue (AED)"].apply(lambda x: f"{x:,.0f}")
            ccy_table["% of Total"] = ccy_table["% of Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(ccy_table, use_container_width=True, hide_index=True)

            # FX insights
            max_pct = ccy_rev["pct"].max()
            max_ccy = ccy_rev.loc[ccy_rev["pct"].idxmax(), "local_currency"]
            n_currencies = len(ccy_rev)

            if max_pct > 70:
                insight_card("⚠", "Concentration Risk",
                             f"{max_pct:.0f}% of revenue in {max_ccy}. "
                             f"Consider hedging or geographic diversification.",
                             AMBER)
            else:
                insight_card("✅", "Well Diversified",
                             f"Revenue spread across {n_currencies} currencies. "
                             f"Largest is {max_ccy} at {max_pct:.0f}%.",
                             GREEN)

            if n_currencies > 1:
                non_aed = ccy_rev[ccy_rev["local_currency"] != "AED"]["revenue_aed"].sum()
                non_aed_pct = non_aed / ccy_rev["revenue_aed"].sum() * 100
                insight_card("💱", "Non-AED Exposure",
                             f"{non_aed_pct:.1f}% of revenue is in non-AED currencies. "
                             f"Subject to FX translation risk.",
                             AMBER if non_aed_pct > 30 else GREEN)
    else:
        empty_state("No currency data available.")
