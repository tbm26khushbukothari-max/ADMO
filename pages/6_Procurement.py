import streamlit as st

st.set_page_config(page_title="Procurement | ADMO", page_icon="♦", layout="wide")

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
    load_venues, load_vendors, load_venue_vendor_map, load_savings,
    get_scope_venue_ids, filter_by_scope,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Procurement", f"Scope: {scope_desc(scope)}")

persona_banner(
    "Procurement",
    "CPO, Procurement Director, Supply Chain Manager",
    ["Which vendors are risky?", "Where can we consolidate?",
     "What's our savings pipeline?", "Are we too dependent on any vendor?",
     "Who supplies signature ingredients?", "What's vendor quality like?"],
)

vendors = load_vendors()
vvm = load_venue_vendor_map()
savings = load_savings()

scoped_vvm = vvm[vvm["venue_id"].isin(venue_ids)]

if scoped_vvm.empty:
    empty_state()
    st.stop()

scoped_vendor_ids = set(scoped_vvm["vendor_id"])
scoped_vendors = vendors[vendors["vendor_id"].isin(scoped_vendor_ids)]

tab_health, tab_supply, tab_blast, tab_savings, tab_risk = st.tabs([
    "📊 Vendor Health", "🏷 Supply Analysis", "💥 Blast Radius",
    "💰 Savings Pipeline", "⚠ Concentration Risk"
])

# ── Tab 1: Vendor Health Matrix ───────────────────────────────

with tab_health:
    section_header("Vendor Health Matrix",
                    "OTD vs Quality — bottom-left = underperformers, top-right = stars")

    if scoped_vendors.empty:
        empty_state("No vendor data.")
    else:
        # Summary KPIs
        total_vendors = len(scoped_vendors)
        sig_vendors = len(scoped_vendors[scoped_vendors["signature_flag"] == "Yes"])
        high_risk = len(scoped_vendors[scoped_vendors["risk_flag"] == "High"])
        avg_otd = scoped_vendors["on_time_delivery_pct"].mean()
        avg_quality = scoped_vendors["quality_score"].mean()

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Total Vendors", str(total_vendors), icon="🏭")
        with c2:
            kpi_card("Signature", str(sig_vendors), icon="⭐",
                     delta=f"{sig_vendors/total_vendors*100:.0f}% of total" if total_vendors else "")
        with c3:
            kpi_card("High Risk", str(high_risk), icon="🚨",
                     border_color=RED if high_risk > 3 else (AMBER if high_risk > 0 else GREEN))
        with c4:
            kpi_card("Avg OTD", f"{avg_otd:.0%}", icon="🚚",
                     border_color=GREEN if avg_otd >= 0.90 else (AMBER if avg_otd >= 0.80 else RED))
        with c5:
            kpi_card("Avg Quality", f"{avg_quality:.1f}/5", icon="📊",
                     border_color=GREEN if avg_quality >= 4.0 else (AMBER if avg_quality >= 3.5 else RED))

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Scatter plot
        fig_scatter = px.scatter(
            scoped_vendors,
            x="on_time_delivery_pct", y="quality_score",
            color="risk_flag",
            color_discrete_map={"Low": GREEN, "Medium": AMBER, "High": RED},
            size=[12] * len(scoped_vendors),
            hover_name="vendor_name",
            hover_data=["category", "signature_flag"],
            labels={
                "on_time_delivery_pct": "On-Time Delivery %",
                "quality_score": "Quality Score",
                "risk_flag": "Risk",
            },
        )
        # Add quadrant lines
        fig_scatter.add_hline(y=4.0, line_dash="dash", line_color=MUTED, opacity=0.5)
        fig_scatter.add_vline(x=0.90, line_dash="dash", line_color=MUTED, opacity=0.5)
        fig_scatter.update_layout(**PLOTLY_LAYOUT, height=420)
        fig_scatter.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
        fig_scatter.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Underperformers callout
        underperformers = scoped_vendors[
            (scoped_vendors["on_time_delivery_pct"] < 0.85) |
            (scoped_vendors["quality_score"] < 3.5)
        ]
        if not underperformers.empty:
            st.divider()
            section_header("Underperforming Vendors", "Below OTD 85% or Quality 3.5/5")
            for _, v in underperformers.iterrows():
                flags = []
                if v["on_time_delivery_pct"] < 0.85:
                    flags.append(f"OTD: {v['on_time_delivery_pct']:.0%}")
                if v["quality_score"] < 3.5:
                    flags.append(f"Quality: {v['quality_score']:.1f}/5")
                insight_card("⚠", v["vendor_name"],
                             f"{v['category']} | {' | '.join(flags)} | Risk: {v['risk_flag']}",
                             RED if v["risk_flag"] == "High" else AMBER)

