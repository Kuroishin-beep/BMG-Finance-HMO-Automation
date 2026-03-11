"""
ui/styles.py
============
Injects a single block of custom CSS to override Streamlit's default theme.
Design direction: warm neutral — soft off-white canvas, slate text,
muted sage accents. Clean, restful, professional.
"""

import streamlit as st


CUSTOM_CSS = """
<style>
/* Google Font import  */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* CSS Variables  */
:root {
    --bg:          #F7F6F3;
    --surface:     #FFFFFF;
    --border:      #E4E2DC;
    --text-primary:#2C2C2C;
    --text-muted:  #7A7770;
    --accent:      #4A7C6F;      /* sage green */
    --accent-light:#EBF2F0;
    --warn:        #C4793A;
    --warn-light:  #FDF3EB;
    --error:       #B94040;
    --error-light: #FDECEA;
    --success:     #3A7A55;
    --success-light:#EBF5EF;
    --radius:      10px;
    --shadow:      0 1px 4px rgba(0,0,0,.07);
}

/* Page & app background  */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Sidebar (if ever enabled) */
[data-testid="stSidebar"] { background: var(--surface) !important; }

/* Main content container  */
[data-testid="stMainBlockContainer"],
.main .block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 960px !important;
}

/* Typography  */
h1 { font-size: 1.6rem !important; font-weight: 600 !important; letter-spacing: -.3px; }
h2 { font-size: 1.1rem !important; font-weight: 600 !important; color: var(--text-primary); }
h3 { font-size: 1rem   !important; font-weight: 500 !important; }
p, li, label, [data-testid="stText"] { font-size: .92rem !important; }

/* Caption / small text */
[data-testid="stCaptionContainer"] small,
.stCaption { color: var(--text-muted) !important; font-size: .82rem !important; }

/*  Tabs  */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1.5px solid var(--border) !important;
    gap: 0 !important;
    margin-bottom: .25rem !important;
}
[data-testid="stTabs"] button[role="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: .88rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    padding: .55rem 1.1rem !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
    border: 1.5px solid transparent !important;
    border-bottom: none !important;
    transition: color .15s, background .15s !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: var(--accent) !important;
    background: var(--accent-light) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    background: var(--surface) !important;
    border-color: var(--border) !important;
    border-bottom-color: var(--surface) !important;
}

/* Dividers  */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.4rem 0 !important; }

/* ── Step labels (subheaders used as step titles) ────── */
[data-testid="stSubheader"] {
    display: flex;
    align-items: center;
    gap: .5rem;
    color: var(--text-primary) !important;
    margin-bottom: .1rem !important;
}

/* Cards / section wrappers  */
/* We wrap each step in a visually quiet card using st.container(border=True) */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow) !important;
    padding: .1rem .2rem !important;
}

/* File uploader  */
[data-testid="stFileUploader"] {
    border: 1.5px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--surface) !important;
    padding: .6rem 1rem !important;
    transition: border-color .2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}
[data-testid="stFileUploader"] label {
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}
[data-testid="stFileDropzoneInstructions"] div span {
    color: var(--text-muted) !important;
    font-size: .82rem !important;
}

/*  Buttons  */
[data-testid="stBaseButton-primary"] > button,
button[kind="primary"] {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: .88rem !important;
    padding: .5rem 1.2rem !important;
    transition: background .15s, transform .1s !important;
    box-shadow: 0 1px 3px rgba(74,124,111,.25) !important;
}
[data-testid="stBaseButton-primary"] > button:hover,
button[kind="primary"]:hover {
    background: #3a6b5f !important;
    transform: translateY(-1px) !important;
}

[data-testid="stBaseButton-secondary"] > button,
button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: .88rem !important;
}
[data-testid="stBaseButton-secondary"] > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Download buttons */
[data-testid="stDownloadButton"] button {
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .88rem !important;
}

/*  Alert / info / success / error boxes  */
[data-testid="stAlertContainer"][data-baseweb="notification"] {
    border-radius: var(--radius) !important;
    font-size: .88rem !important;
    border-left-width: 3px !important;
    padding: .65rem 1rem !important;
}
/* Success */
div[data-testid="stAlertContainer"].st-ae {
    background: var(--success-light) !important;
    border-color: var(--success) !important;
    color: var(--success) !important;
}
/* Warning/info */
div[data-testid="stAlertContainer"].st-af {
    background: var(--warn-light) !important;
    border-color: var(--warn) !important;
}
/* Error */
div[data-testid="stAlertContainer"].st-ag {
    background: var(--error-light) !important;
    border-color: var(--error) !important;
}

/* Metrics  */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: .85rem 1rem .75rem !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stMetricLabel"] { font-size: .78rem !important; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: .5px; }
[data-testid="stMetricValue"] { font-size: 1.7rem !important; font-weight: 600 !important; color: var(--text-primary) !important; }

/*  Expanders  */
[data-testid="stExpander"] {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--surface) !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary {
    font-size: .88rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
}

/*─ Dataframes  */
[data-testid="stDataFrame"] iframe,
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    border: 1.5px solid var(--border) !important;
}

/* Spinner  */
[data-testid="stSpinner"] p { color: var(--text-muted) !important; font-size: .88rem !important; }

/* Scrollbar (webkit)  */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* Step badge helper (via st.markdown) */
.step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px; height: 22px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: .72rem;
    font-weight: 600;
    margin-right: .4rem;
    flex-shrink: 0;
}
.step-header {
    display: flex;
    align-items: center;
    gap: .4rem;
    margin: 1.1rem 0 .5rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
}
.step-header .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px; height: 22px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: .72rem;
    font-weight: 700;
    padding: 0 5px;
}
.muted { color: var(--text-muted); font-size: .83rem; margin-top: -.3rem; margin-bottom: .8rem; }
</style>
"""


def inject_styles() -> None:
    """Call once at app startup to inject the custom CSS."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def step_header(number: int, title: str, description: str = "") -> None:
    """Render a numbered step header with optional description."""
    st.markdown(
        f'<div class="step-header">'
        f'<span class="badge">{number}</span>{title}</div>'
        + (f'<p class="muted">{description}</p>' if description else ""),
        unsafe_allow_html=True,
    )