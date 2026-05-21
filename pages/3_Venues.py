import streamlit as st

st.set_page_config(page_title="Venues | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, alert_card,
    section_header, kpi_card, download_df, insight_card, persona_banner,
    target_vs_actual,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN,
    CARD_BG, BORDER, MUTED, DIM,
    PLOTLY_LAYOUT, SEVERITY_COLORS,
)
from lib.data import (
    load_venues, load_daily_ops, load_monthly_summary, load_transactions,
    load_dishes, load_alerts, load_events, load_reservations,
    load_interactions, load_plan_targets, load_headcount,
    get_scope_venue_ids, filter_by_scope,
    compute_anomaly_flags, compute_slot_splits, compute_waitlist_rate,
    compute_budget_variance,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Venue Deep Dive", f"Scope: {scope_desc(scope)}")

persona_banner(
    "Venue Deep Dive",
    "Brand GM, Venue Manager, Operations Director",
    ["How was my venue this week?", "What's driving revenue?",
     "Are costs under control?", "Any guest complaints?",
     "How's my team staffed?", "What events are coming?"],
)

if not venue_ids:
    empty_state()
    st.stop()

venue_list = sorted(venues[venues["venue_id"].isin(venue_ids)]["sub_brand"].tolist())
selected_venue_name = st.selectbox("Select venue for drill-down", venue_list)
sel_row = venues[venues["sub_brand"] == selected_venue_name]
if sel_row.empty:
    empty_state()
    st.stop()

sel_vid = sel_row.iloc[0]["venue_id"]
sel_info = sel_row.iloc[0]

# Show venue context bar
st.markdown(
    f"<div style='background:{CARD_BG}; border:1px solid {BORDER}; border-radius:8px; "
    f"padding:12px 18px; margin-bottom:16px; display:flex; gap:32px; flex-wrap:wrap;'>"
    f"<div><span style='color:{MUTED}; font-size:0.72rem;'>VERTICAL</span><br/>"
    f"<span style='color:{GOLD}; font-weight:600;'>{sel_info['vertical']}</span></div>"
    f"<div><span style='color:{MUTED}; font-size:0.72rem;'>BRAND</span><br/>"
    f"<span style='color:{OFF_WHITE};'>{sel_info['concept_brand']}</span></div>"
    f"<div><span style='color:{MUTED}; font-size:0.72rem;'>LOCATION</span><br/>"
    f"<span style='color:{OFF_WHITE};'>{sel_info['city']}, {sel_info['country']}</span></div>"
    f"<div><span style='color:{MUTED}; font-size:0.72rem;'>TYPE</span><br/>"
    f"<span style='color:{OFF_WHITE};'>{sel_info['venue_type']}</span></div>"
    f"<div><span style='color:{MUTED}; font-size:0.72rem;'>CAPACITY</span><br/>"
    f"<span style='color:{OFF_WHITE};'>{sel_info['seat_capacity']} seats</span></div>"
    f"<div><span style='color:{MUTED}; font-size:0.72rem;'>OPEN SINCE</span><br/>"
    f"<span style='color:{OFF_WHITE};'>{sel_info['open_date'].strftime('%b %Y')}</span></div>"
    f"</div>",
    unsafe_allow_html=True,
)

daily_ops = load_daily_ops()
summary = load_monthly_summary()
txn = load_transactions()
dishes = load_dishes()
alerts = load_alerts()
events = load_events()
targets = load_plan_targets()

venue_ops = daily_ops[daily_ops["venue_id"] == sel_vid].sort_values("date")
venue_summary = summary[summary["venue_id"] == sel_vid]
venue_txn = txn[txn["venue_id"] == sel_vid]
venue_dishes = dishes[dishes["venue_id"] == sel_vid]
venue_alerts = alerts[alerts["venue_id"] == sel_vid]
venue_events = events[events["venue_id"] == sel_vid] if not events.empty else pd.DataFrame()

if venue_ops.empty:
    empty_state("No operational data for this venue.")
    st.stop()

# ── Venue scorecard ────────────────────────────────────────────

rev = venue_summary["revenue_aed"].sum()
covers = venue_summary["covers"].sum()
avg_occ = venue_ops["occupancy_pct"].mean()
avg_nps = venue_ops["nps_score"].mean()
avg_check = rev / covers if covers else 0
avg_food_cost = venue_ops["food_cost_pct"].mean()
avg_labor_cost = venue_ops["labor_cost_pct"].mean()
avg_sat = venue_ops["avg_satisfaction"].mean() if "avg_satisfaction" in venue_ops.columns else 0

# Budget variance for this venue
_, venue_target, venue_var = compute_budget_variance(venue_summary, targets, {sel_vid})

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Revenue", fmt_currency(rev, ccy), icon="💰", border_color=GOLD)
with c2:
    kpi_card("Covers", f"{covers:,.0f}", icon="🍽")
with c3:
    occ_color = GREEN if avg_occ > 0.7 else (AMBER if avg_occ > 0.5 else RED)
    kpi_card("Avg Occupancy", f"{avg_occ:.0%}", icon="📊", border_color=occ_color)
with c4:
    nps_color = GREEN if avg_nps >= 50 else (AMBER if avg_nps >= 30 else RED)
    kpi_card("Avg NPS", f"{avg_nps:.0f}", icon="⭐", border_color=nps_color)

c5, c6, c7, c8 = st.columns(4)
with c5:
    kpi_card("Avg Check", fmt_currency(avg_check, ccy), icon="🧾")
with c6:
    fc_color = GREEN if avg_food_cost < 0.30 else (AMBER if avg_food_cost < 0.35 else RED)
    kpi_card("Food Cost", f"{avg_food_cost:.1%}", icon="🥘", border_color=fc_color)
with c7:
    lc_color = GREEN if avg_labor_cost < 0.25 else (AMBER if avg_labor_cost < 0.30 else RED)
    kpi_card("Labour Cost", f"{avg_labor_cost:.1%}", icon="👷", border_color=lc_color)
with c8:
    sat_color = GREEN if avg_sat >= 8 else (AMBER if avg_sat >= 7 else RED)
    kpi_card("Satisfaction", f"{avg_sat:.1f}/10", icon="😊", border_color=sat_color)

# Plan vs actual row
st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
c_p1, c_p2, c_p3 = st.columns(3)
with c_p1:
    target_vs_actual("Revenue vs Plan", rev, venue_target, ccy)
with c_p2:
    nps_tgt = targets[targets["venue_id"] == sel_vid]["nps_target"].mean() if not targets.empty else 70
    target_vs_actual("NPS vs Target", avg_nps, nps_tgt, ccy, fmt_fn=lambda v: f"{v:.0f}")
with c_p3:
    cov_tgt = targets[targets["venue_id"] == sel_vid]["covers_target"].sum() if not targets.empty else 0
    target_vs_actual("Covers vs Plan", covers, cov_tgt, ccy, fmt_fn=lambda v: f"{v:,.0f}")

# ── Tabbed sections ────────────────────────────────────────────

tab_perf, tab_menu, tab_events, tab_guests, tab_alerts = st.tabs([
    "📈 Performance Trends", "🍽 Menu & Revenue Mix",
    "🎉 Events & Reservations", "👥 Guest Insights", "🚨 Alerts"
])

with tab_perf:
    section_header("90-Day Revenue Trend",
                    "Daily revenue with anomaly detection (red dots = ±2σ deviation)")
    recent_ops = venue_ops.tail(90)
    anomalies = compute_anomaly_flags(daily_ops, sel_vid)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recent_ops["date"], y=recent_ops["revenue_total_aed"],
        mode="lines", name="Daily Revenue",
        line=dict(color=GOLD, width=1.5),
        fill="tozeroy", fillcolor="rgba(201,169,97,0.08)",
    ))
    if not anomalies.empty:
        anomalies_90 = anomalies[anomalies["date"].isin(recent_ops["date"])]
        if not anomalies_90.empty:
            fig.add_trace(go.Scatter(
                x=anomalies_90["date"], y=anomalies_90["revenue_total_aed"],
                mode="markers", name="Anomaly",
                marker=dict(color=RED, size=9, symbol="circle",
                            line=dict(color=OFF_WHITE, width=1)),
            ))
    fig.update_layout(**PLOTLY_LAYOUT, height=340)
    fig.update_layout(legend=dict(orientation="h", y=1.12))
    fig.update_yaxes(gridcolor="#2A3950")
    fig.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig, use_container_width=True)

    # Last 7 days summary
    last_7 = venue_ops.tail(7)
    last_14 = venue_ops.tail(14)
    if len(last_7) >= 7 and len(last_14) >= 14:
        this_week_rev = last_7["revenue_total_aed"].sum()
        last_week_rev = last_14.head(7)["revenue_total_aed"].sum()
        wow_change = (this_week_rev - last_week_rev) / last_week_rev * 100 if last_week_rev else 0

        st.divider()
        section_header("Last 7 Days vs Prior 7 Days", "Week-over-week comparison")
        w1, w2, w3, w4 = st.columns(4)
        with w1:
            kpi_card("This Week Revenue", fmt_currency(this_week_rev, ccy),
                     delta=f"{wow_change:+.1f}% WoW", delta_good=wow_change >= 0, icon="📊")
        with w2:
            kpi_card("This Week Covers", f"{last_7['covers_total'].sum():,.0f}",
                     delta=f"vs {last_14.head(7)['covers_total'].sum():,.0f} prior", icon="🍽")
        with w3:
            kpi_card("This Week Satisfaction", f"{last_7['avg_satisfaction'].mean():.1f}/10",
                     delta=f"vs {last_14.head(7)['avg_satisfaction'].mean():.1f} prior",
                     delta_good=last_7["avg_satisfaction"].mean() >= last_14.head(7)["avg_satisfaction"].mean(),
                     icon="⭐")
        with w4:
            kpi_card("This Week NPS", f"{last_7['nps_score'].mean():.0f}",
                     delta=f"vs {last_14.head(7)['nps_score'].mean():.0f} prior",
                     delta_good=last_7["nps_score"].mean() >= last_14.head(7)["nps_score"].mean(),
                     icon="📈")

    # Operational metrics trend
    st.divider()
    section_header("Operational Metrics Over Time")
    ops_metric = st.radio(
        "Metric", ["Occupancy", "NPS", "Food Cost %", "Labour Cost %", "Satisfaction"],
        horizontal=True, key="venue_ops_metric",
    )
    ops_col_map = {
        "Occupancy": "occupancy_pct", "NPS": "nps_score",
        "Food Cost %": "food_cost_pct", "Labour Cost %": "labor_cost_pct",
        "Satisfaction": "avg_satisfaction",
    }
    col = ops_col_map[ops_metric]
    fig_ops = go.Figure()
    fig_ops.add_trace(go.Scatter(
        x=venue_ops["date"], y=venue_ops[col],
        mode="lines", name=ops_metric,
        line=dict(color=GOLD, width=1.5),
    ))
    if len(venue_ops) > 14:
        rolling = venue_ops.set_index("date")[col].rolling(14).mean()
        fig_ops.add_trace(go.Scatter(
            x=rolling.index, y=rolling.values,
            mode="lines", name="14-day avg",
            line=dict(color=MUTED, width=1, dash="dash"),
        ))
    fig_ops.update_layout(**PLOTLY_LAYOUT, height=280)
    fig_ops.update_layout(legend=dict(orientation="h", y=1.12))
    tick = ".0%" if "cost" in ops_metric.lower() or "occupancy" in ops_metric.lower() else None
    if tick:
        fig_ops.update_yaxes(gridcolor="#2A3950", tickformat=tick)
    else:
        fig_ops.update_yaxes(gridcolor="#2A3950")
    fig_ops.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_ops, use_container_width=True)

