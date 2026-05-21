import streamlit as st

st.set_page_config(
    page_title="ADMO Lifestyle Dashboard",
    page_icon="♦",
    layout="wide",
    initial_sidebar_state="expanded",
)

from lib.style import metric_card_css, fmt_aed, fmt_usd, GOLD, OFF_WHITE, CARD_BG
from lib.data_loader import load_monthly_summary, load_venues, load_alerts, load_brand_exposure

st.markdown(metric_card_css(), unsafe_allow_html=True)

st.markdown(
    f"<h1 style='text-align:center; color:{GOLD};'>ADMO Lifestyle Holding</h1>"
    f"<p style='text-align:center; color:{OFF_WHITE}; margin-top:-10px;'>"
    "Group Intelligence Dashboard</p>",
    unsafe_allow_html=True,
)

summary = load_monthly_summary()
venues = load_venues()
alerts = load_alerts()

total_rev = summary["revenue_aed"].sum()
total_covers = summary["covers"].sum()
venue_count = venues.shape[0]
brand_count = venues["brand"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Portfolio Revenue (18 mo)", fmt_aed(total_rev))
c2.metric("Total Covers", f"{total_covers:,.0f}")
c3.metric("Active Venues", str(venue_count))
c4.metric("Brands", str(brand_count))

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Monthly Revenue Trend")
    import plotly.express as px
    from lib.style import PLOTLY_LAYOUT, BRAND_COLORS

    monthly_brand = (
        summary.groupby(["month", "brand"])["revenue_aed"]
        .sum()
        .reset_index()
    )
    fig = px.area(
        monthly_brand,
        x="month",
        y="revenue_aed",
        color="brand",
        color_discrete_map=BRAND_COLORS,
        labels={"revenue_aed": "Revenue (AED)", "month": "", "brand": "Brand"},
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=380)
    fig.update_yaxes(gridcolor="#2A3950", gridwidth=0.5)
    fig.update_xaxes(gridcolor="#2A3950", gridwidth=0.5)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Active Alerts")
    open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]
    red_count = (open_alerts["severity"] == "Red").sum()
    amber_count = (open_alerts["severity"] == "Amber").sum()
    green_count = (open_alerts["severity"] == "Green").sum()

    from lib.style import RED, AMBER, GREEN

    st.markdown(
        f"<div style='display:flex; gap:16px; margin-bottom:16px;'>"
        f"<div style='background:{RED}22; border:1px solid {RED}; border-radius:8px; "
        f"padding:16px; flex:1; text-align:center;'>"
        f"<div style='font-size:2rem; font-weight:bold; color:{RED};'>{red_count}</div>"
        f"<div style='color:{OFF_WHITE};'>Red</div></div>"
        f"<div style='background:{AMBER}22; border:1px solid {AMBER}; border-radius:8px; "
        f"padding:16px; flex:1; text-align:center;'>"
        f"<div style='font-size:2rem; font-weight:bold; color:{AMBER};'>{amber_count}</div>"
        f"<div style='color:{OFF_WHITE};'>Amber</div></div>"
        f"<div style='background:{GREEN}22; border:1px solid {GREEN}; border-radius:8px; "
        f"padding:16px; flex:1; text-align:center;'>"
        f"<div style='font-size:2rem; font-weight:bold; color:{GREEN};'>{green_count}</div>"
        f"<div style='color:{OFF_WHITE};'>Green</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    for _, alert in open_alerts.iterrows():
        sev_color = {"Red": RED, "Amber": AMBER, "Green": GREEN}.get(alert["severity"], OFF_WHITE)
        st.markdown(
            f"<div style='background:{CARD_BG}; border-left:4px solid {sev_color}; "
            f"border-radius:4px; padding:8px 12px; margin-bottom:8px;'>"
            f"<strong style='color:{sev_color};'>{alert['severity']}</strong> &mdash; "
            f"<span style='color:{OFF_WHITE};'>{alert['headline']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()

st.subheader("Revenue by Brand")
brand_rev = summary.groupby("brand")["revenue_aed"].sum().sort_values(ascending=True)
fig2 = px.bar(
    x=brand_rev.values,
    y=brand_rev.index,
    orientation="h",
    color=brand_rev.index,
    color_discrete_map=BRAND_COLORS,
    labels={"x": "Revenue (AED)", "y": ""},
)
fig2.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
fig2.update_xaxes(gridcolor="#2A3950", gridwidth=0.5)
st.plotly_chart(fig2, use_container_width=True)

st.markdown(
    f"<p style='text-align:center; color:#9BA8B8; margin-top:20px;'>"
    "Navigate to pages in the sidebar for detailed views "
    "&mdash; Morning Briefing, Group CEO, Brand Operations, Guest Intelligence, Operational Health"
    "</p>",
    unsafe_allow_html=True,
)
