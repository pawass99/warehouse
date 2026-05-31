from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "database" / "repository_analytics.db"
TABLE_NAME = "repository_activity"
GITHUB_COMMITS_API = "https://api.github.com/repos/{owner}/{repo}/commits"

PROJECT_SIZE_ORDER = ["Small", "Medium", "Large"]
CHART_COLORS = ["#c96442", "#5d7657", "#30302e", "#d97757", "#87867f", "#b53333"]
CHART_FONT = "Anthropic Sans, Arial, system-ui, -apple-system, sans-serif"
CHART_TITLE_FONT = "Anthropic Serif, Georgia, Times New Roman, serif"
DIMENSION_COLUMNS = {
    "project_size": "Project Size",
    "project_name": "Project Name",
    "team_name": "Team Name",
    "repository_name": "Repository Name",
    "developer_name": "Developer Name",
}


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #f5f4ed;
                --surface: #faf9f5;
                --surface-strong: #ffffff;
                --surface-warm: #e8e6dc;
                --fg: #141413;
                --fg-2: #3d3d3a;
                --muted: #5e5d59;
                --meta: #87867f;
                --border: #f0eee6;
                --border-soft: #e8e6dc;
                --accent: #c96442;
                --accent-2: #d97757;
                --danger: #b53333;
                --success: #5d7657;
                --dark: #30302e;
                --silver: #b0aea5;
                --font-display: "Anthropic Serif", Georgia, "Times New Roman", serif;
                --font-body: "Anthropic Sans", Arial, system-ui, -apple-system, sans-serif;
                --font-mono: "Anthropic Mono", ui-monospace, Menlo, monospace;
                --shadow-ring: 0 0 0 1px var(--border);
                --shadow-raised: rgba(0, 0, 0, 0.05) 0px 4px 24px;
            }

            html, body, [class*="css"] {
                font-family: var(--font-body);
                letter-spacing: 0;
            }

            .stApp {
                background: var(--bg);
                color: var(--fg);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 4rem;
                max-width: 1200px;
            }

            #MainMenu, footer, header {
                visibility: hidden;
            }

            h1, h2, h3 {
                font-family: var(--font-display);
                font-weight: 500;
                letter-spacing: 0;
                color: var(--fg);
                line-height: 1.1;
            }

            h2, h3 {
                font-weight: 500;
            }

            p, label, span {
                letter-spacing: 0;
            }

            [data-testid="stSidebar"] {
                background: var(--surface);
                border-right: 1px solid var(--border-soft);
                box-shadow: 0 0 0 1px rgba(20, 20, 19, 0.02);
            }

            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                font-family: var(--font-display);
                color: var(--fg);
                font-size: 1.45rem;
                font-weight: 500;
                line-height: 1.15;
            }

            [data-testid="stSidebar"] label {
                color: var(--fg-2);
                font-size: 0.88rem;
                font-weight: 500;
            }

            .dashboard-header {
                display: grid;
                grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
                gap: 3rem;
                align-items: end;
                padding: 1.4rem 0 2rem;
                border-bottom: 1px solid var(--border-soft);
                margin-bottom: 1.5rem;
            }

            .dashboard-eyebrow {
                color: var(--meta);
                font-size: 0.64rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 0.75rem;
            }

            .dashboard-title {
                font-family: var(--font-display);
                font-size: clamp(2.5rem, 5vw, 4rem);
                line-height: 1.1;
                font-weight: 500;
                color: var(--fg);
                margin: 0;
                max-width: 760px;
            }

            .dashboard-subtitle {
                max-width: 720px;
                color: var(--muted);
                font-size: 1.18rem;
                line-height: 1.6;
                margin-top: 1rem;
            }

            .dashboard-period {
                color: var(--fg-2);
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 1.25rem;
                min-width: 180px;
                box-shadow: var(--shadow-raised);
            }

            .dashboard-period-label {
                color: var(--meta);
                font-size: 0.64rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .dashboard-period-value {
                color: var(--fg);
                font-size: 1rem;
                font-weight: 500;
                line-height: 1.4;
                margin-top: 0.35rem;
            }

            [data-testid="stMetric"] {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 18px 18px 16px;
                box-shadow: var(--shadow-raised);
            }

            [data-testid="stMetricLabel"] p {
                color: var(--meta);
                font-size: 0.72rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.12px;
            }

            [data-testid="stMetricValue"] {
                color: var(--fg);
                font-family: var(--font-display);
                font-size: 1.9rem;
                font-weight: 500;
                line-height: 1.1;
            }

            [data-testid="stPlotlyChart"] {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 1rem;
                box-shadow: var(--shadow-raised);
            }

            [data-testid="stDataFrame"] {
                border: 1px solid var(--border);
                border-radius: 8px;
                overflow: hidden;
                background: var(--surface);
            }

            div[data-testid="stVerticalBlock"] > [style*="flex-direction: column"] {
                gap: 1.25rem;
            }

            .st-emotion-cache-ue6h4q,
            .st-emotion-cache-16idsys p,
            [data-testid="stCaptionContainer"] {
                color: var(--muted);
                line-height: 1.6;
            }

            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div {
                background: var(--surface-strong);
                border-radius: 12px;
                border-color: var(--border-soft);
                box-shadow: var(--shadow-ring);
            }

            div[data-baseweb="input"] input,
            div[data-baseweb="select"] input,
            div[data-baseweb="select"] span {
                color: var(--fg) !important;
                -webkit-text-fill-color: var(--fg) !important;
            }

            [data-testid="stSidebar"] div[data-baseweb="select"],
            [data-testid="stSidebar"] div[data-baseweb="select"] div,
            [data-testid="stSidebar"] div[data-baseweb="select"] span,
            [data-testid="stSidebar"] div[data-baseweb="select"] input,
            [data-testid="stSidebar"] div[data-baseweb="input"] input {
                color: var(--fg) !important;
                -webkit-text-fill-color: var(--fg) !important;
            }

            [data-testid="stSidebar"] div[data-baseweb="select"] input::placeholder,
            [data-testid="stSidebar"] div[data-baseweb="input"] input::placeholder {
                color: var(--muted) !important;
                -webkit-text-fill-color: var(--muted) !important;
                opacity: 1;
            }

            div[data-baseweb="popover"],
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="menu"] div {
                background: var(--surface-strong) !important;
                color: var(--fg) !important;
                -webkit-text-fill-color: var(--fg) !important;
            }

            span[data-baseweb="tag"] {
                background: var(--surface-warm);
                color: var(--fg) !important;
                border-radius: 999px;
            }

            .stAlert {
                border-radius: 8px;
                background: var(--surface);
                border: 1px solid var(--border-soft);
            }

            hr {
                margin: 2rem 0;
                border-color: var(--border-soft);
            }

            .section-kicker {
                color: var(--meta);
                font-size: 0.64rem;
                font-weight: 500;
                letter-spacing: 0.5px;
                line-height: 1.6;
                text-transform: uppercase;
                margin: 1.4rem 0 0.35rem;
            }

            .section-title {
                font-family: var(--font-display);
                color: var(--fg);
                font-size: clamp(1.65rem, 2.8vw, 2rem);
                font-weight: 500;
                line-height: 1.14;
                margin: 0 0 1rem;
            }

            .dark-note {
                background: var(--fg);
                border: 1px solid var(--dark);
                border-radius: 16px;
                color: var(--silver);
                padding: 1.5rem;
                margin-top: 1.5rem;
                box-shadow: var(--shadow-raised);
            }

            .dark-note strong,
            .dark-note h3 {
                color: var(--surface);
            }

            .dark-note h3 {
                font-family: var(--font-display);
                font-size: 1.6rem;
                font-weight: 500;
                line-height: 1.2;
                margin: 0 0 0.65rem;
            }

            .dark-note p {
                color: var(--silver);
                line-height: 1.6;
                margin: 0;
            }

            .insight-grid {
                display: grid;
                grid-template-columns: 1.15fr 0.85fr;
                gap: 1.25rem;
                margin-top: 1.5rem;
            }

            .surface-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                box-shadow: var(--shadow-raised);
                padding: 1.5rem;
            }

            .surface-card h3 {
                font-family: var(--font-display);
                font-size: 1.6rem;
                font-weight: 500;
                line-height: 1.2;
                margin: 0 0 0.65rem;
            }

            .surface-card p {
                color: var(--muted);
                line-height: 1.6;
                margin: 0;
            }

            .surface-card .small-label,
            .dark-note .small-label {
                display: inline-flex;
                align-items: center;
                width: fit-content;
                padding: 3px 12px;
                border-radius: 999px;
                font-size: 0.64rem;
                font-weight: 500;
                letter-spacing: 0.12px;
                line-height: 1.6;
                text-transform: uppercase;
                margin-bottom: 0.85rem;
            }

            .surface-card .small-label {
                background: rgba(201, 100, 66, 0.12);
                color: var(--accent);
            }

            .dark-note .small-label {
                background: rgba(250, 249, 245, 0.1);
                color: var(--surface);
            }

            .github-panel {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 16px;
                box-shadow: var(--shadow-raised);
                padding: 1.25rem;
                margin: 0.5rem 0 1.25rem;
            }

            .github-card {
                background: var(--surface);
                border: 1px solid var(--border-soft);
                border-radius: 8px;
                box-shadow: 0 0 0 1px var(--border);
                padding: 1rem 1.1rem;
                margin-bottom: 0.75rem;
            }

            .github-card-title {
                color: var(--fg);
                font-family: var(--font-body);
                font-size: 0.98rem;
                font-weight: 500;
                line-height: 1.45;
                margin-bottom: 0.65rem;
            }

            .github-card-meta {
                color: var(--muted);
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem 0.9rem;
                font-size: 0.84rem;
                line-height: 1.5;
            }

            .github-card-meta code {
                background: var(--surface-warm);
                border: 1px solid var(--border-soft);
                border-radius: 6px;
                color: var(--fg);
                font-family: var(--font-mono);
                font-size: 0.8rem;
                padding: 1px 6px;
            }

            .github-card-link {
                color: var(--accent);
                font-weight: 500;
                text-decoration: none;
            }

            .github-card-link:hover {
                color: var(--accent-2);
                text-decoration: none;
            }

            @media (max-width: 900px) {
                .insight-grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 760px) {
                .dashboard-header {
                    grid-template-columns: 1fr;
                    gap: 1.5rem;
                }

                .dashboard-title {
                    font-size: 2.2rem;
                }

                .dashboard-period {
                    margin-top: 1rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_style(figure: Any, height: int = 420) -> Any:
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="#faf9f5",
        plot_bgcolor="#faf9f5",
        font={"family": CHART_FONT, "size": 12, "color": "#141413"},
        title={
            "font": {"family": CHART_TITLE_FONT, "size": 20, "color": "#141413"},
            "x": 0,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top",
            "pad": {"b": 18},
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11, "color": "#141413"},
        },
        margin={"l": 24, "r": 24, "t": 96, "b": 82},
        height=height,
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#e8e6dc",
        tickfont={"size": 11, "color": "#141413"},
        title_font={"size": 12, "color": "#141413"},
    )
    figure.update_yaxes(
        gridcolor="#e8e6dc",
        zeroline=False,
        tickfont={"size": 11, "color": "#141413"},
        title_font={"size": 12, "color": "#141413"},
    )
    figure.update_traces(textfont={"color": "#141413"})
    return figure


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def query_dataframe(query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with connect() as connection:
        return pd.read_sql_query(query, connection, params=params)


def query_scalar_options(column_name: str) -> list[str]:
    query = f"""
        SELECT DISTINCT {column_name}
        FROM {TABLE_NAME}
        WHERE {column_name} IS NOT NULL
        ORDER BY {column_name}
    """
    dataframe = query_dataframe(query)
    values = dataframe[column_name].dropna().astype(str).tolist()

    if column_name == "project_size":
        return [value for value in PROJECT_SIZE_ORDER if value in values]

    return values


def get_date_bounds() -> tuple[Any, Any]:
    dataframe = query_dataframe(f"SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM {TABLE_NAME}")
    min_date = datetime.strptime(dataframe.loc[0, "min_date"], "%Y-%m-%d").date()
    max_date = datetime.strptime(dataframe.loc[0, "max_date"], "%Y-%m-%d").date()
    return min_date, max_date


def build_where_clause(
    start_date: Any,
    end_date: Any,
    selected_filters: dict[str, list[str]],
) -> tuple[str, tuple[Any, ...]]:
    conditions = ["date BETWEEN ? AND ?"]
    params: list[Any] = [start_date.isoformat(), end_date.isoformat()]

    for column_name, selected_values in selected_filters.items():
        if selected_values:
            placeholders = ", ".join(["?"] * len(selected_values))
            conditions.append(f"{column_name} IN ({placeholders})")
            params.extend(selected_values)

    return "WHERE " + " AND ".join(conditions), tuple(params)


def get_kpis(where_clause: str, params: tuple[Any, ...]) -> dict[str, float]:
    query = f"""
        WITH filtered AS (
            SELECT *
            FROM {TABLE_NAME}
            {where_clause}
        ),
        project_metrics AS (
            SELECT
                project_name,
                MAX(developer_count) AS developer_count,
                SUM(commits) AS total_commits,
                SUM(pull_requests) AS total_pull_requests,
                SUM(merge_conflicts) AS total_merge_conflicts,
                SUM(issues_resolved) AS total_issues_resolved,
                SUM(bugs_reported) AS total_bugs_reported,
                SUM(commits + pull_requests + issues_resolved) AS total_activity
            FROM filtered
            GROUP BY project_name
        )
        SELECT
            (SELECT COUNT(DISTINCT project_name) FROM filtered) AS total_projects,
            (SELECT COUNT(DISTINCT developer_name) FROM filtered) AS total_developers,
            COALESCE(SUM(total_commits), 0) AS total_commits,
            COALESCE(SUM(total_pull_requests), 0) AS total_pull_requests,
            COALESCE(SUM(total_merge_conflicts), 0) AS total_merge_conflicts,
            COALESCE(AVG(total_activity * 1.0 / NULLIF(developer_count, 0)), 0)
                AS avg_productivity_per_developer,
            COALESCE(SUM(total_merge_conflicts) * 1.0 / NULLIF(SUM(total_pull_requests), 0), 0)
                AS avg_conflict_rate
        FROM project_metrics
    """
    row = query_dataframe(query, params).iloc[0].to_dict()
    return {key: 0 if pd.isna(value) else value for key, value in row.items()}


def get_project_summary(where_clause: str, params: tuple[Any, ...]) -> pd.DataFrame:
    query = f"""
        WITH filtered AS (
            SELECT *
            FROM {TABLE_NAME}
            {where_clause}
        ),
        project_metrics AS (
            SELECT
                project_name,
                project_size,
                MAX(developer_count) AS developer_count,
                COUNT(DISTINCT month) AS active_months,
                SUM(commits) AS total_commits,
                SUM(pull_requests) AS total_pull_requests,
                SUM(merge_conflicts) AS total_merge_conflicts,
                SUM(issues_resolved) AS total_issues_resolved,
                SUM(bugs_reported) AS total_bugs_reported,
                SUM(commits + pull_requests + issues_resolved) AS total_activity
            FROM filtered
            GROUP BY project_name, project_size
        ),
        scored AS (
            SELECT
                *,
                ROUND(total_activity * 1.0 / NULLIF(developer_count, 0), 2)
                    AS productivity_per_developer,
                ROUND(total_activity * 1.0 / NULLIF(developer_count * active_months, 0), 2)
                    AS monthly_productivity_per_developer,
                ROUND(total_merge_conflicts * 1.0 / NULLIF(total_pull_requests, 0), 4)
                    AS conflict_rate,
                ROUND(total_bugs_reported * 1.0 / NULLIF(total_commits, 0), 4)
                    AS bug_rate
            FROM project_metrics
        )
        SELECT
            project_name,
            project_size,
            developer_count,
            total_commits,
            total_pull_requests,
            total_merge_conflicts,
            total_issues_resolved,
            total_bugs_reported,
            productivity_per_developer,
            conflict_rate,
            bug_rate,
            CASE
                WHEN bug_rate >= 0.22 THEN 'Focus on code quality'
                WHEN developer_count >= 18 AND monthly_productivity_per_developer < 18 THEN 'Evaluate task distribution'
                WHEN monthly_productivity_per_developer < 18 AND conflict_rate < 0.16 THEN 'Consider adding developers'
                WHEN monthly_productivity_per_developer < 18 AND conflict_rate >= 0.16 THEN 'Improve coordination before adding developers'
                WHEN monthly_productivity_per_developer >= 22 AND conflict_rate < 0.14 THEN 'Team size is effective'
                WHEN conflict_rate >= 0.24 THEN 'Reduce coordination bottlenecks'
                ELSE 'Monitor team balance'
            END AS recommendation,
            total_activity
        FROM scored
        ORDER BY productivity_per_developer DESC
    """
    return query_dataframe(query, params)


def get_monthly_trend(where_clause: str, params: tuple[Any, ...]) -> pd.DataFrame:
    query = f"""
        SELECT
            month,
            SUM(commits) AS commits,
            SUM(pull_requests) AS pull_requests,
            SUM(issues_resolved) AS issues_resolved,
            SUM(commits + pull_requests + issues_resolved) AS total_activity
        FROM {TABLE_NAME}
        {where_clause}
        GROUP BY month
        ORDER BY month
    """
    return query_dataframe(query, params)


def get_repository_distribution(where_clause: str, params: tuple[Any, ...]) -> pd.DataFrame:
    query = f"""
        SELECT
            repository_name,
            SUM(commits + pull_requests + issues_resolved) AS total_activity
        FROM {TABLE_NAME}
        {where_clause}
        GROUP BY repository_name
        HAVING total_activity > 0
        ORDER BY total_activity DESC
        LIMIT 12
    """
    return query_dataframe(query, params)


def get_default_github_repo() -> tuple[str, str]:
    owner = os.getenv("GITHUB_OWNER", "pawas").strip()
    repo = os.getenv("GITHUB_REPO", ROOT_DIR.name).strip()
    return owner, repo


def format_github_date(raw_date: str) -> str:
    if not raw_date:
        return "Unknown date"

    try:
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return raw_date

    return parsed_date.strftime("%d %b %Y %H:%M UTC")


def format_rate_limit_reset(reset_timestamp: str | None) -> str:
    if not reset_timestamp:
        return "beberapa saat lagi"

    try:
        reset_date = datetime.fromtimestamp(int(reset_timestamp), tz=timezone.utc)
    except (TypeError, ValueError):
        return "beberapa saat lagi"

    return reset_date.strftime("%d %b %Y %H:%M UTC")


def parse_github_commit(raw_commit: dict[str, Any]) -> dict[str, str]:
    commit_detail = raw_commit.get("commit") or {}
    commit_author = commit_detail.get("author") or {}
    github_author = raw_commit.get("author") or {}
    message = str(commit_detail.get("message") or "(No commit message)").splitlines()[0]

    return {
        "message": message,
        "sha": str(raw_commit.get("sha") or "")[:7],
        "author": str(github_author.get("login") or commit_author.get("name") or "Unknown"),
        "date": format_github_date(str(commit_author.get("date") or "")),
        "url": str(raw_commit.get("html_url") or ""),
    }


@st.cache_data(ttl=60, show_spinner=False)
def fetch_latest_github_commits(
    owner: str,
    repo: str,
    limit: int,
    token_is_available: bool,
) -> dict[str, Any]:
    del token_is_available

    safe_limit = max(1, min(int(limit), 30))
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            GITHUB_COMMITS_API.format(owner=owner, repo=repo),
            headers=headers,
            params={"per_page": safe_limit},
            timeout=10,
        )
    except requests.Timeout:
        return {
            "ok": False,
            "message": "Request ke GitHub timeout. Coba refresh lagi beberapa saat lagi.",
        }
    except requests.RequestException as error:
        return {
            "ok": False,
            "message": f"Gagal menghubungi GitHub API: {error}",
        }

    if response.status_code == 200:
        payload = response.json()
        return {
            "ok": True,
            "commits": [parse_github_commit(item) for item in payload],
            "authenticated": bool(token),
            "remaining": response.headers.get("X-RateLimit-Remaining"),
        }

    if response.status_code == 404:
        return {
            "ok": False,
            "message": (
                f"Repository `{owner}/{repo}` tidak ditemukan. Periksa owner, nama repo, "
                "atau gunakan GITHUB_TOKEN jika repository bersifat private."
            ),
        }

    rate_remaining = response.headers.get("X-RateLimit-Remaining")
    if response.status_code in {403, 429} and rate_remaining == "0":
        reset_time = format_rate_limit_reset(response.headers.get("X-RateLimit-Reset"))
        return {
            "ok": False,
            "message": f"Rate limit GitHub API habis. Coba lagi setelah {reset_time}.",
        }

    try:
        error_payload = response.json()
        error_message = error_payload.get("message", "Tidak ada detail error.")
    except ValueError:
        error_message = response.text[:240] or "Tidak ada detail error."

    return {
        "ok": False,
        "message": f"GitHub API mengembalikan status {response.status_code}: {error_message}",
    }


