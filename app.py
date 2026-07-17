import streamlit as st
import pandas as pd
import time
from datetime import datetime
from io import BytesIO
from ingestion import ingest_raw_news
from scoring import apply_source_credibility_filter
from cleaning import analyze_duplicates
from config import CATEGORY_KEYWORDS

# Page layout & styling definitions
st.set_page_config(page_title="Indian FMCG M&A Intelligence", page_icon="🇮🇳", layout="wide")

# Custom Styles: Shimmer/Skeleton Animation, Cards, and Badges
st.markdown("""
    <style>
    /* Card Styles */
    .news-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        border-left: 5px solid #0052cc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .source-tag { font-size: 0.8rem; color: #0052cc; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .date-tag { font-size: 0.8rem; color: #718096; font-weight: 500; }
    .category-badge {
        font-size: 0.75rem; background-color: #ebf8ff; color: #2b6cb0;
        padding: 4px 10px; border-radius: 9999px; font-weight: 600; margin-bottom: 12px; display: inline-block;
    }
    
    /* Shimmer Skeleton Loader Style */
    @keyframes shimmer {
        0% { background-position: -468px 0; }
        100% { background-position: 468px 0; }
    }
    .skeleton-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        border-left: 5px solid #cbd5e0;
    }
    .skeleton-line {
        height: 14px;
        margin-bottom: 10px;
        background: #f6f7f8;
        background-image: linear-gradient(to right, #f6f7f8 0%, #edeef1 20%, #f6f7f8 40%, #f6f7f8 100%);
        background-repeat: no-repeat;
        background-size: 800px 104px;
        display: inline-block;
        position: relative;
        animation: shimmer 1.2s infinite linear;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to render Skeleton UI placeholders
def display_shimmer_cards():
    for _ in range(3):
        st.markdown("""
        <div class="skeleton-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <div class="skeleton-line" style="width: 25%; height: 16px;"></div>
                <div class="skeleton-line" style="width: 15%; height: 16px;"></div>
            </div>
            <div class="skeleton-line" style="width: 15%; height: 20px; border-radius: 12px; margin-bottom: 15px;"></div>
            <div class="skeleton-line" style="width: 90%; height: 22px; margin-bottom: 15px;"></div>
            <div class="skeleton-line" style="width: 100%; height: 14px;"></div>
            <div class="skeleton-line" style="width: 60%; height: 14px;"></div>
        </div>
        """, unsafe_allow_html=True)

# Helper function to clean and export dataframe as CSV
@st.cache_data
def convert_df_to_csv(df):
    export_df = df[df["is_duplicate"] == False].copy()
    cols_to_keep = ["title", "description", "url", "source", "published_date", "category"]
    available_cols = [col for col in cols_to_keep if col in export_df.columns]
    
    export_df = export_df[available_cols]
    if "published_date" in export_df.columns:
        export_df["published_date"] = export_df["published_date"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "Date Unavailable"
        )
    return export_df.to_csv(index=False).encode('utf-8')

# Helper function to clean and export dataframe as Excel
@st.cache_data
def convert_df_to_excel(df):
    export_df = df[df["is_duplicate"] == False].copy()
    cols_to_keep = ["title", "description", "url", "source", "published_date", "category"]
    available_cols = [col for col in cols_to_keep if col in export_df.columns]
    
    export_df = export_df[available_cols]
    if "published_date" in export_df.columns:
        export_df["published_date"] = export_df["published_date"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "Date Unavailable"
        )
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name='FMCG Intelligence')
    return output.getvalue()

# Sequential Pipeline Orchestration with UI feedback
def execute_agent_pipeline():
    # Setup interactive step visualizer container
    status_box = st.empty()
    shimmer_box = st.empty()
    
    with status_box.container():
        st.info("🔄 Initialize FMCG Agent...")
        
    with shimmer_box:
        display_shimmer_cards()

    # Step 1: Data Gathering (Ingestion)
    status_box.info("📥 Step 1/3: Scraping regional M&A feeds & corporate registers...")
    time.sleep(0.5)  # Visual pacing
    raw_df = ingest_raw_news()
    
    if raw_df.empty:
        status_box.empty()
        shimmer_box.empty()
        return pd.DataFrame()

    # Step 2: Quality Assessment (Scoring)
    status_box.info("🛡️ Step 2/3: Filtering unknown domains & ranking source authority...")
    time.sleep(0.5)
    filtered_df = apply_source_credibility_filter(raw_df, filter_strict=True)
    
    if filtered_df.empty:
        status_box.empty()
        shimmer_box.empty()
        return pd.DataFrame()

    # Step 3: Vector Embeddings Deduplication (Cleaning)
    status_box.info("🤖 Step 3/3: Running MiniLM transformer semantic vector deduplication...")
    time.sleep(0.5)
    processed_df = analyze_duplicates(filtered_df, threshold=0.75)
    
    # Sort so high authority is on top
    processed_df["published_date"] = pd.to_datetime(processed_df["published_date"], errors="coerce")
    processed_df.sort_values(by=["credibility_score", "published_date"], ascending=[True, False], inplace=True)
    
    # Clean up UI loader elements
    status_box.empty()
    shimmer_box.empty()
    
    return processed_df

@st.cache_data(show_spinner=False)
def fetch_and_process_data():
    return execute_agent_pipeline()


# --- Execution Phase ---
try:
    df_display = fetch_and_process_data()
except Exception as e:
    st.error(f"An error occurred: {e}")
    df_display = pd.DataFrame()

# Layout construction: Sidebar setup
with st.sidebar:
    st.header("Pipeline Controls")
    if st.button("Refresh / Fetch Fresh News", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    if not df_display.empty:
        st.markdown("---")
        st.subheader("📥 Export Options")
        
        # Excel Download Button
        excel_data = convert_df_to_excel(df_display)
        st.download_button(
            label="📁 Download Excel (.xlsx)",
            data=excel_data,
            file_name=f"fmcg_intelligence_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # CSV Download Button
        csv_data = convert_df_to_csv(df_display)
        st.download_button(
            label="📄 Download CSV (.csv)",
            data=csv_data,
            file_name=f"fmcg_intelligence_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Layout construction: Main Page layout
st.title("🇮🇳 Indian FMCG Intelligence Newsletter")
st.subheader("Category-Wise M&A, Funding, and Investment Activity")

if df_display.empty:
    st.warning("No FMCG deal-related news found today.")
else:
    # Create categories tabs based on config definitions
    tabs_list = ["All News"] + list(CATEGORY_KEYWORDS.keys())
    tabs = st.tabs(tabs_list)

    # Build each tab with the processed entries
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0:
                # Filter down to clean instances
                tab_df = df_display[df_display["is_duplicate"] == False]
            else:
                tab_df = df_display[(df_display["category"] == tabs_list[i]) & (df_display["is_duplicate"] == False)]
            
            if tab_df.empty:
                st.info(f"No recent intelligence found for {tabs_list[i]} in the last 24 hours.")
            else:
                for index, row in tab_df.iterrows():
                    pub_date = row['published_date']
                    formatted_date = pub_date.strftime("%d %B %Y | %I:%M %p") if pd.notna(pub_date) else "Date Unavailable"

                    # HTML Newsletter Layout Card
                    st.markdown(f"""
                    <div class="news-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="source-tag">{row['source']}</span>
                            <span class="date-tag">📅 {formatted_date}</span>
                        </div>
                        <span class="category-badge">{row['category']}</span>
                        <h3 style="margin-top: 5px; margin-bottom: 10px; color: #1E1E1E;">{row['title']}</h3>
                        <p style="color: #4F4F4F; font-size: 0.95rem; line-height: 1.5; margin-bottom: 15px;">{row['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.link_button("🔗 Read Original Article", row['url'])
                    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)