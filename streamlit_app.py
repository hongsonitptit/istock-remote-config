import streamlit as st
from ui.remote_config_page import show_remote_config_page
from ui.report_config_page import show_report_config_page
from ui.pnl_page import show_pnl_page
from ui.trend_page import show_trend_page

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Remote Config',
    page_icon=':bar_chart:',  # This is an emoji shortcode. Could be a URL too.
    layout='wide'
)

st.markdown("""
    <style>
        .block-container {
            padding-left: 20px;
            padding-right: 20px;
            padding-top: 0px;
        }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Declare some useful functions.

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
# '''
# # :earth_americas: GDP dashboard

# Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
# notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
# But it's otherwise a great (and did I mention _free_?) source of data.
# '''

# # Add some spacing
# ''
# # ''

show_report_config_page()

# tab1, tab2, tab3, tab4 = st.tabs(["Report", "Remote Config", "Trend", "PNL"])

# with tab1:
#     show_report_config_page()

# with tab2:
#     show_remote_config_page()

# with tab3:
#     show_trend_page()

# with tab4:
#     show_pnl_page()
