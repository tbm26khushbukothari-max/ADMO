NAVY = "#0F1A2E"
GOLD = "#C9A961"
OFF_WHITE = "#F7F4ED"
RED = "#C84B31"
AMBER = "#D89B3F"
GREEN = "#5A7D3C"
CARD_BG = "#1A2940"

BRAND_COLORS = {
    "Nammos": "#C9A961",
    "Em Sherif": "#C84B31",
    "CE LA VI": "#5A7D3C",
    "AlphaMind": "#D89B3F",
    "Other ADMO": "#7B8FA1",
}

SEVERITY_COLORS = {"Red": RED, "Amber": AMBER, "Green": GREEN}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=OFF_WHITE, size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def fmt_aed(value, prefix="AED "):
    if abs(value) >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{prefix}{value / 1_000:.0f}K"
    return f"{prefix}{value:,.0f}"


def fmt_usd(value):
    return fmt_aed(value, prefix="$")


def metric_card_css():
    return """
    <style>
    [data-testid="stMetric"] {
        background-color: #1A2940;
        border: 1px solid #2A3950;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #9BA8B8;
    }
    [data-testid="stMetricValue"] {
        color: #C9A961;
    }
    div[data-testid="stMetricDelta"] > div {
        font-size: 0.85rem;
    }
    </style>
    """
