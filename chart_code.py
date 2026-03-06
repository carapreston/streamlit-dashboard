import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Global Food & Wealth", layout="wide")

# LOAD DATA WITH ERROR HANDLING
@st.cache_data
def load_data():
    try:
        path = r"C:\Users\carac\Documents\DataVisAssignment\calories_gdp_population.csv"
        data = pd.read_csv(path)
        
        # clean column names (removes hidden spaces)
        data.columns = data.columns.str.strip()
        
        # drop missing values
        data = data.dropna(subset=['Population', 'GDP', 'CalorieSupply', 'Region'])   
        data['Year'] = data['Year'].astype(int)
        
        # remove any rows where entity or region is 'World'
        data = data[data['Entity'] != 'World']
        data = data[data['Region'] != 'World']
        
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

# THE APP LOGIC
if df is not None:
    st.title("Wealth vs. Calorie Supply (1961-2022)")

    with st.expander("How to read this dashboard"):
        st.write("""
            * **The Bubble Size** represents total population.
            * **The X-Axis (GDP)** is Logarithmic. This means the distance between €1,000 and €10,000 is the same as €10,000 and €100,000, allowing us to see emerging and wealthy nations on one scale.
            * **The Slope Line** at the bottom measures 'Nutritional Efficiency'; how fast a country turns money into food.
        """)
    
    # sidebar filters
    st.sidebar.header("Filter Controls")
    
    # region selection
    all_regions = sorted(df['Region'].unique().tolist())
    selected_regions = st.sidebar.multiselect("Select Regions", all_regions, default=all_regions)

    # filter the data based on sidebar
    filtered_df = df[df['Region'].isin(selected_regions)]
    
    # country Selection for detailed view
    all_countries = sorted(filtered_df['Entity'].unique().tolist())
    target_country = st.sidebar.selectbox("Select Country for Detail View:", all_countries)

    # TABS FOR DIFFERENT VIEWS
    tab1, tab2 = st.tabs(["Global Overview", "Regional Comparison"])

    with tab1:
        st.subheader("Global Wealth & Nutrition Landscape")
        # main big bubble chart
        fig_global = px.scatter(
            filtered_df,
            x="GDP",
            y="CalorieSupply",
            animation_frame="Year",
            animation_group="Entity",
            size="Population",
            color="Region",
            hover_name="Entity",
            log_x=True, 
            size_max=60,
            range_x=[df['GDP'].min() * 0.9, df['GDP'].max() * 1.1],
            range_y=[df['CalorieSupply'].min() - 500, df['CalorieSupply'].max() + 200],
            template="plotly_white",
            labels={"CalorieSupply": "Calories per Day", "GDP": "GDP per Capita (€)"}
        )

        fig_global.update_xaxes(
            tickprefix="€", 
            tickformat=",", 
            dtick="log",
            type="log"
        )

        fig_global.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 200
        fig_global.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 100
        
        st.plotly_chart(fig_global, use_container_width=True)

    with tab2:
        st.subheader("Regional Trends (Small Multiples)")
        # small multiples chart
        fig_facet = px.scatter(
            filtered_df,
            x="GDP",
            y="CalorieSupply",
            animation_frame="Year",
            animation_group="Entity",
            size="Population",
            color="Region",
            hover_name="Entity",
            facet_col="Region",       
            facet_col_wrap=3,          
            log_x=True, 
            size_max=30,               
            range_x=[df['GDP'].min() * 0.9, df['GDP'].max() * 1.1],
            range_y=[1000, 4500],
            template="plotly_white",
            labels={"CalorieSupply": "kcal/day", "GDP": "GDP (€)"}
        )

        # clean up titles 
        fig_facet.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        # formatting for euro and log scale
        fig_facet.update_xaxes(tickprefix="€",
                               tickformat=",",
                               type="log",
                               nticks=3,
                               ticksuffix="  ")