def render_metric_grid(kpis: dict[str, float]) -> None:
    st.markdown(
        """
        <div class="section-kicker">Decision metrics</div>
        <div class="section-title">Ringkasan kesehatan tim dan repository.</div>
        """,
        unsafe_allow_html=True,
    )
    first_row = st.columns(4)
    second_row = st.columns(3)

    first_row[0].metric("Total Projects", f"{int(kpis['total_projects']):,}")
    first_row[1].metric("Total Developers", f"{int(kpis['total_developers']):,}")
    first_row[2].metric("Total Commits", f"{int(kpis['total_commits']):,}")
    first_row[3].metric("Total Pull Requests", f"{int(kpis['total_pull_requests']):,}")

    second_row[0].metric("Total Merge Conflicts", f"{int(kpis['total_merge_conflicts']):,}")
    second_row[1].metric(
        "Avg Productivity / Developer",
        f"{float(kpis['avg_productivity_per_developer']):,.2f}",
    )
    second_row[2].metric("Avg Conflict Rate", f"{float(kpis['avg_conflict_rate']):.2%}")


def render_commit_card(commit: dict[str, str]) -> None:
    commit_url = escape(commit["url"], quote=True)
    link_html = ""

    if commit_url:
        link_html = (
            f'<a class="github-card-link" href="{commit_url}" '
            'target="_blank" rel="noopener noreferrer">Open commit</a>'
        )

    st.markdown(
        f"""
        <article class="github-card">
            <div class="github-card-title">{escape(commit["message"])}</div>
            <div class="github-card-meta">
                <span><code>{escape(commit["sha"])}</code></span>
                <span>Author: {escape(commit["author"])}</span>
                <span>Date: {escape(commit["date"])}</span>
                {link_html}
            </div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def render_github_commit_activity() -> None:
    default_owner, default_repo = get_default_github_repo()

    st.divider()
    st.markdown(
        """
        <div class="section-kicker">Near real-time activity</div>
        <div class="section-title">Live GitHub Commit Activity</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="github-panel">
            Ambil commit terbaru dari satu repository GitHub. Data ini memakai GitHub REST API
            dan cache 60 detik, jadi sifatnya near real-time refresh, bukan streaming WebSocket.
        </div>
        """,
        unsafe_allow_html=True,
    )

    owner_column, repo_column, limit_column = st.columns((1, 1, 0.75))
    owner = owner_column.text_input("GitHub owner", value=default_owner, key="github_owner")
    repo = repo_column.text_input("Repository name", value=default_repo, key="github_repo")
    commit_limit = limit_column.number_input(
        "Jumlah commit",
        min_value=1,
        max_value=30,
        value=8,
        step=1,
        key="github_commit_limit",
    )

    if st.button("Refresh Commit Data", type="primary"):
        fetch_latest_github_commits.clear()
        st.toast("Cache GitHub commit dibersihkan. Mengambil data terbaru.")

    owner = owner.strip()
    repo = repo.strip()
    if not owner or not repo:
        st.info("Isi GitHub owner dan repository name untuk mengambil commit terbaru.")
        return

    with st.spinner("Mengambil commit terbaru dari GitHub..."):
        result = fetch_latest_github_commits(
            owner,
            repo,
            int(commit_limit),
            bool(os.getenv("GITHUB_TOKEN")),
        )

    if not result["ok"]:
        st.error(result["message"])
        return

    request_mode = "authenticated" if result["authenticated"] else "public unauthenticated"
    remaining = result.get("remaining")
    if remaining is not None:
        st.caption(f"Request mode: {request_mode}. GitHub rate limit remaining: {remaining}.")
    else:
        st.caption(f"Request mode: {request_mode}.")

    commits = result["commits"]
    if not commits:
        st.info("Repository ditemukan, tetapi tidak ada commit yang bisa ditampilkan.")
        return

    for commit in commits:
        render_commit_card(commit)


def main() -> None:
    st.set_page_config(
        page_title="Software Engineering Productivity Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
    )
    inject_custom_css()

    if not DB_PATH.exists():
        st.error("Database belum tersedia.")
        st.code("uv run python scripts/seed_database.py", language="bash")
        st.stop()

    min_date, max_date = get_date_bounds()
    options = {column: query_scalar_options(column) for column in DIMENSION_COLUMNS}

    with st.sidebar:
        st.header("Slice & Dice")
        st.caption("Kosongkan pilihan dimensi untuk memakai semua data.")

        selected_range = st.date_input(
            "Rentang Tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start_date, end_date = selected_range
        else:
            start_date, end_date = min_date, max_date

        selected_filters: dict[str, list[str]] = {}
        for column_name, label in DIMENSION_COLUMNS.items():
            selected_filters[column_name] = st.multiselect(
                label,
                options=options[column_name],
                default=[],
            )

    if start_date > end_date:
        st.warning("Tanggal awal tidak boleh lebih besar dari tanggal akhir.")
        st.stop()

    st.markdown(
        f"""
        <div class="dashboard-header">
            <div>
                <div class="dashboard-eyebrow">Software Engineering Analytics</div>
                <h1 class="dashboard-title">Efektivitas Jumlah Developer</h1>
                <div class="dashboard-subtitle">
                    Analisis produktivitas project berdasarkan ukuran tim, aktivitas repository,
                    merge conflict, issue, dan bug dalam satu tampilan ringkas.
                </div>
            </div>
            <div class="dashboard-period">
                <div class="dashboard-period-label">Periode Analisis</div>
                <div class="dashboard-period-value">{start_date:%d %b %Y} - {end_date:%d %b %Y}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    where_clause, params = build_where_clause(start_date, end_date, selected_filters)
    kpis = get_kpis(where_clause, params)
    project_summary = get_project_summary(where_clause, params)
    monthly_trend = get_monthly_trend(where_clause, params)
    repository_distribution = get_repository_distribution(where_clause, params)

    render_metric_grid(kpis)

    if project_summary.empty:
        st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
        st.stop()

    st.divider()
    st.markdown(
        """
        <div class="section-kicker">Project signals</div>
        <div class="section-title">Produktivitas, ukuran tim, dan distribusi aktivitas.</div>
        """,
        unsafe_allow_html=True,
    )

    left_column, right_column = st.columns((1.1, 1))

    with left_column:
        bar_chart = px.bar(
            project_summary,
            x="project_name",
            y="productivity_per_developer",
            color="project_size",
            color_discrete_sequence=CHART_COLORS,
            category_orders={"project_size": PROJECT_SIZE_ORDER},
            title="Productivity per Developer by Project",
            labels={
                "project_name": "Project",
                "productivity_per_developer": "Productivity per Developer",
                "project_size": "Project Size",
            },
            hover_data=["developer_count", "total_activity", "conflict_rate", "bug_rate"],
        )
        bar_chart.update_layout(xaxis_tickangle=-25, legend_title_text="Size")
        bar_chart.update_traces(marker_line_color="#faf9f5", marker_line_width=1)
        apply_chart_style(bar_chart)
        st.plotly_chart(bar_chart, width="stretch")

    with right_column:
        scatter_plot = px.scatter(
            project_summary,
            x="developer_count",
            y="total_activity",
            size="total_merge_conflicts",
            color="project_size",
            color_discrete_sequence=CHART_COLORS,
            category_orders={"project_size": PROJECT_SIZE_ORDER},
            title="Developer Count vs Total Productivity",
            labels={
                "developer_count": "Developer Count",
                "total_activity": "Total Productivity",
                "project_size": "Project Size",
            },
            hover_name="project_name",
            hover_data=["productivity_per_developer", "conflict_rate", "bug_rate"],
            size_max=34,
        )
        scatter_plot.update_traces(marker={"opacity": 0.82, "line": {"width": 1, "color": "#faf9f5"}})
        apply_chart_style(scatter_plot)
        st.plotly_chart(scatter_plot, width="stretch")

    trend_column, distribution_column = st.columns((1.2, 0.8))

    with trend_column:
        line_chart = px.line(
            monthly_trend,
            x="month",
            y=["commits", "pull_requests", "issues_resolved", "total_activity"],
            markers=True,
            title="Monthly Productivity Trend",
            labels={"month": "Month", "value": "Activity Count", "variable": "Metric"},
            color_discrete_sequence=CHART_COLORS,
        )
        line_chart.update_layout(legend_title_text="Metric", xaxis_tickangle=-25)
        apply_chart_style(line_chart)
        st.plotly_chart(line_chart, width="stretch")

    with distribution_column:
        donut_chart = px.pie(
            repository_distribution,
            names="repository_name",
            values="total_activity",
            hole=0.48,
            title="Repository Activity Distribution",
            color_discrete_sequence=CHART_COLORS,
        )
        donut_chart.update_traces(
            textposition="outside",
            textinfo="percent+label",
            textfont={"color": "#141413"},
            outsidetextfont={"color": "#141413"},
            marker={"line": {"color": "#faf9f5", "width": 1}},
        )
        apply_chart_style(donut_chart, height=450)
        st.plotly_chart(donut_chart, width="stretch")

    st.markdown(
        """
        <div class="section-kicker">Effectiveness table</div>
        <div class="section-title">Rekomendasi tindakan per project.</div>
        """,
        unsafe_allow_html=True,
    )
    display_columns = [
        "project_name",
        "project_size",
        "developer_count",
        "total_commits",
        "total_pull_requests",
        "total_merge_conflicts",
        "total_issues_resolved",
        "total_bugs_reported",
        "productivity_per_developer",
        "conflict_rate",
        "bug_rate",
        "recommendation",
    ]
    st.dataframe(
        project_summary[display_columns],
        width="stretch",
        hide_index=True,
        column_config={
            "project_name": "Project",
            "project_size": "Size",
            "developer_count": st.column_config.NumberColumn("Developers", format="%d"),
            "total_commits": st.column_config.NumberColumn("Commits", format="%d"),
            "total_pull_requests": st.column_config.NumberColumn("Pull Requests", format="%d"),
            "total_merge_conflicts": st.column_config.NumberColumn("Merge Conflicts", format="%d"),
            "total_issues_resolved": st.column_config.NumberColumn("Issues Resolved", format="%d"),
            "total_bugs_reported": st.column_config.NumberColumn("Bugs Reported", format="%d"),
            "productivity_per_developer": st.column_config.NumberColumn(
                "Productivity / Developer", format="%.2f"
            ),
            "conflict_rate": st.column_config.NumberColumn("Conflict Rate", format="%.2%"),
            "bug_rate": st.column_config.NumberColumn("Bug Rate", format="%.2%"),
            "recommendation": "Recommendation",
        },
    )

    render_github_commit_activity()

    st.markdown(
        """
        <div class="insight-grid">
            <section class="dark-note">
                <div class="small-label">Manager context</div>
                <h3>Cara membaca dashboard</h3>
                <p>
                    Dashboard ini membantu engineering manager menilai apakah jumlah developer
                    pada sebuah project sudah efektif. <strong>Productivity per developer</strong>
                    dihitung dari commits, pull requests, dan issues resolved, lalu dibagi jumlah
                    developer. <strong>Conflict rate</strong> menunjukkan rasio merge conflicts
                    terhadap pull requests, sedangkan <strong>bug rate</strong> menunjukkan sinyal
                    kualitas kode dari bugs reported terhadap commits.
                </p>
            </section>
            <section class="surface-card">
                <div class="small-label">GitHub API note</div>
                <h3>Token bersifat opsional</h3>
                <p>
                    Untuk public repository, dashboard tetap bisa mengambil commit tanpa token.
                    Jika repository private atau ingin rate limit lebih longgar, set environment
                    variable <strong>GITHUB_TOKEN</strong> sebelum menjalankan Streamlit.
                </p>
            </section>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
