import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import pearsonr


def app():
    st.title("🏥 APL & Poverty Analysis")
    st.markdown(
        "Analysis of health accessibility (APL) and poverty indicators across French departments (2022)."
    )

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "dept_vulnerabilite_2022.csv"
    )
    df = pd.read_csv(data_path)

    # ------------------------------------------------------------------
    # Variable‑specific configuration
    # ------------------------------------------------------------------
    var_config = {
        "APL Doctors": {
            "col": "apl_med",
            "better": "Higher values indicate better medical accessibility (doctors).",
            "unit": "",
            "fmt": "{:.2f}",
            "threshold": 2.5,  # low access below 2.5
            "direction": "lower",  # lower values = vulnerability
        },
        "APL Nurses": {
            "col": "apl_inf",
            "better": "Higher values indicate better nursing accessibility.",
            "unit": "",
            "fmt": "{:.0f}",
            "threshold": 100,
            "direction": "lower",
        },
        "Poverty rate": {
            "col": "taux_pauvrete",
            "better": "Lower values indicate less poverty.",
            "unit": "%",
            "fmt": "{:.1f}",
            "threshold": 20,
            "direction": "higher",  # higher values = vulnerability
        },
    }

    # Create one tab per indicator
    tabs = st.tabs(list(var_config.keys()))

    # ------------------------------------------------------------------
    # Iterate over tabs / indicators
    # ------------------------------------------------------------------
    for tab_label, tab in zip(var_config.keys(), tabs):
        with tab:
            cfg = var_config[tab_label]
            col_id = cfg["col"]
            values = df[col_id]

            # ---------------- KPI values ----------------
            avg = round(values.mean(), 2)
            dep_max = df.loc[values.idxmax()]
            dep_min = df.loc[values.idxmin()]

            # best/worst depend on direction (lower = vulnerability)
            if cfg["direction"] == "lower":
                best_dep = dep_max  # high value = good accessibility / low poverty
                worst_dep = dep_min
            else:
                best_dep = dep_min
                worst_dep = dep_max

            gap = round(best_dep[col_id] - worst_dep[col_id], 2)

            # Vulnerable departments count
            if cfg["direction"] == "lower":
                vuln_count = df[df[col_id] < cfg["threshold"]].shape[0]
            else:
                vuln_count = df[df[col_id] > cfg["threshold"]].shape[0]

            # ---------------- Display KPIs ----------------
            st.subheader(f"📊 Key indicators – {tab_label}")
            col1, col2, col3 = st.columns(3)
            col1.metric("National average", cfg["fmt"].format(avg) + cfg["unit"])
            col2.metric(
                f"Best ({best_dep['departement']})",
                cfg["fmt"].format(best_dep[col_id]) + cfg["unit"],
            )
            col3.metric(
                f"Worst ({worst_dep['departement']})",
                cfg["fmt"].format(worst_dep[col_id]) + cfg["unit"],
            )

            col4, col5 = st.columns(2)
            col4.metric("Gap (best–worst)", cfg["fmt"].format(gap) + cfg["unit"])
            col5.metric("Vulnerable depts", vuln_count)

            # ---------------- Top‑5 bar chart (Seaborn ≥0.14 compliant) ----------------
            st.markdown("### 🥇 Top 5 departments most vulnerable")
            if cfg["direction"] == "lower":
                top5 = df.nsmallest(5, col_id)[["departement", col_id]]
            else:
                top5 = df.nlargest(5, col_id)[["departement", col_id]]

            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(
                data=top5,
                x=col_id,
                y="departement",
                hue="departement",
                palette="Reds",
                legend=False,
                ax=ax,
            )
            ax.set_xlabel(tab_label)
            ax.set_ylabel("Department")
            ax.set_title(f"Top 5 – {tab_label}")
            if ax.get_legend() is not None:
                ax.get_legend().remove()
            st.pyplot(fig)

    # ------------------------------------------------------------------
  
    st.header("📈 Correlation: Poverty rate vs APL ")
    fig_inf, ax_inf = plt.subplots(figsize=(8, 6))
    sns.regplot(
        data=df,
        x="apl_inf",
        y="taux_pauvrete",
        ax=ax_inf,
        scatter_kws={"s": 60, "alpha": 0.7},
    )
    ax_inf.set_xlabel("APL Nurses (higher = better access)")
    ax_inf.set_ylabel("Poverty rate (%)")
    ax_inf.set_title("Correlation between poverty rate and nurses accessibility (2022)")

    r_inf, p_inf = pearsonr(df["apl_inf"], df["taux_pauvrete"])
    st.pyplot(fig_inf)
    plt.close(fig_inf)
    st.markdown(f"**Pearson r = {r_inf:.2f}** (p = {p_inf:.3f})")
