"""Minimal Streamlit dashboard for clinical trial analytics."""

from pathlib import Path

import streamlit as st
import pandas as pd
import duckdb

st.set_page_config(page_title="Clinical Trials Dashboard", layout="wide")

DB_PATH = "data/clinical_trials.duckdb"
SQL_STAGING = Path("sql/staging")
SQL_ANALYTICS = Path("sql/analytics")


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

    conn = get_connection()
    init_views(conn)

    # Metrics row
    col1, col2, col3 = st.columns(3)

    total_studies = conn.execute("SELECT COUNT(*) FROM stg_studies").fetchone()[0]
    total_conditions = conn.execute("SELECT COUNT(DISTINCT condition_name) FROM stg_conditions").fetchone()[0]
    total_countries = conn.execute("SELECT COUNT(DISTINCT country) FROM stg_locations").fetchone()[0]

    col1.metric("Total Studies", f"{total_studies:,}")
    col2.metric("Unique Conditions", f"{total_conditions:,}")
    col3.metric("Countries", f"{total_countries:,}")

    st.divider()

    # Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Trials by Phase")
        df_phase = run_query(conn, SQL_ANALYTICS / "trials_by_phase.sql")
        st.bar_chart(df_phase.set_index("phase")["trial_count"])

    with col_right:
        st.subheader("Top 10 Conditions")
        df_conditions = run_query(conn, SQL_ANALYTICS / "top_conditions.sql").head(10)
        st.bar_chart(df_conditions.set_index("condition_name")["trial_count"])

    st.divider()

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Trials by Country")
        df_country = run_query(conn, SQL_ANALYTICS / "trials_by_country.sql").head(10)
        st.bar_chart(df_country.set_index("country")["trial_count"])

    with col_right2:
        st.subheader("Completion Rate by Intervention Type")
        df_interventions = run_query(conn, SQL_ANALYTICS / "interventions_completion_rate.sql")
        st.bar_chart(df_interventions.set_index("intervention_type")["completion_rate"])


if __name__ == "__main__":
    main()
