import streamlit as st
import pandas as pd
import pandas as pd
from redis_utils import set_remote_config
from datetime import datetime
from redis_utils import get_all_remote_config

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Remote Config',
    page_icon=':bar_chart:',  # This is an emoji shortcode. Could be a URL too.
    layout='wide'
)

@st.dialog("Update remote config")
def show_update_remove_config_dialog(key: str):
    data = original_data[key]
    group = data.get('group', '')
    value = data.get('value', '')
    note = data.get('note', '')
    st.write(f"Update for {key}")
    new_value = st.text_area("Value", value=value, key="new_value")
    new_note = st.text_area("Note", value=note, key="new_note")
    new_group = st.text_input("Group", value=group, key="new_group")
    if st.button("Update"):
        original_data[key]['group'] = new_group
        original_data[key]['value'] = new_value
        original_data[key]['note'] = new_note
        set_remote_config(original_data)
        st.success("Dữ liệu đã được lưu thành công!")
        st.rerun()  # Refresh the app to show updated data



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

original_data = get_all_remote_config()

table_data = []
for key, value in original_data.items():
    table_data.append(value)

df = pd.DataFrame(table_data, columns=['group', 'name', 'value', 'note'])
df = df.drop('group', axis=1)

keys = original_data.keys()

selected_key = st.selectbox(
    "Select key",
    original_data.keys(),
)

if st.button("Update"):
    show_update_remove_config_dialog(selected_key)

st.dataframe(df,
                # Set max height to 800px to prevent excessively tall tables
            height=min(35 * len(df) + 35, 800))
