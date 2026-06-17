"""
theme.py
----------
Shared visual identity for CineScope, applied via custom CSS injected into
every page. Design language: a late-night screening room. Deep charcoal/navy
background (the screen glow look), warm marquee-amber accent for highlights
and rank numbers, and a clean grotesk for data with a tighter serif for
titles - nodding to film credits without being a costume.

Palette:
  --bg-primary:    #14141c   (near-black charcoal, theatre dark)
  --bg-secondary:  #1d1d29   (panel/card background)
  --bg-tertiary:   #262635   (hover/elevated surfaces)
  --accent:        #e8a33d   (marquee amber - rank numbers, highlights)
  --accent-soft:   #e8a33d22 (translucent accent for backgrounds)
  --text-primary:  #f1efe9   (warm off-white, not pure white)
  --text-muted:    #9a96a8   (secondary text)
  --success:       #5fb87a   (rising trend)
  --danger:        #d9695f   (falling trend)
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bitter:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-primary: #14141c;
    --bg-secondary: #1d1d29;
    --bg-tertiary: #262635;
    --accent: #e8a33d;
    --accent-soft: rgba(232, 163, 61, 0.13);
    --text-primary: #f1efe9;
    --text-muted: #9a96a8;
    --success: #5fb87a;
    --danger: #d9695f;
}

.stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

h1, h2, h3 {
    font-family: 'Bitter', serif !important;
    letter-spacing: -0.01em;
}

h1 {
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

h2, h3 {
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

p, div, span, label {
    font-family: 'Inter', sans-serif;
}

/* Eyebrow label style for section headers */
.cs-eyebrow {
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.72rem;
    color: var(--accent);
    font-weight: 600;
    margin-bottom: -0.6rem;
}

/* Card container */
.cs-card {
    background: var(--bg-secondary);
    border: 1px solid var(--bg-tertiary);
    border-radius: 6px;
    padding: 1.1rem 1.3rem;
}

/* Rank badge */
.cs-rank {
    font-family: 'Bitter', serif;
    font-weight: 700;
    font-size: 1.6rem;
    color: var(--accent);
    display: inline-block;
    min-width: 2.2rem;
}

.cs-trend-up { color: var(--success); font-weight: 600; }
.cs-trend-down { color: var(--danger); font-weight: 600; }
.cs-muted { color: var(--text-muted); font-size: 0.85rem; }

/* Streamlit metric override */
[data-testid="stMetric"] {
    background: var(--bg-secondary);
    border: 1px solid var(--bg-tertiary);
    border-radius: 6px;
    padding: 0.9rem 1rem;
}
[data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-family: 'Bitter', serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--bg-tertiary);
}

hr {
    border-color: var(--bg-tertiary) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--bg-tertiary);
    border-radius: 6px;
}
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def eyebrow(text: str):
    st.markdown(f"<div class='cs-eyebrow'>{text}</div>", unsafe_allow_html=True)


PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#1d1d29",
        "plot_bgcolor": "#1d1d29",
        "font": {"color": "#f1efe9", "family": "Inter, sans-serif"},
        "colorway": ["#e8a33d", "#5fb87a", "#d9695f", "#9a96a8", "#7c9fd8"],
        "xaxis": {"gridcolor": "#262635", "zerolinecolor": "#262635"},
        "yaxis": {"gridcolor": "#262635", "zerolinecolor": "#262635"},
        "legend": {"bgcolor": "rgba(0,0,0,0)"},
    }
}
