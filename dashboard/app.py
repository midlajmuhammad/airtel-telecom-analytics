"""Airtel network usage dashboard for a network capacity planner.

All displayed metrics come from SQLite queries. Python prepares chart labels
and layouts; it does not recalculate the dashboard measures.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import hmac
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TABLES = {"customers", "usage_daily", "plans"}
OFFER_START = "2025-05"
MIN_GROUP = 100
RED = "#E4002B"
BLUE = "#4C6A92"
TEAL = "#188C8C"
GREY = "#687586"
GROUP_COLOURS = {"A": BLUE, "B": RED}

T3 = {
    "test": "Welch two-sample t-test",
    "tail": "one-tailed",
    "hypothesis": "B mean > A mean",
    "t": 19.45,
    "df": 17_444,
    "p": 1.1e-83,
    "mean_a": 1_393,
    "mean_b": 1_867,
    "n_a": 9_247,
    "n_b": 9_201,
}

st.set_page_config(
    page_title="Airtel | Network usage",
    page_icon=":material/cell_tower:",
    layout="wide",
    initial_sidebar_state="expanded",
)

header_image = base64.b64encode(
    (ROOT / "dashboard" / "assets" / "airtel_header.webp").read_bytes()
).decode("ascii")
sidebar_image = base64.b64encode(
    (ROOT / "dashboard" / "assets" / "airtel_sidebar.webp").read_bytes()
).decode("ascii")
logo_image = base64.b64encode(
    (ROOT / "dashboard" / "assets" / "airtel_logo.png").read_bytes()
).decode("ascii")
tab_background_image = base64.b64encode(
    (ROOT / "dashboard" / "assets" / "airtel_tab_background.png").read_bytes()
).decode("ascii")
st.html(
    """
    <style>
    :root { --airtel-red: #e4002b; --airtel-dark: #a9001e; }
    .stApp {
        background-image:
            linear-gradient(rgba(245,247,250,.68), rgba(245,247,250,.68)),
            url("data:image/png;base64,TAB_BACKGROUND_IMAGE");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container {
        width: 100%; max-width: none; margin: 0;
        padding: .35rem 1rem .45rem;
    }
    .airtel-banner {
        min-height: 54px; padding: 7px 18px; margin: 0 0 6px;
        border-radius: 10px; color: #fff;
        background-image: linear-gradient(90deg, rgba(228,0,43,.96) 0%, rgba(150,0,30,.84) 48%, rgba(4,12,36,.48) 100%),
                          url("data:image/webp;base64,HEADER_IMAGE");
        background-size: cover; background-position: 50% 48%;
        animation: airtelPan 24s ease-in-out infinite alternate;
        display: flex; align-items: center; gap: 18px;
        box-shadow: 0 4px 14px rgba(94, 0, 18, .15);
    }
    @keyframes airtelPan {
        from { background-position: 48% 48%; }
        to { background-position: 52% 52%; }
    }
    .airtel-wordmark { width: 48px; height: 48px; object-fit: contain; filter: brightness(0) invert(1); }
    .airtel-divider { height: 34px; border-left: 2px solid rgba(255,255,255,.75); }
    .airtel-title { font-size: 22px; font-weight: 750; line-height: 1.05; }
    .airtel-subtitle { font-size: 12px; opacity: .9; margin-top: 3px; }
    .chart-head {
        background: linear-gradient(100deg, #b80022, #e4002b);
        color: #fff; border-radius: 9px; padding: 9px 13px;
        margin: 0 0 6px; box-shadow: 0 2px 6px rgba(120, 0, 22, .12);
    }
    .chart-title { font-size: 14px; line-height: 1.2; font-weight: 750; }
    .chart-subtitle { margin-top: 3px; font-size: 11px; opacity: .88; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 8px; background: #eef0f3; padding: 4px; border-radius: 10px;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"] {
        height: 38px; border-radius: 8px; padding: 0 20px; font-weight: 700;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background: var(--airtel-red); color: white;
    }
    [role="tablist"] {
        gap: 8px; background: #eef0f3; padding: 4px; border-radius: 10px;
    }
    [role="tab"] {
        min-height: 40px; border-radius: 8px; padding: 0 20px;
        font-weight: 700; color: #344054;
    }
    [role="tab"][aria-selected="true"] {
        background: #e4002b; color: #fff;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #20252b;
        background-image:
            linear-gradient(rgba(20,24,31,.64), rgba(20,24,31,.64)),
            url("data:image/webp;base64,SIDEBAR_IMAGE");
        background-size: 100% 100%, cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2 { color: #f8fafc !important; }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: #f8fafc !important; }
    [data-testid="stSidebar"] hr { border-color: #50565e; }
    [data-testid="stMetric"] { background: #fff; border: 1px solid #e2e4e8; border-radius: 12px; padding: 12px 15px; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border-color: #e1e3e7; border-radius: 12px; }
    h1 { font-size: 1.28rem !important; margin: .25rem 0 .05rem !important; }
    [data-testid="stVerticalBlock"] { gap: .55rem; }
    [data-testid="stCaptionContainer"] p { font-size: .78rem; line-height: 1.25; }
    [data-testid="stCaptionContainer"] { color: #800020; }
    @media (max-width: 900px) {
      .airtel-title { font-size: 19px; }
      .airtel-wordmark { font-size: 20px; }
      .block-container { padding-left: .7rem; padding-right: .7rem; }
    }
    @media (prefers-reduced-motion: reduce) {
      .airtel-banner { animation: none; }
    }
    </style>
    <div class="airtel-banner">
      <img class="airtel-wordmark" src="data:image/png;base64,LOGO_IMAGE" alt="Airtel logo"><div class="airtel-divider"></div>
      <div><div class="airtel-title">Airtel Telecom Analytics</div>
      <div class="airtel-subtitle">Network Usage &amp; Capacity Planning</div></div>
    </div>
    """.replace("HEADER_IMAGE", header_image)
    .replace("SIDEBAR_IMAGE", sidebar_image)
    .replace("TAB_BACKGROUND_IMAGE", tab_background_image)
    .replace("LOGO_IMAGE", logo_image),
)


def has_tables(path: Path) -> bool:
    try:
        with sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        return REQUIRED_TABLES <= tables
    except sqlite3.Error:
        return False


def save_uploaded_database(uploaded_file) -> Path | None:
    """Extract only airtel.db from an authenticated ZIP into private temp storage."""
    destination = Path(tempfile.gettempdir()) / "airtel-cloud-upload.db"
    temporary = destination.with_suffix(".db.part")
    try:
        with ZipFile(uploaded_file) as archive:
            candidates = [
                item for item in archive.infolist()
                if not item.is_dir() and Path(item.filename).name.lower() == "airtel.db"
            ]
            if len(candidates) != 1 or candidates[0].file_size > 512 * 1024 * 1024:
                st.error("ZIP must contain one airtel.db file smaller than 512 MB.")
                return None
            with archive.open(candidates[0]) as source, temporary.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
        if not has_tables(temporary):
            temporary.unlink(missing_ok=True)
            st.error("The uploaded archive does not contain a valid Airtel SQLite database.")
            return None
        temporary.replace(destination)
        return destination
    except (BadZipFile, OSError, RuntimeError, sqlite3.Error) as exc:
        temporary.unlink(missing_ok=True)
        st.error(f"Could not read the uploaded database archive ({type(exc).__name__}).")
        return None


def download_drive_database(file_id: str, service_account_info: dict) -> Path | None:
    """Fetch a restricted Drive .gz file with read-only service-account access."""
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.service_account import Credentials

    cache_key = hashlib.sha256(file_id.encode("utf-8")).hexdigest()[:16]
    database_path = Path(tempfile.gettempdir()) / f"airtel-drive-{cache_key}.db"
    if database_path.exists() and has_tables(database_path):
        return database_path

    compressed_path = database_path.with_suffix(".db.gz.part")
    expanded_path = database_path.with_suffix(".db.part")
    try:
        credentials = Credentials.from_service_account_info(
            dict(service_account_info),
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        session = AuthorizedSession(credentials)
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        with session.get(
            download_url,
            params={"alt": "media"},
            stream=True,
            timeout=(20, 180),
        ) as response:
            response.raise_for_status()
            with compressed_path.open("wb") as output:
                total = 0
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        total += len(chunk)
                        if total > 512 * 1024 * 1024:
                            raise ValueError("Compressed database exceeds the 512 MB limit")
                        output.write(chunk)

        with gzip.open(compressed_path, "rb") as source, expanded_path.open("wb") as target:
            total = 0
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                if total > 1024 * 1024 * 1024:
                    raise ValueError("Expanded database exceeds the 1 GB limit")
                target.write(chunk)
        if not has_tables(expanded_path):
            raise ValueError("Downloaded file is not the expected Airtel SQLite database")
        expanded_path.replace(database_path)
        return database_path
    except Exception as exc:
        compressed_path.unlink(missing_ok=True)
        expanded_path.unlink(missing_ok=True)
        st.error(
            "Could not download and validate the restricted Google Drive database "
            f"({type(exc).__name__}). Check the file ID, service-account Secrets, "
            "and that the Drive file is shared with the service-account email.",
            icon=":material/error:",
        )
        return None
    finally:
        compressed_path.unlink(missing_ok=True)


def find_db() -> Path | None:
    candidates = []
    if os.environ.get("AIRTEL_DB"):
        candidates.append(Path(os.environ["AIRTEL_DB"]).expanduser())
    candidates.extend(
        [
            Path(tempfile.gettempdir()) / "airtel-cloud-upload.db",
            ROOT / "data" / "raw" / "airtel.db",
            ROOT / "data" / "airtel.db",
            ROOT / "airtel.db",
        ]
    )
    local_db = next((p for p in candidates if p.exists() and has_tables(p)), None)
    if local_db:
        return local_db

    # Streamlit Cloud secrets provide credentials for the restricted Drive file.
    try:
        db_secrets = st.secrets.get("database", {})
    except Exception:
        db_secrets = {}
    drive_file_id = db_secrets.get("drive_file_id")
    service_account_info = db_secrets.get("service_account")
    if drive_file_id and service_account_info:
        drive_db = download_drive_database(drive_file_id, service_account_info)
        if drive_db:
            return drive_db

    database_url = db_secrets.get("url") or os.environ.get("AIRTEL_DB_URL")
    access_token = db_secrets.get("token") or os.environ.get("AIRTEL_DB_TOKEN")
    if not database_url:
        return None
    if not database_url.lower().startswith("https://"):
        st.error("The private database URL must use HTTPS.", icon=":material/lock:")
        return None

    url_key = hashlib.sha256(database_url.encode("utf-8")).hexdigest()[:16]
    destination = Path(tempfile.gettempdir()) / f"airtel-private-{url_key}.db"
    if destination.exists() and has_tables(destination):
        return destination

    request_headers = {"User-Agent": "AirtelAnalyticsDashboard/1.0"}
    if access_token:
        request_headers["Authorization"] = f"Bearer {access_token}"
    request = Request(database_url, headers=request_headers)
    temporary = destination.with_suffix(".db.part")
    try:
        with urlopen(request, timeout=180) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if not has_tables(temporary):
            temporary.unlink(missing_ok=True)
            st.error(
                "The private database URL did not return a valid Airtel SQLite database. "
                "Check the file URL and access settings in Streamlit Cloud Secrets.",
                icon=":material/error:",
            )
            return None
        temporary.replace(destination)
        return destination
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, sqlite3.Error) as exc:
        temporary.unlink(missing_ok=True)
        st.error(
            "Could not load the private Airtel database from its configured HTTPS source "
            f"({type(exc).__name__}). Check the URL, token, and file permissions in "
            "Streamlit Cloud Secrets.",
            icon=":material/error:",
        )
        return None


DB_PATH = find_db()

if DB_PATH is None:
    st.title("Airtel network usage")
    st.warning("The dashboard database has not been loaded in this Streamlit Cloud instance.")
    try:
        upload_password = st.secrets.get("database", {}).get("upload_password", "")
    except Exception:
        upload_password = ""
    if upload_password:
        entered_password = st.text_input("Dashboard setup password", type="password")
        if entered_password and hmac.compare_digest(entered_password, upload_password):
            uploaded_archive = st.file_uploader(
                "Upload the Airtel database ZIP", type=["zip"], max_upload_size=200
            )
            if uploaded_archive is not None:
                DB_PATH = save_uploaded_database(uploaded_archive)
        elif entered_password:
            st.error("Incorrect setup password.")
    else:
        st.info(
            "For private Google Drive loading, configure `drive_file_id` and "
            "`service_account` under Streamlit Cloud Secrets, then reboot this app. "
            "Alternatively, add `upload_password` to enable the protected ZIP uploader."
        )
    if DB_PATH is None:
        st.stop()


@st.cache_data(show_spinner=False)
def q(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a read-only SQL query and cache the resulting table."""
    with sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True) as conn:
        return pd.read_sql_query(sql, conn, params=params or {})


def fmt_month(key: str) -> str:
    return datetime.strptime(key, "%Y-%m").strftime("%b %Y")


def metric_card(title: str, value: str, detail: str, *, fixed: bool = False) -> None:
    badge = (
        '<span style="margin-left:8px;padding:2px 7px;border-radius:999px;'
        'background:#ffe2e7;color:#a9001e;font-size:9px;font-weight:700;'
        'letter-spacing:.04em">FIXED</span>'
        if fixed
        else ""
    )
    st.html(
        '<div style="box-sizing:border-box;min-height:94px;height:100%;padding:9px 12px;'
        'border:1px solid #e1e4e8;border-left:4px solid #e4002b;border-radius:13px;'
        'background:linear-gradient(145deg,#fff 55%,#fff5f6);'
        'box-shadow:0 2px 9px rgba(29,39,54,.055);font-family:Arial,sans-serif">'
        f'<div style="font-size:12px;font-weight:700;color:#344054">{escape(title)}{badge}</div>'
        f'<div style="font-size:20px;font-weight:750;line-height:1.08;color:#a9001e;margin:5px 0 4px">{escape(value)}</div>'
        f'<div style="font-size:9px;line-height:1.3;color:#687586">{escape(detail)}</div>'
        '</div>'
    )


def chart_style(fig: go.Figure, *, height: int, title: str, subtitle: str) -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(
            text=f"{title}<br><sup>{subtitle}</sup>",
            x=0.02,
            xanchor="left",
            y=0.98,
            yanchor="top",
            font=dict(size=14, color="#172B4D"),
        ),
        margin=dict(l=12, r=12, t=60, b=14),
        font=dict(family="Arial, sans-serif", size=11, color="#800020"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(
        automargin=True, showgrid=False, zeroline=False,
        tickfont=dict(color="#800020"), title_font=dict(color="#800020"),
    )
    fig.update_yaxes(
        automargin=True, gridcolor="#E8EDF2", zeroline=False,
        tickfont=dict(color="#800020"), title_font=dict(color="#800020"),
    )
    return fig


def show_chart(
    fig: go.Figure, *, key: str, alt: str, include_month: bool = False
) -> None:
    title_text = fig.layout.title.text or ""
    title_parts = title_text.split("<br><sup>", maxsplit=1)
    title = escape(title_parts[0])
    subtitle = escape(title_parts[1].removesuffix("</sup>")) if len(title_parts) > 1 else ""
    fig.update_layout(title=None, margin=dict(l=12, r=12, t=18, b=14))
    with st.container(border=True):
        chart_col, filter_col = st.columns([5.2, 1], gap="small", vertical_alignment="top")
        with chart_col:
            st.html(
                '<div style="background:linear-gradient(100deg,#b80022,#e4002b);'
                'color:#fff;border-radius:9px;padding:9px 13px;margin:0 0 6px;'
                'box-shadow:0 2px 6px rgba(120,0,22,.12);font-family:Arial,sans-serif">'
                f'<div style="font-size:14px;line-height:1.2;font-weight:750">{title}</div>'
                f'<div style="margin-top:3px;font-size:11px;line-height:1.35;opacity:.9">{subtitle}</div>'
                '</div>'
            )
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
                key=key,
                alt=alt,
                on_select="ignore",
            )
        with filter_col:
            with st.popover("Filters", icon=":material/filter_alt:", use_container_width=True):
                chart_filter_controls(key, include_month=include_month)


def no_data(message: str = "No data for this filter combination.") -> None:
    st.info(message, icon=":material/info:")


st.sidebar.title("Airtel network usage")
st.sidebar.caption("Network Usage & Capacity Planning")
st.sidebar.divider()
st.sidebar.subheader("Summary filters")
st.sidebar.caption("Each chart has its own independent Filters control.")
circle_options = q(
    "SELECT circle_name FROM circles WHERE circle_name IS NOT NULL ORDER BY 1"
)["circle_name"].tolist()
region_options = q(
    "SELECT DISTINCT region FROM circles "
    "WHERE region IS NOT NULL ORDER BY 1"
)["region"].tolist()
conn_options = q(
    "SELECT DISTINCT connection_type FROM customers "
    "WHERE connection_type IS NOT NULL ORDER BY 1"
)["connection_type"].tolist()
device_options = q(
    "SELECT DISTINCT device_type FROM customers "
    "WHERE device_type IS NOT NULL ORDER BY 1"
)["device_type"].tolist()
segment_options = q(
    "SELECT DISTINCT age_band FROM customers "
    "WHERE age_band IS NOT NULL ORDER BY 1"
)["age_band"].tolist()
plan_options = q(
    "SELECT DISTINCT plan_type FROM plans "
    "WHERE plan_type IS NOT NULL ORDER BY 1"
)["plan_type"].tolist()
month_keys = q(
    "SELECT DISTINCT strftime('%Y-%m', usage_date) AS month "
    "FROM usage_daily ORDER BY month"
)["month"].tolist()

sel_circle = st.sidebar.selectbox(
    ":material/location_on: Circle", ["All", *circle_options], key="filter_circle"
)
selected_range = st.sidebar.select_slider(
    ":material/date_range: Date range",
    options=month_keys,
    value=(month_keys[0], month_keys[-1]),
    format_func=fmt_month,
    key="filter_date_range",
)
available_months = [m for m in month_keys if selected_range[0] <= m <= selected_range[1]]
sel_segment = st.sidebar.selectbox(
    ":material/groups: Customer segment",
    ["All", *segment_options],
    key="filter_segment",
)
sel_plan = st.sidebar.selectbox(
    ":material/layers: Plan type", ["All", *plan_options], key="filter_plan_type"
)
sel_region = st.sidebar.selectbox(
    ":material/map: Region", ["All", *region_options], key="filter_region"
)
sel_conn = st.sidebar.selectbox(
    ":material/signal_cellular_alt: Connection type",
    ["All", *conn_options],
    key="filter_connection_type",
)
sel_device = st.sidebar.selectbox(
    ":material/devices: Device type", ["All", *device_options], key="filter_device_type"
)
previous_summary_month = st.session_state.get("filter_detail_month")
if previous_summary_month not in available_months:
    st.session_state["filter_detail_month"] = available_months[-1]
summary_month_key = st.sidebar.selectbox(
    ":material/calendar_month: Summary month",
    available_months,
    index=available_months.index(st.session_state["filter_detail_month"]),
    format_func=fmt_month,
    key="filter_detail_month",
)
GLOBAL_PARAMS = {
    "circle": sel_circle,
    "region": sel_region,
    "segment": sel_segment,
    "plan_type": sel_plan,
    "conn": sel_conn,
    "device": sel_device,
    "start_month": selected_range[0],
    "end_month": selected_range[1],
}

CUSTOMER_FILTER = (
    "(:circle = 'All' OR cir.circle_name = :circle) "
    "AND (:segment = 'All' OR c.age_band = :segment) "
    "AND (:plan_type = 'All' OR c.current_plan_id IN "
    "(SELECT plan_id FROM plans WHERE plan_type = :plan_type)) "
    "AND (:region = 'All' OR cir.region = :region) "
    "AND (:conn = 'All' OR c.connection_type = :conn) "
    "AND (:device = 'All' OR c.device_type = :device) "
)
FILTER = CUSTOMER_FILTER + (
    " AND strftime('%Y-%m', u.usage_date) BETWEEN :start_month AND :end_month"
)


def chart_filter_params(key: str, *, include_month: bool = False) -> dict[str, str]:
    prefix = f"chart_filter_{key}"
    selected_range = st.session_state.get(
        f"{prefix}_date_range", (month_keys[0], month_keys[-1])
    )
    params = {
        "circle": st.session_state.get(f"{prefix}_circle", "All"),
        "region": st.session_state.get(f"{prefix}_region", "All"),
        "segment": st.session_state.get(f"{prefix}_segment", "All"),
        "plan_type": st.session_state.get(f"{prefix}_plan", "All"),
        "conn": st.session_state.get(f"{prefix}_connection", "All"),
        "device": st.session_state.get(f"{prefix}_device", "All"),
        "start_month": selected_range[0],
        "end_month": selected_range[-1],
    }
    if include_month:
        available = [m for m in month_keys if params["start_month"] <= m <= params["end_month"]]
        chosen_month = st.session_state.get(f"{prefix}_month", available[-1])
        params["month"] = chosen_month if chosen_month in available else available[-1]
    return params


def chart_filter_controls(key: str, *, include_month: bool = False) -> None:
    """Render filters scoped to one chart; values are read by its SQL on rerun."""
    prefix = f"chart_filter_{key}"
    st.caption("These filters affect this chart only.")
    st.selectbox("Circle", ["All", *circle_options], key=f"{prefix}_circle")
    st.selectbox("Region", ["All", *region_options], key=f"{prefix}_region")
    st.selectbox("Customer segment", ["All", *segment_options], key=f"{prefix}_segment")
    st.selectbox("Plan type", ["All", *plan_options], key=f"{prefix}_plan")
    st.selectbox("Connection type", ["All", *conn_options], key=f"{prefix}_connection")
    st.selectbox("Device type", ["All", *device_options], key=f"{prefix}_device")
    default_range = (month_keys[0], month_keys[-1])
    selected_range = st.select_slider(
        "Date range",
        options=month_keys,
        value=st.session_state.get(f"{prefix}_date_range", default_range),
        format_func=fmt_month,
        key=f"{prefix}_date_range",
    )
    if include_month:
        available = [m for m in month_keys if selected_range[0] <= m <= selected_range[-1]]
        previous = st.session_state.get(f"{prefix}_month")
        if previous not in available:
            st.session_state[f"{prefix}_month"] = available[-1]
        st.selectbox(
            "Detail month", available,
            format_func=fmt_month,
            key=f"{prefix}_month",
        )


def filter_scope(params: dict[str, str]) -> str:
    chosen = [
        f"Circle: {params['circle']}" if params["circle"] != "All" else "",
        f"Region: {params['region']}" if params["region"] != "All" else "",
        f"Segment: {params['segment']}" if params["segment"] != "All" else "",
        f"Plan: {params['plan_type']}" if params["plan_type"] != "All" else "",
        f"Connection: {params['conn']}" if params["conn"] != "All" else "",
        f"Device: {params['device']}" if params["device"] != "All" else "",
    ]
    active = " · ".join(value for value in chosen if value) or "All circles and segments"
    return f"{active} | {fmt_month(params['start_month'])} – {fmt_month(params['end_month'])}"


tab_overview, tab_detail = st.tabs(["Overview", "Detail"])


with tab_overview:
    st.title("Airtel network usage | Overview")
    st.caption(
        "This dashboard helps Network Capacity Planner understand data demand, "
        "subscriber usage patterns and capacity-planning needs. Use each chart's Filters control "
        "to update that chart independently."
    )

    fixed_days = q("""
        SELECT (SELECT COUNT(*) FROM usage_daily) AS total_days,
               (SELECT COUNT(DISTINCT customer_id) FROM usage_daily) AS total_subs,
               (SELECT MIN(usage_date) FROM usage_daily) AS first_day,
               (SELECT MAX(usage_date) FROM usage_daily) AS last_day
    """).iloc[0]

    averages = q(f"""
        WITH cal AS (
            SELECT COUNT(DISTINCT usage_date) AS d FROM usage_daily
             WHERE strftime('%Y-%m', usage_date) BETWEEN :start_month AND :end_month
        ),
        subscriber AS (
            SELECT c.customer_id, COUNT(u.customer_id) AS days,
                   SUM(u.data_mb) AS mb
              FROM customers c
              LEFT JOIN usage_daily u ON u.customer_id = c.customer_id
               AND strftime('%Y-%m', u.usage_date) BETWEEN :start_month AND :end_month
              LEFT JOIN circles cir ON cir.circle_id = c.circle_id
             WHERE {CUSTOMER_FILTER}
             GROUP BY c.customer_id
        )
        SELECT ROUND(AVG(mb / NULLIF(days, 0)), 0) AS per_usage_day,
               SUM(days > 0) AS active_subs,
               ROUND(AVG(COALESCE(mb, 0) / cal.d), 0) AS per_calendar_day,
               COUNT(*) AS all_subs, cal.d AS calendar_days
          FROM subscriber, cal
    """, GLOBAL_PARAMS).iloc[0]

    card_cols = st.columns(3, gap="small")
    with card_cols[0]:
        metric_card(
            "Usage-days recorded",
            f"{int(fixed_days.total_days):,}",
            "One usage-day is one subscriber with a record on one date. "
            f"Fixed total covers {fixed_days.first_day} to {fixed_days.last_day} "
            f"and {int(fixed_days.total_subs):,} subscribers.",
            fixed=True,
        )
    with card_cols[1]:
        metric_card(
            "Validated T3 test | Group B vs A",
            f"p = {T3['p']:.1e}",
            f"Welch test, {T3['tail']}, H1: B > A; t = {T3['t']:.2f}, "
            f"df = {T3['df']:,}. May-Jun daily mean: B {T3['mean_b']:,} MB "
            f"(n={T3['n_b']:,}) vs A {T3['mean_a']:,} MB (n={T3['n_a']:,}). "
            "Evidence of a difference does not establish cause.",
            fixed=True,
        )
    with card_cols[2]:
        usage_value = (
            f"{averages.per_usage_day:,.0f} MB / {averages.per_calendar_day:,.0f} MB"
            if pd.notna(averages.per_usage_day)
            else "No data"
        )
        metric_card(
            "Average data per subscriber",
            usage_value,
            f"First value per subscriber usage-day (n={int(averages.active_subs or 0):,}); "
            f"second per calendar day ({int(averages.calendar_days)} days, "
            f"n={int(averages.all_subs):,}). Both are MB.",
        )

    hero_params = chart_filter_params("overview_monthly_usage_heatmap")
    hero_scope = filter_scope(hero_params)
    hero_month_keys = [
        m for m in month_keys if hero_params["start_month"] <= m <= hero_params["end_month"]
    ]
    hero = q(f"""
        WITH calendar AS (
            SELECT strftime('%Y-%m', usage_date) AS month,
                   COUNT(DISTINCT usage_date) AS days
              FROM usage_daily GROUP BY month
        ), subscriber_month AS (
            SELECT c.ab_group AS grp, strftime('%Y-%m', u.usage_date) AS month,
                   u.customer_id, COUNT(*) AS usage_days, SUM(u.data_mb) AS mb
              FROM usage_daily u JOIN customers c ON c.customer_id = u.customer_id
              LEFT JOIN circles cir ON cir.circle_id = c.circle_id
             WHERE {FILTER}
             GROUP BY c.ab_group, month, u.customer_id
        )
        SELECT sm.month, sm.grp, COUNT(*) AS subscribers,
               ROUND(AVG(sm.mb / sm.usage_days), 0) AS per_usage_day,
               ROUND(AVG(sm.mb / cal.days), 0) AS per_calendar_day
          FROM subscriber_month sm JOIN calendar cal ON cal.month = sm.month
         GROUP BY sm.month, sm.grp ORDER BY sm.month, sm.grp
    """, hero_params)

    subs_params = chart_filter_params("overview_monthly_subscribers_treemap")
    subs_scope = filter_scope(subs_params)
    monthly_subs = q(f"""
        SELECT strftime('%Y-%m', u.usage_date) AS month,
               COUNT(DISTINCT u.customer_id) AS subscribers
          FROM usage_daily u JOIN customers c ON c.customer_id = u.customer_id
          LEFT JOIN circles cir ON cir.circle_id = c.circle_id
         WHERE {FILTER}
         GROUP BY month ORDER BY month
    """, subs_params)

    plan_params = chart_filter_params("overview_plan_allowance_violin")
    plan_scope = filter_scope(plan_params)
    plan_usage = q(f"""
        WITH plan AS (
            SELECT plan_id, plan_name,
                   CASE WHEN INSTR(data_quota, '/day') > 0
                        THEN CAST(SUBSTR(data_quota, 1, INSTR(data_quota, ' ') - 1) AS REAL) * 30
                        ELSE CAST(SUBSTR(data_quota, 1, INSTR(data_quota, ' ') - 1) AS REAL)
                   END AS monthly_gb
              FROM plans
        ), months AS (
            SELECT COUNT(DISTINCT strftime('%Y-%m', usage_date)) AS n
              FROM usage_daily
             WHERE strftime('%Y-%m', usage_date) BETWEEN :start_month AND :end_month
        ), subscriber AS (
            SELECT c.customer_id, c.current_plan_id AS plan_id, SUM(u.data_mb) AS mb
              FROM customers c JOIN usage_daily u ON u.customer_id = c.customer_id
              LEFT JOIN circles cir ON cir.circle_id = c.circle_id
             WHERE {FILTER}
             GROUP BY c.customer_id
        ), normalized AS (
            SELECT p.plan_name, s.customer_id,
                   COUNT(*) OVER (PARTITION BY p.plan_name) AS subscribers,
                   CASE WHEN COUNT(*) OVER (PARTITION BY p.plan_name) >= {MIN_GROUP}
                        THEN ROUND(100.0 * (s.mb / 1024.0 / m.n) / p.monthly_gb, 2)
                   END AS utilization_pct
              FROM subscriber s JOIN plan p ON p.plan_id = s.plan_id
              CROSS JOIN months m
        )
        SELECT plan_name, subscribers, utilization_pct
          FROM normalized ORDER BY plan_name, customer_id
    """, plan_params)

    left, right = st.columns([1.45, 1], gap="small")
    with left:
        if hero.empty:
            no_data()
        else:
            heat_y = []
            heat_z = []
            for group in [g for g in ("A", "B") if g in hero["grp"].values]:
                for col, denominator in (
                    ("per_usage_day", "usage-day"),
                    ("per_calendar_day", "calendar-day"),
                ):
                    heat_y.append(f"Group {group} | {denominator}")
                    monthly = hero[hero["grp"] == group].set_index("month")
                    heat_z.append(
                        [monthly.loc[m, col] if m in monthly.index else None for m in hero_month_keys]
                    )
            fig = go.Figure(
                go.Heatmap(
                    x=[fmt_month(m) for m in hero_month_keys],
                    y=heat_y,
                    z=heat_z,
                    colorscale="Reds",
                    colorbar=dict(title="MB / day", thickness=10, len=0.78),
                    hovertemplate="%{y}<br>%{x}: %{z:,.0f} MB per subscriber<extra></extra>",
                    xgap=2,
                    ygap=3,
                )
            )
            fig.update_yaxes(autorange="reversed", title=None)
            fig.update_xaxes(title="Month", tickangle=-25)
            chart_style(
                fig,
                height=205,
                title="Monthly data per subscriber by group and denominator",
                subtitle=f"Usage-day vs calendar-day means | {hero_scope}",
            )
            show_chart(
                fig,
                key="overview_monthly_usage_heatmap",
                alt="Monthly data per subscriber by experiment group and day denominator",
            )

    with right:
        if monthly_subs.empty:
            no_data()
        else:
            fig = go.Figure(
                go.Treemap(
                    labels=[fmt_month(m) for m in monthly_subs["month"]],
                    parents=[""] * len(monthly_subs),
                    values=monthly_subs["subscribers"],
                    texttemplate="%{label}<br><b>%{value:,}</b>",
                    textfont=dict(size=11, color="white"),
                    marker=dict(colors=monthly_subs["subscribers"], colorscale="Blues", line=dict(color="white", width=2)),
                    hovertemplate="%{label}<br>%{value:,} active subscribers<extra></extra>",
                    branchvalues="total",
                )
            )
            chart_style(
                fig,
                height=112,
                title="Monthly active subscriber counts",
                subtitle=f"At least one usage-day in the month | {subs_scope}",
            )
            show_chart(
                fig,
                key="overview_monthly_subscribers_treemap",
                alt="Monthly subscriber count tiles, sized by the number of active subscribers",
            )

        if plan_usage.empty or plan_usage["utilization_pct"].notna().sum() == 0:
            no_data("No plan group has at least 100 subscribers for this filter.")
        else:
            plot = plan_usage[plan_usage["utilization_pct"].notna()]
            plan_order = sorted(plot["plan_name"].drop_duplicates().tolist())
            fig = go.Figure()
            for plan_name in plan_order:
                values = plot.loc[plot["plan_name"] == plan_name, "utilization_pct"]
                count = int(plot.loc[plot["plan_name"] == plan_name, "subscribers"].iloc[0])
                fig.add_trace(
                    go.Violin(
                        x=[plan_name] * len(values),
                        y=values,
                        name=plan_name,
                        box=dict(visible=True),
                        meanline=dict(visible=True),
                        points=False,
                        line_color=TEAL,
                        fillcolor="rgba(24,140,140,0.30)",
                        hovertemplate=f"{plan_name}<br>%{{y:.1f}}% of allowance<extra>n={count:,}</extra>",
                    )
                )
            fig.update_xaxes(title="Plan", tickangle=-18)
            fig.update_yaxes(title="Monthly data used / monthly allowance (%)", ticksuffix="%", rangemode="tozero")
            chart_style(
                fig,
                height=125,
                title="Subscriber allowance use by plan",
                subtitle=f"Per-subscriber distribution | plan allowance averaged monthly | {plan_scope}",
            )
            show_chart(
                fig,
                key="overview_plan_allowance_violin",
                alt="Distribution of subscriber data use as a percentage of plan allowance",
            )


with tab_detail:
    st.title("Airtel network usage | Detail")
    st.caption(
        "This dashboard helps Network Capacity Planner understand data demand, "
        "subscriber usage patterns and capacity-planning needs. Use each chart's Filters control "
        "to update that chart independently."
    )
    month = summary_month_key
    selected_month = fmt_month(month)

    month_metrics = q(f"""
        WITH calendar AS (
            SELECT COUNT(DISTINCT usage_date) AS days FROM usage_daily
             WHERE strftime('%Y-%m', usage_date) = :month
        ), subscriber AS (
            SELECT u.customer_id, COUNT(*) AS usage_days, SUM(u.data_mb) AS mb
              FROM usage_daily u JOIN customers c ON c.customer_id = u.customer_id
              LEFT JOIN circles cir ON cir.circle_id = c.circle_id
             WHERE {FILTER} AND strftime('%Y-%m', u.usage_date) = :month
             GROUP BY u.customer_id
        )
        SELECT COUNT(*) AS active_subs, SUM(usage_days) AS usage_days,
               ROUND(SUM(mb) / 1024.0 / 1024.0, 2) AS total_tb,
               ROUND(SUM(mb), 0) AS total_mb,
               ROUND(AVG(mb / usage_days), 0) AS per_usage_day,
               ROUND(AVG(mb / calendar.days), 0) AS per_calendar_day,
               calendar.days AS calendar_days
          FROM subscriber, calendar
    """, {**GLOBAL_PARAMS, "month": month}).iloc[0]

    metric_cols = st.columns(3, gap="small")
    with metric_cols[0]:
        metric_card(
            f"Active subscribers | {selected_month}",
            f"{int(month_metrics.active_subs or 0):,}",
            "Active means at least one usage-day under the current sidebar filters.",
        )
    with metric_cols[1]:
        metric_card(
            f"Data carried | {selected_month}",
            f"{month_metrics.total_tb or 0:,.2f} TB",
            f"{month_metrics.total_mb or 0:,.0f} MB divided by 1,024 squared. "
            f"{int(month_metrics.usage_days or 0):,} usage-days.",
        )
    with metric_cols[2]:
        metric_card(
            f"Data per subscriber usage-day | {selected_month}",
            f"{month_metrics.per_usage_day or 0:,.0f} MB",
            f"Mean of each active subscriber's data divided by their own usage-days. "
            f"Calendar-day measure: {month_metrics.per_calendar_day or 0:,.0f} MB "
            f"over {int(month_metrics.calendar_days)} days.",
        )

    daily_params = chart_filter_params("detail_daily_load_calendar_heatmap", include_month=True)
    daily_scope = filter_scope(daily_params)
    daily_month = fmt_month(daily_params["month"])
    daily = q(f"""
        SELECT u.usage_date AS day,
               CAST(strftime('%d', u.usage_date) AS INTEGER) AS day_num,
               CAST(strftime('%w', u.usage_date) AS INTEGER) AS weekday_num,
               ROUND(SUM(u.data_mb) / 1024.0 / 1024.0, 3) AS tb,
               COUNT(*) AS usage_days,
               ROUND(AVG(SUM(u.data_mb) / 1024.0 / 1024.0) OVER (), 3) AS mean_tb
          FROM usage_daily u JOIN customers c ON c.customer_id = u.customer_id
          LEFT JOIN circles cir ON cir.circle_id = c.circle_id
         WHERE {FILTER} AND strftime('%Y-%m', u.usage_date) = :month
         GROUP BY u.usage_date ORDER BY u.usage_date
    """, daily_params)

    group_params = chart_filter_params("detail_group_box_plot", include_month=True)
    group_scope = filter_scope(group_params)
    group_month = fmt_month(group_params["month"])
    group_dist = q(f"""
        WITH subscriber AS (
            SELECT c.ab_group AS label, u.customer_id, COUNT(*) AS days,
                   SUM(u.data_mb) AS mb
              FROM usage_daily u JOIN customers c ON c.customer_id = u.customer_id
              LEFT JOIN circles cir ON cir.circle_id = c.circle_id
             WHERE {FILTER} AND strftime('%Y-%m', u.usage_date) = :month
             GROUP BY c.ab_group, u.customer_id
        ), counted AS (
            SELECT label, customer_id, days, mb,
                   COUNT(*) OVER (PARTITION BY label) AS subscribers
              FROM subscriber
        )
        SELECT label, customer_id, subscribers,
               CASE WHEN subscribers >= {MIN_GROUP}
                    THEN ROUND(mb / days, 0) END AS mb_per_usage_day
          FROM counted ORDER BY label, customer_id
    """, group_params)

    device_params = chart_filter_params("detail_device_violin_plot", include_month=True)
    device_scope = filter_scope(device_params)
    device_month = fmt_month(device_params["month"])
    device_dist = q(f"""
        WITH subscriber AS (
            SELECT c.device_type AS label, u.customer_id, COUNT(*) AS days,
                   SUM(u.data_mb) AS mb
              FROM usage_daily u JOIN customers c ON c.customer_id = u.customer_id
              LEFT JOIN circles cir ON cir.circle_id = c.circle_id
             WHERE {FILTER} AND strftime('%Y-%m', u.usage_date) = :month
             GROUP BY c.device_type, u.customer_id
        ), counted AS (
            SELECT label, customer_id, days, mb,
                   COUNT(*) OVER (PARTITION BY label) AS subscribers
              FROM subscriber
        )
        SELECT label, customer_id, subscribers,
               CASE WHEN subscribers >= {MIN_GROUP}
                    THEN ROUND(mb / days, 0) END AS mb_per_usage_day
          FROM counted ORDER BY label, customer_id
    """, device_params)

    chart_left, chart_right = st.columns([1.45, 1], gap="small")
    with chart_left:
        if daily.empty:
            no_data()
        else:
            weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            z = [[None for _ in range(31)] for _ in weekdays]
            custom = [[None for _ in range(31)] for _ in weekdays]
            for row in daily.itertuples(index=False):
                z[int(row.weekday_num)][int(row.day_num) - 1] = row.tb
                custom[int(row.weekday_num)][int(row.day_num) - 1] = row.day
            mean_tb = float(daily["mean_tb"].iloc[0])
            fig = go.Figure(
                go.Heatmap(
                    x=list(range(1, 32)),
                    y=weekdays,
                    z=z,
                    customdata=custom,
                    zmid=mean_tb,
                    colorscale="RdBu_r",
                    colorbar=dict(title="TB / day", thickness=10, len=0.78),
                    hovertemplate="%{customdata}<br>%{z:.3f} TB<br>Mean: "
                    f"{mean_tb:.3f} TB/day<extra></extra>",
                    xgap=3,
                    ygap=3,
                )
            )
            fig.update_xaxes(title="Day of month", dtick=1, range=[0.5, 31.5])
            fig.update_yaxes(title=None, autorange="reversed")
            chart_style(
                fig,
                height=190,
                title=f"Daily network load | {daily_month}",
                subtitle=f"Calendar heatmap; color centered on SQL monthly mean {mean_tb:.3f} TB/day | {daily_scope}",
            )
            show_chart(
                fig,
                key="detail_daily_load_calendar_heatmap",
                alt=f"Calendar heatmap of daily network load in terabytes for {daily_month}",
                include_month=True,
            )

    with chart_right:
        available_groups = [g for g in ("A", "B") if g in group_dist["label"].values]
        if group_dist.empty or group_dist["mb_per_usage_day"].notna().sum() == 0:
            no_data("Group rates are hidden when a group has fewer than 100 subscribers.")
        else:
            fig = go.Figure()
            for group in available_groups:
                rows = group_dist[
                    (group_dist["label"] == group)
                    & group_dist["mb_per_usage_day"].notna()
                ]
                if rows.empty:
                    continue
                count = int(rows["subscribers"].iloc[0])
                fig.add_trace(
                    go.Box(
                        x=[f"Group {group} (n={count:,})"] * len(rows),
                        y=rows["mb_per_usage_day"],
                        name=f"Group {group}",
                        boxmean=True,
                        boxpoints=False,
                        marker_color=GROUP_COLOURS.get(group, GREY),
                        line_color=GROUP_COLOURS.get(group, GREY),
                        hovertemplate=f"Group {group}<br>%{{y:,.0f}} MB per usage-day<extra>n={count:,}</extra>",
                    )
                )
            fig.update_xaxes(title="Experiment group")
            fig.update_yaxes(title="Subscriber mean (MB per usage-day)", rangemode="tozero")
            chart_style(
                fig,
                height=120,
                title=f"Usage distribution by experiment group | {group_month}",
                subtitle=f"Each box summarizes subscriber-level means | {group_scope}",
            )
            show_chart(
                fig,
                key="detail_group_box_plot",
                alt=f"Subscriber usage-day distribution for groups A and B in {group_month}",
                include_month=True,
            )

        usable_devices = device_dist[device_dist["mb_per_usage_day"].notna()]
        if usable_devices.empty:
            no_data("Device rates are hidden when a category has fewer than 100 subscribers.")
        else:
            fig = go.Figure()
            for device in usable_devices["label"].drop_duplicates().tolist():
                rows = usable_devices[usable_devices["label"] == device]
                count = int(rows["subscribers"].iloc[0])
                fig.add_trace(
                    go.Violin(
                        x=[str(device)] * len(rows),
                        y=rows["mb_per_usage_day"],
                        name=str(device),
                        box=dict(visible=True),
                        meanline=dict(visible=True),
                        points=False,
                        line_color=TEAL,
                        fillcolor="rgba(24,140,140,0.28)",
                        hovertemplate=f"{device}<br>%{{y:,.0f}} MB per usage-day<extra>n={count:,}</extra>",
                    )
                )
            fig.update_xaxes(title="Device category")
            fig.update_yaxes(title="Subscriber mean (MB per usage-day)", rangemode="tozero")
            chart_style(
                fig,
                height=120,
                title=f"Usage distribution by device | {device_month}",
                subtitle=f"Smartphone and feature phone categories | {device_scope}",
            )
            show_chart(
                fig,
                key="detail_device_violin_plot",
                alt=f"Subscriber data usage distribution by device type in {device_month}",
                include_month=True,
            )

with st.sidebar.expander("Metric definitions and caveats"):
    st.markdown(
        "- **Usage-day:** one subscriber with one usage record on one date. It may differ from a calendar day.\n"
        "- **Active subscriber:** at least one usage-day in the selected period.\n"
        "- **Per usage-day:** each subscriber's data divided by their own usage-days, then averaged across subscribers.\n"
        "- **Per calendar day:** each subscriber's data divided by the period's calendar days, then averaged across subscribers.\n"
        "- **Allowance use:** subscriber data averaged across observed months, divided by the plan's monthly allowance. Daily quotas are multiplied by 30.\n"
        "- **TB conversion:** 1 TB = 1,024 x 1,024 MB.\n"
        "- Groups A/B are source labels; the comparison does not establish causation. T3 is a fixed validated result and ignores dashboard filters.\n"
        f"- Rates are suppressed for groups below {MIN_GROUP} subscribers."
    )
st.sidebar.divider()
st.sidebar.image(str(ROOT / "dashboard" / "assets" / "airtel_logo.png"), width=90)
