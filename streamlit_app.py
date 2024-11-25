import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import json

st.set_page_config(layout="wide", page_title="India Petroleum Sales Dashboard")

@st.cache_data
def load_data():
    # Read the Excel file
    df = pd.read_excel('./data.xlsx', sheet_name=0)
    
    # Clean column names - remove any whitespace and special characters
    df.columns = df.columns.str.strip()
    
    # Remove any total or subtotal rows
    df = df[~df['STATE/UT'].str.contains('Region|Total|REGION|ALL INDIA', na=False)]
    
    # Melt the DataFrame to convert years to a single column
    # Exclude any non-year columns
    year_columns = [col for col in df.columns if col != 'STATE/UT']
    df_melted = df.melt(id_vars=['STATE/UT'], 
                       value_vars=year_columns,
                       var_name='Year', 
                       value_name='Sales')
    df_melted['Year'] = df_melted['Year'].str[:4].astype(int)

    
    # Convert Sales to numeric, handling any errors
    df_melted['Sales'] = pd.to_numeric(df_melted['Sales'], errors='coerce')
    
    # Drop any rows with NaN values
    df_melted = df_melted.dropna()
    
    return df_melted

@st.cache_data
def load_geojson():
    try:
        with open('india.geojson', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning("GeoJSON file not found. Map visualization will not be available.")
        return None

st.title("India Petroleum Sales Dashboard")
st.markdown(
    '<small><a href="https://ppac.gov.in/consumption/state-wise" target="_blank">Source: ppac.gov.in</a></small>',
    unsafe_allow_html=True,
)

df = load_data()

# Melt the DataFrame for easier visualization
df_melted = df.melt(id_vars=["STATE/UT"], var_name="Year", value_name="Consumption")
df_melted["Consumption"] = pd.to_numeric(df_melted["Consumption"], errors="coerce")

# Sidebar selectors
st.sidebar.title("Filters")

years = sorted(df['Year'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("Select Year", years)

state_options = sorted(df["STATE/UT"].unique().tolist())
selected_state = st.sidebar.selectbox("Select a State/UT", state_options)

# Top and Bottom K slider
k = st.sidebar.slider("Select K for Top/Bottom K", 1, 10, 5)

# Top K and Bottom K
latest_year = df_melted["Year"].iloc[-1]
top_k = df[df[latest_year].notna()].nlargest(k, latest_year)
bottom_k = df[df[latest_year].notna()].nsmallest(k, latest_year)

# Display Top K and Bottom K
col1, col2 = st.columns(2)

with col1:

    st.subheader(f"Top {k} States by Sales")
    year_data = df[df['Year'] == selected_year]
    top_k = year_data.nlargest(k, 'Sales')
    fig_top = px.bar(top_k, x='STATE/UT', y='Sales',
                    title=f"Top {k} States - {selected_year}")
    fig_top.update_layout(
        xaxis_title="State/UT",
        yaxis_title="Sales (Metric Tonnes)",
        xaxis_tickangle=45
    )
    st.plotly_chart(fig_top, use_container_width=True)

with col2:

    st.subheader(f"Bottom {k} States by Sales")
    year_data = df[df['Year'] == selected_year]
    top_k = year_data.nsmallest(k, 'Sales')
    fig_top = px.bar(top_k, x='STATE/UT', y='Sales',
                    title=f"Top {k} States - {selected_year}")
    fig_top.update_layout(
        xaxis_title="State/UT",
        yaxis_title="Sales (Metric Tonnes)",
        xaxis_tickangle=45
    )
    st.plotly_chart(fig_top, use_container_width=True)


# State-specific analysis
st.subheader(f"Consumption Analysis for {selected_state}")
state_data = df_melted[df_melted["STATE/UT"] == selected_state]

# Summary Statistics
st.subheader("Summary Statistics, (Metric Tonnes)")
col1, col2, col3, col4 = st.columns(4)

current_year_sales = year_data[year_data['STATE/UT'] == selected_state]['Sales'].values[0]
avg_sales = df[df['STATE/UT'] == selected_state]['Sales'].mean()
max_sales = df[df['STATE/UT'] == selected_state]['Sales'].max()
min_sales = df[df['STATE/UT'] == selected_state]['Sales'].min()

col1.metric("Current Year Sales", f"{current_year_sales:,.1f}")
col2.metric("Average Sales", f"{avg_sales:,.1f}")
col3.metric("Maximum Sales", f"{max_sales:,.1f}")
col4.metric("Minimum Sales", f"{min_sales:,.1f}")

# Year-over-Year Growth
st.subheader("Year-over-Year Growth")
df.info(verbose=True)
pivot_df = df.pivot(index='Year', columns='STATE/UT', values='Sales')
growth_df = pivot_df.pct_change() * 100
selected_state_growth = growth_df[selected_state].dropna()

print(selected_state_growth.index)
print(selected_state_growth.values)

fig_growth = px.line(x=selected_state_growth.index, 
                   y=selected_state_growth.values,
                   title=f"Year-over-Year Growth Rate - {selected_state}")
fig_growth.update_layout(
    xaxis_title="Year",
    yaxis_title="Growth Rate (%)",
    showlegend=False
)
st.plotly_chart(fig_growth, use_container_width=True)
