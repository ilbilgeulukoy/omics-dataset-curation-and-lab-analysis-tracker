import streamlit as st


ICONS = {
    "dashboard": """
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g_dash_1" x1="8" y1="8" x2="56" y2="56">
          <stop offset="0" stop-color="#71D7D0"/>
          <stop offset="1" stop-color="#7B8CFF"/>
        </linearGradient>
        <linearGradient id="g_dash_2" x1="10" y1="10" x2="54" y2="54">
          <stop offset="0" stop-color="#FFC38F"/>
          <stop offset="1" stop-color="#FF5EA8"/>
        </linearGradient>
      </defs>
      <rect x="12" y="12" width="16" height="16" rx="5" fill="url(#g_dash_1)"/>
      <rect x="36" y="12" width="16" height="24" rx="5" fill="url(#g_dash_2)"/>
      <rect x="12" y="36" width="16" height="16" rx="5" fill="#F4F7FF"/>
      <rect x="36" y="44" width="16" height="8" rx="4" fill="#7AA7FF"/>
    </svg>
    """,
    "schema": """
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g_schema_1" x1="12" y1="8" x2="52" y2="56">
          <stop offset="0" stop-color="#FFD084"/>
          <stop offset="1" stop-color="#FF8C5A"/>
        </linearGradient>
      </defs>
      <rect x="16" y="8" width="32" height="48" rx="10" fill="url(#g_schema_1)"/>
      <circle cx="44" cy="18" r="6" fill="#FFF0A6"/>
      <path d="M24 23H40M24 31H40M24 39H35" stroke="white" stroke-width="4" stroke-linecap="round"/>
    </svg>
    """,
    "templates": """
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g_temp_1" x1="10" y1="10" x2="54" y2="54">
          <stop offset="0" stop-color="#63C8F3"/>
          <stop offset="1" stop-color="#67D489"/>
        </linearGradient>
        <linearGradient id="g_temp_2" x1="18" y1="12" x2="46" y2="42">
          <stop offset="0" stop-color="#F5F7FF"/>
          <stop offset="1" stop-color="#DBE7FF"/>
        </linearGradient>
      </defs>
      <path d="M14 18C14 14.686 16.686 12 20 12H44C47.314 12 50 14.686 50 18V38C50 41.314 47.314 44 44 44H30L20 52V44C16.686 44 14 41.314 14 38V18Z" fill="url(#g_temp_1)"/>
      <rect x="31" y="18" width="15" height="15" rx="4" fill="url(#g_temp_2)"/>
      <rect x="18" y="19" width="8" height="8" rx="2.5" fill="#F2F6FF"/>
      <rect x="34.5" y="21.5" width="3.5" height="3.5" rx="1" fill="#71A4FF"/>
      <rect x="40" y="21.5" width="3.5" height="3.5" rx="1" fill="#D98BFF"/>
      <path d="M34 29.5H43.5" stroke="#6E83C8" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
    """,
    "notes": """
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g_notes_1" x1="12" y1="10" x2="52" y2="56">
          <stop offset="0" stop-color="#F7B2D9"/>
          <stop offset="1" stop-color="#F29F79"/>
        </linearGradient>
      </defs>
      <rect x="18" y="10" width="28" height="44" rx="10" fill="url(#g_notes_1)"/>
      <circle cx="45" cy="18" r="6" fill="#FFD7F1"/>
      <path d="M25 24H39M25 32H39M25 40H34" stroke="white" stroke-width="4" stroke-linecap="round"/>
    </svg>
    """,
    "graph": """
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 20L32 30L45 18M20 20L16 43L32 30L45 43M32 30L48 45" stroke="#76A7FF" stroke-width="3.5" stroke-linecap="round"/>
      <circle cx="20" cy="20" r="7" fill="#76D7F2"/>
      <circle cx="45" cy="18" r="6" fill="#F2F6FF"/>
      <circle cx="16" cy="43" r="6" fill="#B4F0D7"/>
      <circle cx="48" cy="45" r="7" fill="#D49CFF"/>
      <circle cx="32" cy="30" r="5" fill="#7AA7FF"/>
    </svg>
    """,
    "assistant": """
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g_ai_1" x1="14" y1="16" x2="50" y2="48">
          <stop offset="0" stop-color="#63C8F3"/>
          <stop offset="1" stop-color="#A783FF"/>
        </linearGradient>
      </defs>
      <rect x="14" y="18" width="36" height="24" rx="12" fill="url(#g_ai_1)"/>
      <circle cx="27" cy="30" r="3.5" fill="white"/>
      <circle cx="37" cy="30" r="3.5" fill="white"/>
      <path d="M28.5 37H35.5" stroke="white" stroke-width="3" stroke-linecap="round"/>
      <path d="M32 18V11" stroke="#A8D6FF" stroke-width="4" stroke-linecap="round"/>
      <circle cx="32" cy="9" r="3.5" fill="#EAF5FF"/>
    </svg>
    """,
}


