import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

def app():
    st.title("Health Inequalities in France: Premature Mortality & Medical Accessibility")

    st.markdown("""
    This dashboard explores **healthcare disparities** between French departments using two key indicators:
    
    - **Premature mortality** (under age 65)
    - **Access to general practitioners (APL)**

    A vulnerability score combines these indicators to highlight the most at-risk regions.
    """)

    # Load data
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "dept_vulnerabilite_2022.csv"))
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "departements.geojson"), "r", encoding="utf-8") as f:
        geojson_dept = json.load(f)

    # Convert necessary columns
    numeric_cols = ["mortalite_0_64", "apl_med", "z_mortalite_0_64", "vuln_apl_med", "score_vuln_global"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["classe_vuln", "score_vuln_global"])

    # --- Section 1: Map of Premature Mortality ---
    st.header("1. Map of Premature Mortality (under age 65)")

    st.markdown("""
    This map shows the **raw premature mortality rate** per 1,000 inhabitants.

    > High mortality rates may reflect limited access to healthcare, delayed diagnoses, or care avoidance in underserved regions.
    """)

    fig_mortality = px.choropleth(
        df,
        geojson=geojson_dept,
        locations="code_dep",
        featureidkey="properties.code",
        color="mortalite_0_64",
        color_continuous_scale="Reds",
        hover_name="departement",
        labels={"mortalite_0_64": "Premature Mortality (‰)"}
    )
    fig_mortality.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig_mortality, use_container_width=True)

    # --- Section 2: Map of APL ---
    st.header("2. Map of Healthcare Accessibility (APL)")

    st.markdown("""
    This map displays the **Localized Potential Accessibility (APL)** score for general practitioners.

    > Higher APL values indicate **better access** to primary care.  
    Lower values may reflect **GP shortages** or **geographic isolation**.
    """)

    fig_apl = px.choropleth(
        df,
        geojson=geojson_dept,
        locations="code_dep",
        featureidkey="properties.code",
        color="apl_med",
        color_continuous_scale="Blues",
        hover_name="departement",
        labels={"apl_med": "APL (GP Access)"}
    )
    fig_apl.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig_apl, use_container_width=True)

    # --- Section 3: National KPIs ---
    st.header("3. National Summary")

    avg_mort = df["mortalite_0_64"].mean()
    avg_apl = df["apl_med"].mean()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg Premature Mortality", f"{avg_mort:.2f} ‰")
    with col2:
        st.metric("Avg GP Accessibility (APL)", f"{avg_apl:.2f}")

    # --- Section 4: Most Vulnerable Departments ---
    st.header("4. Departments with Very High Vulnerability")

    st.markdown("""
    The departments below are classified as **'Very High' vulnerability**, based on a combined score of:
    - **Premature mortality**
    - **Medical accessibility (APL)**

    The bar chart shows:
    - Y-axis: mortality rate
    - Color: APL (access to general practitioners)
    """)

    top_vuln = df[df["classe_vuln"] == "Très élevée"].copy()
    top_vuln = top_vuln.sort_values(by="mortalite_0_64", ascending=False)

    fig_bar = px.bar(
        top_vuln,
        x="departement",
        y="mortalite_0_64",
        color="apl_med",
        hover_data=["apl_med", "score_vuln_global"],
        labels={
            "departement": "Department",
            "mortalite_0_64": "Mortality < 65 (‰)",
            "apl_med": "APL (GP Access)",
            "score_vuln_global": "Global Vulnerability Score"
        },
        title="Most Vulnerable Departments by Premature Mortality"
    )
    fig_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("""
    > **Interpretation:**  
    Departments such as **Creuse**, **Nièvre**, or **Cher** face both **high premature mortality** and **poor access to care**.  
    These regions should be prioritized for **primary care reinforcement**.
    """)

    # --- Final Interpretation ---
    st.markdown("""
    ### 5. Conclusion

    - Significant **territorial inequalities** remain in access to healthcare in France.
    - Some departments show **both high premature mortality and low GP availability**, signaling compounded risk.
    - These insights can help guide **targeted investment in healthcare infrastructure** and **early intervention strategies**.
    """)