with tab_menu:
    col_l, col_r = st.columns(2)

    with col_l:
        section_header("Service Slot Mix", "When do guests come?")
        slots = compute_slot_splits(txn, {sel_vid})
        if not slots.empty:
            fig_slot = px.pie(
                values=slots.values, names=slots.index,
                color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C"],
                hole=0.4,
            )
            fig_slot.update_layout(**PLOTLY_LAYOUT, height=280)
            fig_slot.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_slot, use_container_width=True)

    with col_r:
        section_header("Food vs Beverage", "Revenue split")
        food_rev = venue_summary["food_revenue_aed"].sum()
        bev_rev = venue_summary["beverage_revenue_aed"].sum()
        fig_fb = px.pie(
            values=[food_rev, bev_rev], names=["Food", "Beverage"],
            color_discrete_sequence=[GOLD, "#5A7D3C"], hole=0.4,
        )
        fig_fb.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_fb.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_fb, use_container_width=True)

    # Monthly revenue trend by F&B
    st.divider()
    section_header("Monthly Food vs Beverage Trend")
    if not venue_summary.empty:
        fb_monthly = venue_summary.groupby("month").agg(
            food=("food_revenue_aed", "sum"),
            bev=("beverage_revenue_aed", "sum"),
        ).reset_index()
        fig_fb_trend = go.Figure()
        fig_fb_trend.add_trace(go.Bar(x=fb_monthly["month"], y=fb_monthly["food"],
                                       name="Food", marker_color=GOLD))
        fig_fb_trend.add_trace(go.Bar(x=fb_monthly["month"], y=fb_monthly["bev"],
                                       name="Beverage", marker_color="#5A7D3C"))
        fig_fb_trend.update_layout(**PLOTLY_LAYOUT, height=280, barmode="stack")
        fig_fb_trend.update_layout(legend=dict(orientation="h", y=1.12))
        fig_fb_trend.update_yaxes(gridcolor="#2A3950")
        fig_fb_trend.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_fb_trend, use_container_width=True)

    section_header("Dish Menu", "Sorted by margin — signature dishes flagged")
    if venue_dishes.empty:
        empty_state("No dish data.")
    else:
        dish_display = venue_dishes[["dish_name", "category", "price_aed",
                                      "food_cost_pct", "margin_aed", "signature_flag"]].copy()
        dish_display.columns = ["Dish", "Category", "Price (AED)",
                                "Food Cost %", "Margin (AED)", "Signature"]
        dish_display["Food Cost %"] = (dish_display["Food Cost %"] * 100).round(1).astype(str) + "%"
        dish_display["Signature"] = dish_display["Signature"].map({"Yes": "⭐ Yes", "No": ""})
        st.dataframe(
            dish_display.sort_values("Margin (AED)", ascending=False),
            use_container_width=True, hide_index=True, height=380,
        )
        download_df(dish_display, f"admo_menu_{sel_vid}.csv", "📥 Download Menu Data")

        # Dish insights
        avg_margin = venue_dishes["margin_aed"].mean()
        top_dish = venue_dishes.nlargest(1, "margin_aed").iloc[0]
        worst_dish = venue_dishes.nsmallest(1, "margin_aed").iloc[0]
        sig_count = len(venue_dishes[venue_dishes["signature_flag"] == "Yes"])
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            insight_card("🥇", "Highest Margin",
                         f"{top_dish['dish_name']} — AED {top_dish['margin_aed']:.0f}", GREEN)
        with col_d2:
            insight_card("⚠", "Lowest Margin",
                         f"{worst_dish['dish_name']} — AED {worst_dish['margin_aed']:.0f}", AMBER)
        with col_d3:
            insight_card("⭐", "Signature Dishes",
                         f"{sig_count} of {len(venue_dishes)} dishes are signature items", GOLD)