def icon_html(name: str) -> str:
    return ICONS.get(name, ICONS["dashboard"])


def inject_liquid_glass_theme():
    st.markdown(
        """
<style>
:root {
    --bg-a: #f7fbff;
    --bg-b: #edf4fc;
    --bg-c: #f8fbff;
    --ink: #142033;
    --muted: #5e6d86;

    --glass-card: rgba(255,255,255,0.42);
    --glass-card-2: rgba(238,244,255,0.24);
    --glass-border: rgba(255,255,255,0.54);

    --hero-a: rgba(255,255,255,0.52);
    --hero-b: rgba(238,244,255,0.26);

    --tab-bg: rgba(255,255,255,0.58);
    --tab-bg-2: rgba(238,243,255,0.30);
    --tab-active: rgba(255,255,255,0.86);
    --tab-active-2: rgba(233,239,255,0.62);

    --icon-bg-1: rgba(255,255,255,0.90);
    --icon-bg-2: rgba(232,238,250,0.96);

    --soft-shadow: 0 10px 24px rgba(110,130,180,0.08);
    --soft-shadow-2: 0 18px 40px rgba(110,130,180,0.10);
}



html, body, [class*="css"] {
    color-scheme: light dark;
}

.stApp {
    background:
        radial-gradient(circle at 9% 11%, rgba(160, 215, 255, 0.22), transparent 24%),
        radial-gradient(circle at 91% 10%, rgba(214, 186, 255, 0.20), transparent 24%),
        radial-gradient(circle at 50% 90%, rgba(177, 224, 255, 0.12), transparent 34%),
        linear-gradient(180deg, var(--bg-a) 0%, var(--bg-b) 56%, var(--bg-c) 100%) !important;
    color: var(--ink);
}

.block-container {
    max-width: 1420px;
    padding-top: 3.4rem;
    padding-bottom: 2rem;
    animation: softPageIn 0.42s ease both;
}

h1, h2, h3, h4 {
    color: var(--ink) !important;
    letter-spacing: -0.035em !important;
}

p, label, span, div {
    color: inherit;
}

header[data-testid="stHeader"] {
    height: 3.05rem !important;
    background:
        linear-gradient(180deg, rgba(250,252,255,0.80), rgba(244,248,255,0.62)) !important;
    border-bottom: 1px solid rgba(224,232,244,0.58) !important;
    backdrop-filter: blur(22px) saturate(1.25) !important;
    -webkit-backdrop-filter: blur(22px) saturate(1.25) !important;
    box-shadow: 0 8px 24px rgba(90,110,160,0.05) !important;
}


div[data-testid="stToolbar"] {
    visibility: visible !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.58), rgba(244,248,255,0.44)) !important;
    border-right: 1px solid rgba(255,255,255,0.48) !important;
    backdrop-filter: blur(18px) saturate(1.16);
    -webkit-backdrop-filter: blur(18px) saturate(1.16);
}


.glass-hero {
    position: relative;
    overflow: hidden;
    padding: 27px 30px;
    border-radius: 32px;
    background:
        radial-gradient(circle at 13% 18%, rgba(255,255,255,0.74), transparent 28%),
        radial-gradient(circle at 92% 6%, rgba(218,194,255,0.18), transparent 32%),
        linear-gradient(135deg, var(--hero-a), var(--hero-b));
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(24px) saturate(1.22);
    -webkit-backdrop-filter: blur(24px) saturate(1.22);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.50),
        0 22px 48px rgba(105,125,175,0.08);
    margin: 0 0 22px 0;
}


.glass-title {
    position: relative;
    z-index: 1;
    font-size: 30px;
    line-height: 1.08;
    font-weight: 820;
    color: var(--ink);
    margin-bottom: 10px;
}

.glass-subtitle {
    position: relative;
    z-index: 1;
    max-width: 1040px;
    font-size: 15px;
    color: var(--muted);
    line-height: 1.58;
    font-weight: 500;
}

.module-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(145px, 1fr));
    gap: 15px;
    margin: 10px 0 22px 0;
    perspective: 1200px;
}

.flip-card {
    min-height: 150px;
    perspective: 1200px;
}

.flip-card-inner {
    position: relative;
    width: 100%;
    height: 150px;
    transform-style: preserve-3d;
    transition: transform 0.72s cubic-bezier(.2,.8,.2,1);
}

.flip-card:hover .flip-card-inner {
    transform: rotateY(180deg) translateY(-2px);
}

.flip-card-front,
.flip-card-back {
    position: absolute;
    inset: 0;
    border-radius: 28px;
    padding: 18px 16px;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    overflow: hidden;
    background:
        radial-gradient(circle at 24% 16%, rgba(255,255,255,0.48), transparent 34%),
        linear-gradient(135deg, var(--glass-card), var(--glass-card-2));
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(21px) saturate(1.24);
    -webkit-backdrop-filter: blur(21px) saturate(1.24);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.42),
        var(--soft-shadow);
}

.flip-card-back {
    transform: rotateY(180deg);
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.flip-card:hover .flip-card-front,
.flip-card:hover .flip-card-back {
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.48),
        var(--soft-shadow-2);
}

.module-icon-wrap,
.module-icon-wrap.purple,
.module-icon-wrap.cyan {
    width: 56px;
    height: 56px;
    border-radius: 17px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 13px;
    background:
        linear-gradient(180deg, var(--icon-bg-1), var(--icon-bg-2)) !important;
    border: 1px solid rgba(255,255,255,0.70) !important;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.74),
        0 8px 18px rgba(110,130,180,0.08) !important;
    backdrop-filter: blur(12px) saturate(1.08) !important;
    -webkit-backdrop-filter: blur(12px) saturate(1.08) !important;
}


.module-icon-wrap::before {
    display: none !important;
}

.module-icon-wrap svg {
    width: 38px !important;
    height: 38px !important;
    opacity: 1 !important;
    filter: saturate(1.06) contrast(1.02) !important;
}

.module-icon-wrap svg * {
    opacity: 1 !important;
}

.module-label {
    position: relative;
    z-index: 1;
    font-size: 14px;
    font-weight: 780;
    color: var(--ink) !important;
    margin-bottom: 7px;
    line-height: 1.25;
}

.module-desc {
    position: relative;
    z-index: 1;
    font-size: 12px;
    line-height: 1.45;
    color: var(--muted) !important;
}

div[data-testid="stTabs"] > div[role="tablist"] {
    display: inline-flex !important;
    width: auto !important;
    max-width: 100% !important;
    padding: 6px !important;
    gap: 4px !important;
    margin: 4px 0 18px 0 !important;
    border-radius: 18px !important;
    border: 1px solid var(--glass-border) !important;
    background:
        linear-gradient(135deg, var(--tab-bg), var(--tab-bg-2)) !important;
    backdrop-filter: blur(18px) saturate(1.2) !important;
    -webkit-backdrop-filter: blur(18px) saturate(1.2) !important;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.50),
        0 10px 24px rgba(112,130,180,0.08) !important;
    border-bottom: 1px solid var(--glass-border) !important;
}

button[role="tab"] {
    min-height: 34px !important;
    padding: 7px 11px !important;
    border-radius: 13px !important;
    color: var(--muted) !important;
    background: transparent !important;
    font-size: 12.5px !important;
    font-weight: 640 !important;
}

button[role="tab"] p {
    font-size: 12.5px !important;
    font-weight: 640 !important;
}

button[role="tab"][aria-selected="true"] {
    color: var(--ink) !important;
    background:
        linear-gradient(135deg, var(--tab-active), var(--tab-active-2)) !important;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.82),
        0 8px 18px rgba(115,135,220,0.10) !important;
}


.section-glass-header {
    display: flex;
    align-items: center;
    gap: 13px;
    margin: 22px 0 12px 0;
}

.section-dot {
    width: 40px;
    height: 40px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(180deg, var(--icon-bg-1), var(--icon-bg-2));
    border: 1px solid var(--glass-border);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.46),
        0 10px 22px rgba(120,140,205,0.08);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
}

.section-dot-inner {
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: linear-gradient(180deg, #fafdff, #98b8ff);
    box-shadow: 0 0 12px rgba(148,185,255,0.38);
}

.section-glass-title {
    font-size: 22px;
    font-weight: 780;
    letter-spacing: -0.04em;
    color: var(--ink);
}

.section-glass-caption {
    font-size: 13px;
    color: var(--muted);
    margin-top: 2px;
}

div[data-testid="stMetric"] {
    background:
        linear-gradient(135deg, var(--glass-card), var(--glass-card-2));
    border: 1px solid var(--glass-border);
    border-radius: 22px;
    padding: 14px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.42),
        var(--soft-shadow);
}

div[data-testid="stExpander"] {
    background:
        linear-gradient(135deg, var(--glass-card), var(--glass-card-2));
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    overflow: hidden;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: var(--soft-shadow);
}

div[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(227,233,245,0.75);
    box-shadow: 0 12px 24px rgba(105,125,175,0.05);
}


div.stButton > button,
div.stDownloadButton > button {
    border-radius: 14px;
    border: 1px solid rgba(220,228,244,0.84);
    background:
        linear-gradient(180deg, rgba(255,255,255,0.82), rgba(248,250,255,0.70));
    color: var(--ink);
    box-shadow: 0 8px 18px rgba(105,125,175,0.04);
}


div.stButton > button:hover,
div.stDownloadButton > button:hover {
    border-color: rgba(171,197,245,0.95);
    box-shadow: 0 10px 22px rgba(150,170,230,0.08);
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
textarea {
    background: rgba(255,255,255,0.78) !important;
    border: 1px solid rgba(223,230,244,0.95) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    color: var(--ink) !important;
}


.info-glass-card {
    padding: 16px 18px;
    border-radius: 18px;
    background:
        linear-gradient(135deg, var(--glass-card), var(--glass-card-2));
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: var(--soft-shadow);
    color: var(--muted);
    line-height: 1.55;
    margin-bottom: 16px;
}

@keyframes softPageIn {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 1200px) {
    .module-grid {
        grid-template-columns: repeat(3, minmax(180px, 1fr));
    }
}

@media (max-width: 760px) {
    .module-grid {
        grid-template-columns: repeat(1, minmax(220px, 1fr));
    }
}

@media (prefers-reduced-motion: reduce) {
    .flip-card-inner,
    .block-container {
        animation: none !important;
        transition: none !important;
    }
    .flip-card:hover .flip-card-inner {
        transform: none !important;
    }
}

/* LIGHT_STABILITY_PATCH_START */
/* Keep the UI stable even if Streamlit's native dark toggle is clicked */
.stApp,
.block-container {
    color: #142033 !important;
}

h1, h2, h3, h4,
.glass-title,
.section-glass-title,
.module-label,
div[data-testid="stMetricValue"],
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div {
    color: #142033 !important;
}

.glass-subtitle,
.section-glass-caption,
.module-desc,
.info-glass-card,
p, label, span {
    color: #5e6d86 !important;
}

div[data-testid="stMetric"] {
    background:
        linear-gradient(135deg, rgba(255,255,255,0.62), rgba(241,245,255,0.34)) !important;
    border: 1px solid rgba(255,255,255,0.58) !important;
}

div[data-testid="stMetricValue"] {
    opacity: 1 !important;
    visibility: visible !important;
}

.module-icon-wrap svg {
    opacity: 1 !important;
}
/* LIGHT_STABILITY_PATCH_END */

</style>
        """,
        unsafe_allow_html=True,
    )