# ── Tab 2: Supply Analysis ────────────────────────────────────

with tab_supply:
    section_header("Supply Chain Composition",
                    "Signature vs commodity split and category breakdown")

    col_l, col_r = st.columns(2)

    with col_l:
        section_header("Signature vs Commodity")
        sig_counts = scoped_vendors["signature_flag"].value_counts().reset_index()
        sig_counts.columns = ["Type", "Count"]
        sig_counts["Type"] = sig_counts["Type"].map({"Yes": "Signature", "No": "Commodity"})
        fig_sig = px.pie(
            sig_counts, values="Count", names="Type",
            color_discrete_sequence=[GOLD, "#4A5568"], hole=0.45,
        )
        fig_sig.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_sig.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_sig, use_container_width=True)

        insight_card("📊", "Signature Ratio",
                     f"{sig_vendors} signature vendors out of {total_vendors} total "
                     f"({sig_vendors/total_vendors*100:.0f}%)" if total_vendors else "No data",
                     GOLD)

    with col_r:
        section_header("Vendors by Category")
        cat_counts = scoped_vendors["category"].value_counts().head(10).reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig_cat = px.bar(
            cat_counts, x="Count", y="Category", orientation="h",
            color_discrete_sequence=[GOLD],
            labels={"Count": "Vendors", "Category": ""},
        )
        fig_cat.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
        fig_cat.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_cat, use_container_width=True)

    # Risk distribution
    st.divider()
    section_header("Risk Distribution", "How many vendors fall into each risk bucket?")
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        risk_counts = scoped_vendors["risk_flag"].value_counts().reset_index()
        risk_counts.columns = ["Risk", "Count"]
        fig_risk = px.pie(risk_counts, values="Count", names="Risk",
                          color_discrete_map={"Low": GREEN, "Medium": AMBER, "High": RED},
                          hole=0.45)
        fig_risk.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_risk.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_risk, use_container_width=True)

    with col_r2:
        # Quality vs OTD distribution
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Box(y=scoped_vendors["on_time_delivery_pct"], name="OTD %",
                                   marker_color=GOLD, boxpoints="all"))
        fig_dist.add_trace(go.Box(y=scoped_vendors["quality_score"] / 5, name="Quality (normalised)",
                                   marker_color=GREEN, boxpoints="all"))
        fig_dist.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                                title="Performance Distribution")
        fig_dist.update_yaxes(gridcolor="#2A3950", tickformat=".0%")
        st.plotly_chart(fig_dist, use_container_width=True)

    # Full vendor table
    st.divider()
    section_header("Vendor Directory", "Full list of vendors in scope")
    vendor_display = scoped_vendors[["vendor_name", "category", "signature_flag",
                                      "on_time_delivery_pct", "quality_score", "risk_flag"]].copy()
    vendor_display.columns = ["Vendor", "Category", "Signature", "OTD %", "Quality", "Risk"]
    vendor_display["OTD %"] = (vendor_display["OTD %"] * 100).round(1).astype(str) + "%"
    vendor_display["Signature"] = vendor_display["Signature"].map({"Yes": "⭐ Yes", "No": ""})
    st.dataframe(vendor_display.sort_values("Risk", key=lambda s: s.map({"High": 0, "Medium": 1, "Low": 2})),
                 use_container_width=True, hide_index=True, height=380)
    download_df(vendor_display, "admo_vendors.csv", "📥 Download Vendor Data")

# ── Tab 3: Blast Radius ──────────────────────────────────────