with tab_events:
    section_header("Events & Private Dining",
                    "Past events, revenue, and upcoming reservations")

    if not venue_events.empty:
        events_rev = venue_events["total_revenue_aed"].sum()
        events_count = len(venue_events)
        avg_per_head = venue_events["per_head_revenue_aed"].mean()
        repeat_hosts = venue_events["repeat_host_flag"].value_counts().get("Yes", 0)
        repeat_pct = repeat_hosts / events_count * 100 if events_count else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("Events Revenue", fmt_currency(events_rev, ccy), icon="🎉", border_color=GOLD)
        with c2:
            kpi_card("Total Events", str(events_count), icon="📅")
        with c3:
            kpi_card("Avg Per Head", fmt_currency(avg_per_head, ccy), icon="🍽")
        with c4:
            kpi_card("Repeat Hosts", f"{repeat_pct:.0f}%", icon="🔄",
                     border_color=GREEN if repeat_pct > 30 else MUTED)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Events by type
        col_l, col_r = st.columns(2)
        with col_l:
            event_types = venue_events["event_type"].value_counts().reset_index()
            event_types.columns = ["Type", "Count"]
            fig_et = px.pie(
                event_types, values="Count", names="Type",
                color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C", "#9BA8B8"],
                hole=0.45,
            )
            fig_et.update_layout(**PLOTLY_LAYOUT, height=280, title="Events by Type")
            fig_et.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_et, use_container_width=True)

        with col_r:
            # Monthly events trend
            venue_events_m = venue_events.copy()
            venue_events_m["month"] = venue_events_m["event_date"].dt.to_period("M").dt.to_timestamp()
            ev_monthly = venue_events_m.groupby("month").agg(
                count=("event_id", "count"),
                revenue=("total_revenue_aed", "sum"),
            ).reset_index()
            fig_em = go.Figure()
            fig_em.add_trace(go.Bar(x=ev_monthly["month"], y=ev_monthly["revenue"],
                                     name="Revenue", marker_color=GOLD))
            fig_em.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                                  title="Monthly Events Revenue")
            fig_em.update_yaxes(gridcolor="#2A3950")
            fig_em.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_em, use_container_width=True)
    else:
        empty_state("No events data for this venue.")

    # Reservations
    st.divider()
    section_header("Upcoming Reservations", "Today's reservation book and waitlist status")
    try:
        reservations = load_reservations()
        venue_res = reservations[reservations["venue_id"] == sel_vid]
        if not venue_res.empty:
            res_count = len(venue_res)
            confirmed = len(venue_res[venue_res["status"] == "Confirmed"])
            waitlisted = len(venue_res[venue_res["status"] == "Waitlist"])
            avg_party = venue_res["party_size"].mean()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                kpi_card("Total Reservations", str(res_count), icon="📋")
            with c2:
                kpi_card("Confirmed", str(confirmed), icon="✅", border_color=GREEN)
            with c3:
                kpi_card("Waitlisted", str(waitlisted), icon="⏳",
                         border_color=AMBER if waitlisted > 0 else GREEN)
            with c4:
                kpi_card("Avg Party Size", f"{avg_party:.1f}", icon="👥")

            # Reservation breakdown by slot
            slot_res = venue_res["time_slot"].value_counts().reset_index()
            slot_res.columns = ["Slot", "Count"]
            fig_rs = px.bar(slot_res, x="Slot", y="Count", color_discrete_sequence=[GOLD])
            fig_rs.update_layout(**PLOTLY_LAYOUT, height=200, showlegend=False,
                                  title="Reservations by Time Slot")
            fig_rs.update_yaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_rs, use_container_width=True)
        else:
            empty_state("No reservations for this venue.")
    except Exception:
        empty_state("Reservation data unavailable.")

