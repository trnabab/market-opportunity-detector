"""
Streamlit dashboard for Market Opportunity Detector.

Run with: cd src && streamlit run dashboard/app.py
"""

import sys
import os

if __name__ == "__main__" or "streamlit" in sys.modules:
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

import streamlit as st
import pandas as pd
from api.queries import get_opportunities, get_keyword_history, get_categories

st.set_page_config(
    page_title="Market Opportunity Detector",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS for modern look ----
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1f77b4;
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.75rem;
        color: white;
    }
    .stMetric label {
        color: rgba(255,255,255,0.8) !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# ---- Header ----
st.title("📈 Market Opportunity Detector")
st.caption("Discover trending products with low competition — powered by eBay + Google Trends")

# ---- Sidebar: filters ----
st.sidebar.header("🎛️ Filters")

categories = get_categories()
category_names = ["All Categories"] + [c["name"] for c in categories]
selected_category = st.sidebar.selectbox("Category", category_names)

limit = st.sidebar.slider("Number of opportunities", 5, 100, 20)
min_score = st.sidebar.slider("Minimum score", 0, 100, 0)

st.sidebar.markdown("---")
st.sidebar.header("📂 Tracked Categories")
for c in categories:
    st.sidebar.markdown(f"• **{c['name']}** _{c['seed']}_")

# ---- Load data ----
opportunities = get_opportunities(limit=limit)

if not opportunities:
    st.info("No opportunities yet. Run the weekly collection script to populate data.")
    st.stop()

df = pd.DataFrame(opportunities)
df = df[df["score"] >= min_score]
df["score_date"] = pd.to_datetime(df["score_date"])

# ---- KPI Metrics ----
st.markdown("### 📊 Summary")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric("Total Keywords", len(df))
with col_m2:
    avg_score = df["score"].mean() if len(df) > 0 else 0
    st.metric("Avg Score", f"{avg_score:.1f}")
with col_m3:
    top_score = df["score"].max() if len(df) > 0 else 0
    st.metric("Top Score", f"{top_score:.1f}")
with col_m4:
    date_range = df["score_date"].max() - df["score_date"].min() if len(df) > 1 else pd.Timedelta(0)
    st.metric("Data Span", f"{date_range.days} days")

st.markdown("---")

# ---- Top Opportunities Table ----
st.markdown("### 🏆 Top Opportunities")
display_df = df.copy()
display_df["score_date"] = display_df["score_date"].dt.strftime("%Y-%m-%d")
display_df = display_df.rename(columns={
    "keyword": "Keyword",
    "score": "Score",
    "score_date": "Date",
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score",
            format="%.1f",
            min_value=0,
            max_value=100,
        ),
    },
)

st.markdown("---")

# ---- Keyword Analysis Section ----
st.markdown("### 🔍 Keyword Analysis")
unique_keywords = list(dict.fromkeys([o["keyword"] for o in opportunities]))
keyword = st.selectbox("Select a keyword to explore", unique_keywords)

if keyword:
    history = get_keyword_history(keyword)
    if not history:
        st.warning(f"No history yet for **{keyword}**.")
    else:
        history_df = pd.DataFrame(history)
        history_df["date"] = pd.to_datetime(history_df["date"])

        agg_df = (
            history_df.groupby("date", as_index=False)
            .agg({
                "trend_momentum": "mean",
                "competition_density": "mean",
                "avg_price": "mean",
                "listing_count": "sum",
                "unique_sellers": "sum",
            })
            .sort_values("date")
            .reset_index(drop=True)
        )

        latest = history_df.sort_values("date", ascending=False).iloc[0]

        st.markdown(f"#### Stats for **{keyword}**")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            val = latest.get("trend_momentum")
            st.metric("Trend Momentum", f"{val:.3f}" if val else "—")
        with col_s2:
            val = latest.get("competition_density")
            st.metric("Competition Density", f"{val:.4f}" if val else "—")
        with col_s3:
            val = latest.get("avg_price")
            st.metric("Avg Price", f"${val:.2f}" if val else "—")
        with col_s4:
            val = latest.get("listing_count")
            st.metric("Listings", val if val else "—")

        st.markdown("---")

        # ---- Charts row 1: Trend Momentum & Google Trends ----
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 📈 Trend Momentum Over Time")
            if len(agg_df) < 2:
                if len(agg_df) == 1:
                    st.info(f"Single snapshot: {agg_df['trend_momentum'].iloc[0]:.3f}")
                else:
                    st.info("No trend momentum data yet.")
            else:
                st.line_chart(agg_df.set_index("date")[["trend_momentum"]], use_container_width=True)

        with col2:
            st.markdown("##### 🌐 Latest 12-Week Google Trends")
            trend_values = latest.get("trend_values") or []
            if trend_values:
                weeks_df = pd.DataFrame({
                    "Week": range(1, len(trend_values) + 1),
                    "Interest": trend_values,
                })
                st.area_chart(weeks_df.set_index("Week"), use_container_width=True)
            else:
                st.info("No Google Trends data for this snapshot.")

        # ---- Charts row 2: Competition & Prices ----
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("##### 🏪 Competition Density Over Time")
            if len(agg_df) < 2:
                if len(agg_df) == 1 and agg_df["competition_density"].iloc[0]:
                    st.info(f"Single snapshot: {agg_df['competition_density'].iloc[0]:.4f}")
                else:
                    st.info("Not enough data yet.")
            else:
                st.line_chart(agg_df.set_index("date")[["competition_density"]], use_container_width=True)

        with col4:
            st.markdown("##### 💰 Average Price Over Time")
            if len(agg_df) < 2:
                if len(agg_df) == 1 and agg_df["avg_price"].iloc[0]:
                    st.info(f"Single snapshot: ${agg_df['avg_price'].iloc[0]:.2f}")
                else:
                    st.info("Not enough data yet.")
            else:
                st.line_chart(agg_df.set_index("date")[["avg_price"]], use_container_width=True)

# ---- Footer ----
st.markdown("---")
st.caption("Built with Streamlit • Data from eBay API + Google Trends")