with tab_blast:
    section_header("Blast Radius — Vendor Dependency",
                    "Select a vendor to see which venues would be affected if they fail")

    vendor_options = sorted(scoped_vendors["vendor_name"].tolist())
    if vendor_options:
        selected_vendor = st.selectbox("Select a vendor", vendor_options)
        sel_vendor_id = vendors[vendors["vendor_name"] == selected_vendor]["vendor_id"].iloc[0]

        dependent_venues = vvm[vvm["vendor_id"] == sel_vendor_id]["venue_id"].unique()
        dep_in_scope = [v for v in dependent_venues if v in venue_ids]
        dep_all = list(dependent_venues)

        vendor_info = vendors[vendors["vendor_id"] == sel_vendor_id].iloc[0]

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Affected Venues (Scope)", str(len(dep_in_scope)), icon="📍",
                     border_color=RED if len(dep_in_scope) > 5 else (AMBER if len(dep_in_scope) > 2 else GREEN))
        with c2:
            kpi_card("Affected Venues (Total)", str(len(dep_all)), icon="🌍")
        with c3:
            kpi_card("Category", vendor_info["category"], icon="🏷")
        with c4:
            otd_color = GREEN if vendor_info["on_time_delivery_pct"] >= 0.90 else (
                AMBER if vendor_info["on_time_delivery_pct"] >= 0.80 else RED)
            kpi_card("OTD %", f"{vendor_info['on_time_delivery_pct']:.0%}", icon="🚚",
                     border_color=otd_color)
        with c5:
            q_color = GREEN if vendor_info["quality_score"] >= 4.0 else (
                AMBER if vendor_info["quality_score"] >= 3.5 else RED)
            kpi_card("Quality", f"{vendor_info['quality_score']:.1f}/5", icon="⭐",
                     border_color=q_color)

        # Impact assessment
        if vendor_info["signature_flag"] == "Yes" and len(dep_in_scope) >= 3:
            insight_card("🚨", "High Impact Signature Vendor",
                         f"{selected_vendor} is a signature vendor supplying {len(dep_in_scope)} venues. "
                         f"Loss would require emergency sourcing — consider backup supplier.",
                         RED)
        elif len(dep_in_scope) >= 5:
            insight_card("⚠", "Wide Dependencies",
                         f"{selected_vendor} supplies {len(dep_in_scope)} venues in scope. "
                         f"Consider diversifying.",
                         AMBER)

        dep_display = venues[venues["venue_id"].isin(dep_in_scope)][
            ["sub_brand", "city", "country", "vertical"]
        ].rename(columns={
            "sub_brand": "Venue", "city": "City", "country": "Country", "vertical": "Vertical",
        })

        if not dep_display.empty:
            st.dataframe(dep_display, use_container_width=True, hide_index=True)
        else:
            empty_state("No scoped venues depend on this vendor.")

# ── Tab 4: Savings Pipeline ──────────────────────────────────

with tab_savings:
    section_header("Procurement Savings Pipeline",
                    "Consolidation, renegotiation and substitution opportunities")

    captured = savings[savings["status"] == "Captured"]["annual_savings_aed"].sum()
    pipeline = savings[savings["status"] == "Pipeline"]["annual_savings_aed"].sum()
    identified = savings[savings["status"] == "Identified"]["annual_savings_aed"].sum()
    total_sav = captured + pipeline + identified

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Captured", fmt_currency(captured, ccy), border_color=GREEN, icon="✅")
    with c2:
        kpi_card("Pipeline", fmt_currency(pipeline, ccy), border_color=AMBER, icon="🔄")
    with c3:
        kpi_card("Identified", fmt_currency(identified, ccy), border_color=MUTED, icon="🔍")
    with c4:
        kpi_card("Total Opportunity", fmt_currency(total_sav, ccy), border_color=GOLD, icon="💎")

    # Savings by category
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        cat_sav = savings.groupby("category")["annual_savings_aed"].sum().reset_index()
        fig_cs = px.pie(cat_sav, values="annual_savings_aed", names="category",
                        color_discrete_sequence=[GOLD, AMBER, GREEN], hole=0.45)
        fig_cs.update_layout(**PLOTLY_LAYOUT, height=280, title="Savings by Category")
        fig_cs.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_cs, use_container_width=True)

    with col_r:
        status_sav = savings.groupby("status")["annual_savings_aed"].sum().reset_index()
        fig_ss = px.bar(status_sav, x="status", y="annual_savings_aed",
                        color="status",
                        color_discrete_map={"Captured": GREEN, "Pipeline": AMBER, "Identified": "#9BA8B8"},
                        labels={"annual_savings_aed": f"Savings ({ccy})", "status": ""})
        fig_ss.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                              title="Savings by Status")
        fig_ss.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_ss, use_container_width=True)

    # Actionable items
    st.divider()
    section_header("Actionable Opportunities", "Pipeline and identified items ready for procurement action")
    pipeline_savings = savings[savings["status"].isin(["Identified", "Pipeline"])]
    if pipeline_savings.empty:
        empty_state("No pipeline / identified savings.")
    else:
        display_sav = pipeline_savings[[
            "savings_id", "category", "description", "annual_savings_aed", "status"
        ]].rename(columns={
            "savings_id": "ID", "category": "Category", "description": "Description",
            "annual_savings_aed": "Annual Savings (AED)", "status": "Status",
        })
        st.dataframe(display_sav.sort_values("Annual Savings (AED)", ascending=False),
                     use_container_width=True, hide_index=True, height=350)

        # Top opportunities
        top3 = pipeline_savings.nlargest(3, "annual_savings_aed")
        for _, row in top3.iterrows():
            insight_card("💡", f"{row['category']} — {fmt_currency(row['annual_savings_aed'], ccy)}/yr",
                         row["description"], GOLD)