with tab_guests:
    section_header("Guest Profile for This Venue",
                    "Who visits, how often, and what's their value?")

    from lib.data import load_guests
    all_guests = load_guests()

    # Find guests who visited this venue
    venue_guest_ids = set(venue_txn["guest_id"].dropna().unique())
    venue_guests = all_guests[all_guests["guest_id"].isin(venue_guest_ids)]

    if venue_guests.empty:
        empty_state("No guest data for this venue.")
    else:
        total_g = len(venue_guests)
        diamond_pct = len(venue_guests[venue_guests["guest_tier"] == "Diamond"]) / total_g * 100 if total_g else 0
        avg_ltv = venue_guests["lifetime_spend_aed"].mean()
        avg_visits = venue_guests["total_visits"].mean()
        multi_brand = len(venue_guests[venue_guests["brands_visited_count"] >= 2]) / total_g * 100 if total_g else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Unique Guests", f"{total_g:,}", icon="👥")
        with c2:
            kpi_card("Diamond %", f"{diamond_pct:.1f}%", icon="💎")
        with c3:
            kpi_card("Avg LTV", fmt_currency(avg_ltv, ccy), icon="💰")
        with c4:
            kpi_card("Avg Visits", f"{avg_visits:.1f}", icon="🔄")
        with c5:
            kpi_card("Multi-Brand %", f"{multi_brand:.1f}%", icon="🔗")

        col_l, col_r = st.columns(2)
        with col_l:
            tier_dist = venue_guests["guest_tier"].value_counts().reset_index()
            tier_dist.columns = ["Tier", "Count"]
            fig_t = px.pie(tier_dist, values="Count", names="Tier",
                           color_discrete_map={"Diamond": GOLD, "Platinum": "#9BA8B8",
                                               "Gold": "#D89B3F", "Standard": "#4A5568"},
                           hole=0.45)
            fig_t.update_layout(**PLOTLY_LAYOUT, height=280, title="Guest Tier Mix")
            fig_t.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_t, use_container_width=True)

        with col_r:
            nat_dist = venue_guests["nationality"].value_counts().head(8).reset_index()
            nat_dist.columns = ["Nationality", "Count"]
            fig_n = px.bar(nat_dist, x="Count", y="Nationality", orientation="h",
                           color_discrete_sequence=[GOLD])
            fig_n.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                                title="Top Nationalities")
            fig_n.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_n, use_container_width=True)

    # Guest interactions
    st.divider()
    section_header("Recent Guest Interactions", "Compliments, complaints and special occasions")
    try:
        interactions = load_interactions()
        venue_int = interactions[interactions["venue_id"] == sel_vid].sort_values(
            "interaction_date", ascending=False
        ).head(10)
        if not venue_int.empty:
            int_types = venue_int["interaction_type"].value_counts()
            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1:
                compliments = int_types.get("Compliment", 0)
                kpi_card("Compliments", str(compliments), icon="👍", border_color=GREEN)
            with col_i2:
                complaints = int_types.get("Complaint resolved", 0) + int_types.get("Complaint", 0)
                kpi_card("Complaints", str(complaints), icon="⚠",
                         border_color=RED if complaints > 3 else AMBER)
            with col_i3:
                occasions = int_types.get("Occasion", 0)
                kpi_card("Occasions", str(occasions), icon="🎂")

            for _, row in venue_int.iterrows():
                color = GREEN if "Compliment" in row["interaction_type"] else (
                    RED if "Complaint" in row["interaction_type"] else GOLD)
                st.markdown(
                    f"<div style='background:{CARD_BG}; border-left:3px solid {color}; "
                    f"border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:0.82rem;'>"
                    f"<strong style='color:{color};'>{row['interaction_type']}</strong> "
                    f"<span style='color:{DIM};'>— {row['interaction_date'].strftime('%d %b %Y')}</span><br/>"
                    f"<span style='color:{OFF_WHITE};'>{row['note'][:120]}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            empty_state("No recorded interactions.")
    except Exception:
        empty_state("Interaction data unavailable.")

with tab_alerts:
    section_header("Active Alerts", "Issues flagged for this venue")
    open_v_alerts = venue_alerts[venue_alerts["status"].isin(["Open", "Investigating", "Escalated"])]
    if open_v_alerts.empty:
        st.markdown(
            f"<div style='background:{CARD_BG}; border:1px solid {GREEN}44; "
            f"border-radius:8px; padding:24px; text-align:center;'>"
            f"<span style='color:{GREEN}; font-size:1.5rem;'>✓</span><br/>"
            f"<span style='color:{GREEN}; font-weight:600;'>All Clear</span><br/>"
            f"<span style='color:{MUTED}; font-size:0.85rem;'>No active alerts for {selected_venue_name}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        c1, c2 = st.columns([1, 3])
        with c1:
            red_n = len(open_v_alerts[open_v_alerts["severity"] == "Red"])
            amber_n = len(open_v_alerts[open_v_alerts["severity"] == "Amber"])
            kpi_card("Red Alerts", str(red_n), border_color=RED)
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            kpi_card("Amber Alerts", str(amber_n), border_color=AMBER)
        with c2:
            for _, a in open_v_alerts.sort_values(
                "severity", key=lambda s: s.map({"Red": 0, "Amber": 1, "Green": 2})
            ).iterrows():
                alert_card(a["severity"], a["headline"], description=a["description"],
                           owner=a["owner"], status=a["status"])