#       # positioning the title:
        # target xaxis2 for the bottom-middle chart in this 3-column setup.
        for axis_name in fig_facet.layout:
            if axis_name.startswith('xaxis'):
                if axis_name == 'xaxis2': # this gets the bottom-middle slot
                    fig_facet.layout[axis_name].title = {
                        "text": "GDP per Capita (€)",
                        "standoff": 20, # increases the distance from numbers
                        "font": {"size": 14}
                    }
                else:
                    fig_facet.layout[axis_name].title.text = ""
        
        # match the animation speed to the main chart
        if fig_facet.layout.updatemenus:
            fig_facet.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 200
            fig_facet.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 100

        fig_facet.update_layout(showlegend=False)
        st.plotly_chart(fig_facet, use_container_width=True)




    # INDIVIDUAL COUNTRY LINE GRAPH 
    st.divider()

    country_df = df[df['Entity'] == target_country]
    
    # dynamic caption to give a guide
    if not country_df.empty:
        start_yr = int(country_df['Year'].min())
        end_yr = int(country_df['Year'].max())
        
        st.subheader(f"Detailed Trend for {target_country}")
        st.caption(f"Showing available data from {start_yr} to {end_yr}")
    
    # base line for calories
    fig_detail = px.line(country_df, x="Year", y="CalorieSupply", 
                         title=f"Trend Analysis: {target_country}",
                         labels={"CalorieSupply": "Daily kcal"})

    # add GDP to the second axis
    fig_detail.add_scatter(x=country_df["Year"], y=country_df["GDP"], 
                           name="GDP per Capita", mode="lines", yaxis="y2",
                           line=dict(color='green', width=3)) # Green for money
    
    fig_detail.update_layout(
        # primary axis
        yaxis=dict(
            title="Daily Calories (kcal)", 
            showgrid=False
        ),
        # secondary axis 
        yaxis2=dict(
            title="GDP per Capita (€)", 
            overlaying="y", 
            side="right", 
            tickprefix="€", 
            showgrid=False 
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white"
    )
    
    st.plotly_chart(fig_detail, use_container_width=True)

    # insight note
    st.info("**Observation:** When the green (GDP) and blue (Calories) lines move in parallel, it indicates a high dependency on economic growth for food security. A widening gap or 'flattening' blue line suggests the country has reached nutritional saturation.")

    # CALCULATING SLOPE (Growth Efficiency)
    st.divider()
    st.subheader(f"Growth Efficiency: {target_country}")

    if len(country_df) > 1:
        import numpy as np
        
        # slope = how many calories are added for every 1 Euro of GDP
        slope, intercept = np.polyfit(country_df['GDP'], country_df['CalorieSupply'], 1)
        
        # "Calories per €1,000" to make it easy to read
        efficiency = slope * 1000
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### The 'Wealth-to-Food' Ratio")
            st.metric("Efficiency Score", f"{efficiency:.2f} kcal", help="Calories added per €1,000 of GDP growth")
            
            if efficiency > 50:
                st.success(f"**Rapid Converter:** {target_country} is very efficient at turning wealth into food availability.")
            elif efficiency > 10:
                st.info(f"**Moderate Converter:** {target_country} shows a steady link between wealth and diet.")
            else:
                st.warning(f"**Saturated/Flat:** In {target_country}, wealth growth has almost no effect on calorie supply.")

        with col2:
            # simple scatter of the logic
            fig_slope = px.scatter(country_df, x="GDP", y="CalorieSupply", 
                                   trendline="ols", # yhis is the slope line
                                   trendline_color_override="red",
                                   title=f"The Slope of Progress: {target_country}")
            st.plotly_chart(fig_slope, use_container_width=True)
            
        st.write(f"**Interpretation:** For every **€1,000** this country's GDP grows, they gain roughly **{efficiency:.1f} calories** per person.")

    # CALCULATING CORRELATION
    st.divider()
    st.subheader(f"Statistical Relationship: {target_country}")

    if len(country_df) > 1:
        # calculate overall pearson correlation
        correlation = country_df['GDP'].corr(country_df['CalorieSupply'])
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### Summary")
            st.metric("Correlation Coefficient ($r$)", f"{correlation:.2f}")
            
            if correlation > 0.8:
                st.success("**Strong Positive Link:** As this country gets richer, they almost always increase calorie intake.")
            elif correlation > 0.4:
                st.info("**Moderate Link:** Wealth is a factor, but other variables (policy, culture, education) are at play.")
            else:
                st.warning("**Weak/No Link:** Calorie supply is seperate from economic growth.")

        with col2:
            # calculate the running correlation
            country_df = country_df.sort_values('Year')
            cumulative_corr = [
                country_df['GDP'].iloc[:i].corr(country_df['CalorieSupply'].iloc[:i]) 
                for i in range(2, len(country_df) + 1)
            ]
            country_df['Running_Link'] = [None] + cumulative_corr 

            # dynamic range with padding
            c_min = country_df['Running_Link'].min()
            c_max = country_df['Running_Link'].max()
            
            padding = 0.1
            y_min = max(-1.05, c_min - padding) if pd.notna(c_min) else -1
            y_max = min(1.05, c_max + padding) if pd.notna(c_max) else 1

            fig_corr = px.line(country_df, x='Year', y='Running_Link', 
                               title="Historical Wealth-Food Correlation",
                               labels={"Running_Link": "Correlation Strength (r)"})
            
            # add red line
            fig_corr.add_hline(y=0.5, line_dash="dash", line_color="red", 
                               annotation_text="Weakening Link (Below 0.5)")

            # apply dynamic range
            fig_corr.update_yaxes(
                range=[y_min, y_max], 
                zeroline=False, 
                zerolinewidth=2, 
                zerolinecolor='Black',
                gridcolor='lightgrey'
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
        st.write(f"**How to read this:** If the line stays near 1.0, wealth and food are still locked together. If the line drops, it means at this time in {target_country}, money has less influence on diet.")
else:
    st.warning("The dataframe 'df' is empty. Please check the CSV file path and column names.")
    