# ── Tab 5: Concentration Risk ─────────────────────────────────

with tab_risk:
    section_header("Concentration Risk — Vendors per Venue",
                    "Venues with few vendors are vulnerable to supply disruption")

    vendor_per_venue = scoped_vvm.groupby("venue_id")["vendor_id"].nunique().reset_index()
    vendor_per_venue.columns = ["venue_id", "vendor_count"]
    vendor_per_venue = vendor_per_venue.merge(
        venues[["venue_id", "sub_brand", "vertical"]], on="venue_id", how="left"
    )

    sig_vendor_ids = set(vendors[vendors["signature_flag"] == "Yes"]["vendor_id"])
    sig_per_venue = scoped_vvm[scoped_vvm["vendor_id"].isin(sig_vendor_ids)].groupby(
        "venue_id"
    )["vendor_id"].nunique().reset_index()
    sig_per_venue.columns = ["venue_id", "sig_vendor_count"]
    vendor_per_venue = vendor_per_venue.merge(sig_per_venue, on="venue_id", how="left")
    vendor_per_venue["sig_vendor_count"] = vendor_per_venue["sig_vendor_count"].fillna(0).astype(int)

    # KPIs
    avg_vendors = vendor_per_venue["vendor_count"].mean()
    min_vendors = vendor_per_venue["vendor_count"].min()
    low_sig = vendor_per_venue[vendor_per_venue["sig_vendor_count"] < 3]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Avg Vendors/Venue", f"{avg_vendors:.1f}", icon="🏭")
    with c2:
        kpi_card("Min Vendors", str(min_vendors), icon="⚠",
                 border_color=RED if min_vendors < 5 else GREEN)
    with c3:
        kpi_card("Low Sig. Vendors", f"{len(low_sig)} venues", icon="🔍",
                 border_color=AMBER if len(low_sig) > 0 else GREEN)
    with c4:
        # Single-source risk
        single_source = scoped_vvm.groupby(["venue_id", "vendor_id"]).size().reset_index()
        # Categories with only 1 vendor
        kpi_card("Total Vendor Links", str(len(scoped_vvm)), icon="🔗")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    fig_conc = go.Figure()
    sorted_vpv = vendor_per_venue.sort_values("vendor_count")
    fig_conc.add_trace(go.Bar(
        x=sorted_vpv["sub_brand"],
        y=sorted_vpv["vendor_count"],
        name="Total Vendors", marker_color=GOLD,
    ))
    fig_conc.add_trace(go.Bar(
        x=sorted_vpv["sub_brand"],
        y=sorted_vpv["sig_vendor_count"],
        name="Signature Vendors", marker_color="#5A7D3C",
    ))
    fig_conc.update_layout(**PLOTLY_LAYOUT, height=380, barmode="group")
    fig_conc.update_layout(legend=dict(orientation="h", y=1.1))
    fig_conc.update_yaxes(gridcolor="#2A3950", title_text="Vendor Count")
    fig_conc.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_conc, use_container_width=True)

    if not low_sig.empty:
        st.divider()
        section_header("Venues at Risk", "Fewer than 3 signature vendors")
        for _, row in low_sig.iterrows():
            insight_card("⚠", row["sub_brand"],
                         f"{row['sig_vendor_count']} signature vendor(s), {row['vendor_count']} total — "
                         f"limited supply chain resilience",
                         RED if row["sig_vendor_count"] == 0 else AMBER)
