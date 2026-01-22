"""Minimal Streamlit dashboard for clinical trial analytics."""

from pathlib import Path

import streamlit as st
import pandas as pd
import duckdb
import altair as alt

st.set_page_config(page_title="Clinical Trials Dashboard", layout="wide")

DB_PATH = "data/clinical_trials.duckdb"
SQL_STAGING = Path("sql/staging")
SQL_ANALYTICS = Path("sql/analytics")

# Consistent color
CHART_COLOR = "#4C78A8"

# Clinical trial phase order (domain knowledge)
PHASE_ORDER = ["PHASE1", "PHASE2", "PHASE3", "PHASE4", "Unknown"]


def normalize_phase(phase: str | None) -> str:
    """Normalize phase values, treating NA/null as Unknown."""
    if phase is None or phase == "NA" or phase == "":
        return "Unknown"
    return phase


@st.cache_resource
def get_connection():
    """Get cached database connection."""
    if not Path(DB_PATH).exists():
        st.error(f"Database not found: {DB_PATH}")
        st.info("Run `make ingest` first to load data.")
        st.stop()
    return duckdb.connect(DB_PATH)


def init_views(conn):
    """Initialize staging views."""
    for sql_file in sorted(SQL_STAGING.glob("*.sql")):
        conn.execute(sql_file.read_text())


def run_query(conn, sql_file: Path) -> pd.DataFrame:
    """Run an analytics query and return DataFrame."""
    query = sql_file.read_text()
    return conn.execute(query).df()


def main():
    st.title("Clinical Trials Dashboard")
    st.caption("Data sourced from ClinicalTrials.gov API")

    conn = get_connection()
    init_views(conn)

    # --- Metrics ---
    st.header("Overview")

    total_studies = conn.execute("SELECT COUNT(*) FROM stg_studies").fetchone()[0]
    total_conditions = conn.execute("SELECT COUNT(DISTINCT condition_name) FROM stg_conditions").fetchone()[0]
    total_countries = conn.execute("SELECT COUNT(DISTINCT country) FROM stg_locations").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM stg_studies WHERE overall_status = 'COMPLETED'").fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Studies", f"{total_studies:,}")
    with col2:
        st.metric("Completed", f"{completed:,}")
        if total_studies > 0:
            st.caption(f"{completed / total_studies * 100:.0f}% of total")
    with col3:
        st.metric("Conditions", f"{total_conditions:,}")
    with col4:
        st.metric("Countries", f"{total_countries:,}")

    st.divider()

    # --- Row 1: Phase and Interventions ---
    st.header("Study Characteristics")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Trials by Phase")
        st.caption("Count of studies grouped by reported trial phase")

        df_phase = run_query(conn, SQL_ANALYTICS / "trials_by_phase.sql")
        df_phase["phase"] = df_phase["phase"].apply(normalize_phase)
        df_phase = df_phase.groupby("phase", as_index=False)["trial_count"].sum()

        # Sort by clinical phase order
        df_phase["phase_order"] = df_phase["phase"].apply(
            lambda x: PHASE_ORDER.index(x) if x in PHASE_ORDER else len(PHASE_ORDER)
        )
        df_phase = df_phase.sort_values("phase_order")

        chart_phase = (
            alt.Chart(df_phase)
            .mark_bar(color=CHART_COLOR)
            .encode(
                x=alt.X("trial_count:Q", title="Number of Trials"),
                y=alt.Y("phase:N", sort=list(df_phase["phase"]), title="Phase"),
            )
            .properties(height=300)
        )
        st.altair_chart(chart_phase, width="stretch")
        st.caption("*Studies without phase information are grouped as 'Unknown'*")

    with col_right:
        st.subheader("Completion Rate by Intervention")
        st.caption("Percentage of completed studies per intervention type")

        df_interventions = run_query(conn, SQL_ANALYTICS / "interventions_completion_rate.sql")
        df_interventions = df_interventions.sort_values("completion_rate", ascending=False).head(10)

        chart_interventions = (
            alt.Chart(df_interventions)
            .mark_bar(color=CHART_COLOR)
            .encode(
                x=alt.X("completion_rate:Q", title="Completion Rate (%)", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("intervention_type:N", sort="-x", title="Intervention Type"),
            )
            .properties(height=300)
        )
        st.altair_chart(chart_interventions, width="stretch")

    st.divider()

    # --- Row 2: Conditions and Geography ---
    st.header("Conditions & Geography")

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Top 10 Conditions")
        st.caption("Most frequently studied conditions across all trials")

        df_conditions = run_query(conn, SQL_ANALYTICS / "top_conditions.sql").head(10)

        chart_conditions = (
            alt.Chart(df_conditions)
            .mark_bar(color=CHART_COLOR)
            .encode(
                x=alt.X("trial_count:Q", title="Number of Trials"),
                y=alt.Y("condition_name:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300)),
            )
            .properties(height=350)
        )
        st.altair_chart(chart_conditions, width="stretch")

    with col_right2:
        st.subheader("Top 10 Countries")
        st.caption("Countries with the highest number of trial locations")

        df_country = run_query(conn, SQL_ANALYTICS / "trials_by_country.sql").head(10)

        chart_country = (
            alt.Chart(df_country)
            .mark_bar(color=CHART_COLOR)
            .encode(
                x=alt.X("trial_count:Q", title="Number of Trials"),
                y=alt.Y("country:N", sort="-x", title=None),
            )
            .properties(height=350)
        )
        st.altair_chart(chart_country, width="stretch")

    st.divider()

    # --- Row 3: Duration ---
    st.header("Study Duration")
    st.caption("Average duration in months from start to primary completion date")

    df_duration = run_query(conn, SQL_ANALYTICS / "study_duration.sql")
    df_duration = df_duration[df_duration["avg_duration_months"].notna()]
    df_duration["phase"] = df_duration["phase"].apply(normalize_phase)
    df_duration = df_duration.sort_values("avg_duration_months", ascending=False).head(10)

    if not df_duration.empty:
        df_duration["label"] = df_duration["study_type"] + " / " + df_duration["phase"]

        chart_duration = (
            alt.Chart(df_duration)
            .mark_bar(color=CHART_COLOR)
            .encode(
                x=alt.X("avg_duration_months:Q", title="Average Duration (months)"),
                y=alt.Y("label:N", sort="-x", title=None),
            )
            .properties(height=300, padding={"bottom": 20})
        )
        st.altair_chart(chart_duration, width="stretch")
    else:
        st.info("No duration data available.")


if __name__ == "__main__":
    main()
