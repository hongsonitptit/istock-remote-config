import streamlit as st
from ui.remote_config_page import show_remote_config_page
from ui.report_config_page import show_report_config_page
from ui.pnl_page import show_pnl_page
from ui.trend_page import show_trend_page
from ui.portfolio_page import show_portfolio_page

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='iConfig - Portfolio',
    page_icon=':bar_chart:',
    layout='wide',
    initial_sidebar_state="expanded"
)

# Move CSS to a place where it won't affect top bar/sidebar visibility
st.markdown("""
    <style>
        .block-container {
            padding-left: 50px;
            padding-right: 20px;
            padding-top: 0px;
        }
        
        /* Hide the header bar background and decoration */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
            border-bottom: none;
            visibility: hidden;
        }
        
        /* Ensure the sidebar toggle button remains visible and clickable */
        [data-testid="stHeader"] button {
            visibility: visible;
        }

        /* Hide the status widget (Deploy button etc) */
        [data-testid="stStatusWidget"] {
            display: none !important;
        }
        
        /* Hide the top decoration line */
        [data-testid="stDecoration"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

# Define the navigation
pages = {
    "Reports": [
        st.Page(show_report_config_page, title="Main Report", url_path="report", default=True),
        st.Page(show_trend_page, title="Trend", url_path="trend"),
        st.Page(show_pnl_page, title="PNL", url_path="pnl"),
    ],
    "Tools": [
        st.Page(show_remote_config_page, title="Remote Config", url_path="remote-config"),
        st.Page(show_portfolio_page, title="Portfolio", url_path="portfolio"),
    ]
}

pg = st.navigation(pages)
pg.run()