def app_hero():
    st.markdown(
        f"""
<div class="glass-hero">
  <div class="glass-title">Omics Dataset Curation & Lab Analysis Tracker</div>
  <div class="glass-subtitle">
    Research dashboard for dataset registry management, metadata and QC readiness tracking,
    H5AD manifest organization, curation note indexing, and dataset relationship exploration before downstream analysis.
  </div>
</div>

<div class="module-grid">
  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="module-icon-wrap">{icon_html("dashboard")}</div>
        <div class="module-label">Dashboard</div>
      </div>
      <div class="flip-card-back">
        <div class="module-label">Dashboard</div>
        <div class="module-desc">Dataset overview, filters, metrics, and assay summaries.</div>
      </div>
    </div>
  </div>

  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="module-icon-wrap">{icon_html("schema")}</div>
        <div class="module-label">CSV Format Guide</div>
      </div>
      <div class="flip-card-back">
        <div class="module-label">CSV Format Guide</div>
        <div class="module-desc">Required and recommended metadata fields for structured dataset curation.</div>
      </div>
    </div>
  </div>

  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="module-icon-wrap">{icon_html("templates")}</div>
        <div class="module-label">CSV Templates</div>
      </div>
      <div class="flip-card-back">
        <div class="module-label">CSV Templates</div>
        <div class="module-desc">Input templates for datasets, samples, QC summaries, and H5AD manifests.</div>
      </div>
    </div>
  </div>

  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="module-icon-wrap">{icon_html("notes")}</div>
        <div class="module-label">Obsidian Notes</div>
      </div>
      <div class="flip-card-back">
        <div class="module-label">Obsidian Notes</div>
        <div class="module-desc">Markdown curation notes generated from the dataset registry.</div>
      </div>
    </div>
  </div>

  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="module-icon-wrap">{icon_html("graph")}</div>
        <div class="module-label">Knowledge Graph</div>
      </div>
      <div class="flip-card-back">
        <div class="module-label">Knowledge Graph</div>
        <div class="module-desc">Network view of datasets, accessions, papers, platforms, and status fields.</div>
      </div>
    </div>
  </div>

  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="module-icon-wrap">{icon_html("assistant")}</div>
        <div class="module-label">Curation Assistant</div>
      </div>
      <div class="flip-card-back">
        <div class="module-label">Curation Assistant</div>
        <div class="module-desc">SQLite full-text retrieval over indexed Obsidian curation notes.</div>
      </div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def glass_header(icon: str, title: str, caption: str = ""):
    st.markdown(
        f"""
<div class="section-glass-header">
  <div class="section-dot"><div class="section-dot-inner"></div></div>
  <div>
    <div class="section-glass-title">{title}</div>
    <div class="section-glass-caption">{caption}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def info_card(text: str):
    st.markdown(
        f"""
<div class="info-glass-card">
{text}
</div>
        """,
        unsafe_allow_html=True,
    )
