import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import StandardScaler
import os

MAP_HEIGHT = 400  # uniform height for all maps


def app():
    """Streamlit page analysing mortality of seniors (65+) and related vulnerability metrics."""

    # ------------------------------------------------------------------
    # 🏷️  Page header
    # ------------------------------------------------------------------
    st.title("👵 APL & Mortality of 65+ Population")
    st.markdown(
        "This page analyzes several vulnerability indicators that may influence "
        "mortality of people aged 65 and over in French departments."
    )

    # ------------------------------------------------------------------
    # 📥  Load data
    # ------------------------------------------------------------------
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "dept_vulnerabilite_2022.csv"
    )
    df = pd.read_csv(data_path).dropna(
        subset=["mortalite_65_plus", "apl_med", "apl_inf", "taux_pauvrete"]
    )

    # ------------------------------------------------------------------
    # 🔢  Key indicators
    # ------------------------------------------------------------------
    avg_mortality = round(df["mortalite_65_plus"].mean(), 2)
    dep_max = df.loc[df["mortalite_65_plus"].idxmax()]
    dep_min = df.loc[df["mortalite_65_plus"].idxmin()]
    high_vuln_count = (df["classe_vuln"] == "Très élevée").sum()
    max_min_diff = round(dep_max["mortalite_65_plus"] - dep_min["mortalite_65_plus"], 2)
    high_mortality_count = (df["mortalite_65_plus"] > 40).sum()

    st.subheader("📊 Key Indicators")
    c1, c2, c3 = st.columns(3)
    c1.metric("📊 National average", f"{avg_mortality} ‰")
    c2.metric(f"🔺 Max ({dep_max['departement']})", f"{dep_max['mortalite_65_plus']} ‰")
    c3.metric(f"🔻 Min ({dep_min['departement']})", f"{dep_min['mortalite_65_plus']} ‰")

    c4, c5 = st.columns(2)
    c4.metric("🖏️ Max–min gap", f"{max_min_diff} ‰")
    c5.metric("🚩 Departments > 40 ‰", high_mortality_count)

    st.metric("🚨 Highly vulnerable departments", high_vuln_count)

    # ------------------------------------------------------------------
    # 🥇  Top‑5 barplot
    # ------------------------------------------------------------------
    st.markdown("### 🥇 Top 5 departments most affected")
    top5 = (
        df.nlargest(5, "mortalite_65_plus")[["departement", "mortalite_65_plus"]]
        .reset_index(drop=True)
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(
        data=top5,
        x="mortalite_65_plus",
        y="departement",
        hue="departement",
        palette="Reds_d",
        legend=False,
        ax=ax,
    )
    ax.set_xlabel("Mortality rate (‰)")
    ax.set_ylabel("Department")
    ax.set_title("Top 5 mortality 65+")
    st.pyplot(fig)
    plt.close(fig)

    # ------------------------------------------------------------------
    # 🔍  Mortality by vulnerability class
    # ------------------------------------------------------------------
    st.markdown("### 🔍 Mortality by overall vulnerability")
    vuln_group = (
        df.groupby("classe_vuln")["mortalite_65_plus"].mean().round(2)
        .reindex(["Faible", "Moyenne", "Élevée", "Très élevée"])
        .dropna()
    )
    palette_vuln = {
        "Faible": "#A8E6A2",
        "Moyenne": "#FFD580",
        "Élevée": "#FFA07A",
        "Très élevée": "#FF6347",
    }

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    sns.barplot(
        x=vuln_group.values,
        y=vuln_group.index,
        hue=vuln_group.index,
        palette=[palette_vuln[k] for k in vuln_group.index],
        legend=False,
        ax=ax2,
    )
    for i, v in enumerate(vuln_group.values):
        ax2.text(v + 0.3, i, f"{v} ‰", va="center", fontsize=10)
    ax2.set_title("Mortality rate 65+ by vulnerability class")
    ax2.set_xlabel("Mortality rate (‰)")
    ax2.set_ylabel("Vulnerability class")
    sns.despine()
    st.pyplot(fig2)
    plt.close(fig2)

    # ------------------------------------------------------------------
    # 📈  Correlation
    # ------------------------------------------------------------------
    corr_score = round(df["score_vuln_global"].corr(df["mortalite_65_plus"]), 3)
    st.markdown(
        f"**📈 Correlation: global vulnerability score / mortality 65+** : `{corr_score}`"
    )
    st.info(
        "Departments with higher global vulnerability scores tend to have significantly "
        "higher mortality rates among people aged 65 and over."
    )

    # ------------------------------------------------------------------
    # 🗺️  Maps in tabs
    # ------------------------------------------------------------------
    geo_path = os.path.join(os.path.dirname(__file__), "..", "data", "departements.geojson")
    st.markdown("### 🗺️ Maps")

    tab1, tab2, tab3 = st.tabs(["65+ mortality", "APL & Poverty", "Combined score"])

    # ----- Tab 1 : Mortality map ---------------------------------------
    with tab1:
        try:
            m_mort = folium.Map(location=[46.5, 2.2], zoom_start=6)
            folium.Choropleth(
                geo_data=geo_path,
                data=df,
                columns=["code_dep", "mortalite_65_plus"],
                key_on="feature.properties.code",
                fill_color="YlOrRd",
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name="Mortality rate of 65+ (‰)",
            ).add_to(m_mort)
            st_folium(m_mort, width=700, height=MAP_HEIGHT)
        except Exception as e:
            st.error("❌ Unable to display the mortality map")
            st.exception(e)

    # ----- Tab 2 : APL & Poverty map -----------------------------------
    with tab2:
        var_options = {
            "APL Doctors": "apl_med",
            "APL Nurses": "apl_inf",
            "Poverty rate": "taux_pauvrete",
        }
        selected_label = st.selectbox("Select a variable to map:", list(var_options.keys()))
        selected_column = var_options[selected_label]

        if selected_column == "apl_med":
            color, thresholds = "RdYlGn", [1.9, 2.5, 3, 3.5, 4.5, 5.2]
        elif selected_column == "apl_inf":
            color, thresholds = "RdYlGn", [60, 100, 150, 200, 250, 300]
        elif selected_column == "taux_pauvrete":
            color, thresholds = "RdYlGn", [9, 13, 17, 21, 25, 30]
        else:
            color, thresholds = "YlOrRd", None

        try:
            m_var = folium.Map(location=[46.5, 2.2], zoom_start=6)
            folium.Choropleth(
                geo_data=geo_path,
                data=df,
                columns=["code_dep", selected_column],
                key_on="feature.properties.code",
                fill_color=color,
                fill_opacity=0.7,
                line_opacity=0.2,
                threshold_scale=thresholds,
                legend_name=f"{selected_label} (critical = red | favorable = green)",
            ).add_to(m_var)
            st_folium(m_var, width=700, height=MAP_HEIGHT)
        except Exception as e:
            st.error("❌ Map not available")
            st.exception(e)

    # ----- Tab 3 : Combined senior vulnerability score -----------------
    with tab3:
        st.markdown("#### 📺 Combined senior health vulnerability score")
        st.markdown(
            "This score aggregates mortality 65+, poverty, and access to healthcare "
            "(APL doctors/nurses). Lower APL implies poorer access; therefore APL z‑scores "
            "are inverted before aggregation."
        )

        # 1️⃣ Z‑score normalisation and inversion of APL metrics
        features = ["mortalite_65_plus", "apl_med", "apl_inf", "taux_pauvrete"]
        scaler = StandardScaler()
        z_values = scaler.fit_transform(df[features])
        df_z = pd.DataFrame(z_values, columns=[f"{col}_z" for col in features])
        df_z["code_dep"] = df["code_dep"]
        df_z["apl_med_z"] *= -1
        df_z["apl_inf_z"] *= -1

        # 2️⃣ Aggregate to combined score (higher = worse)
        score_cols = [
            "mortalite_65_plus_z",
            "apl_med_z",
            "apl_inf_z",
            "taux_pauvrete_z",
        ]
        df_z["score_senior"] = df_z[score_cols].sum(axis=1).round(3)

        # 3️⃣ Merge for mapping
        df_map = df.merge(df_z[["code_dep", "score_senior"]], on="code_dep")

        # 4️⃣ Folium choropleth
        try:
            m_comb = folium.Map(location=[46.5, 2.2], zoom_start=6)
            folium.Choropleth(
                geo_data=geo_path,
                data=df_map,
                columns=["code_dep", "score_senior"],
                key_on="feature.properties.code",
                fill_color="YlOrRd",
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name="Combined senior health vulnerability score (higher = worse)",
            ).add_to(m_comb)
            st_folium(m_comb, width=700, height=MAP_HEIGHT)
        except Exception as e:
            st.error("❌ Combined map not available")
            st.exception(e)

        # 5️⃣ Table: top 10 most vulnerable departments
        st.markdown("##### 🏆 Top 10 most vulnerable departments")
        top10 = (
            df_map[["departement", "score_senior"]]
            .nlargest(10, "score_senior")
            .reset_index(drop=True)
        )
        st.dataframe(top10, hide_index=True)
