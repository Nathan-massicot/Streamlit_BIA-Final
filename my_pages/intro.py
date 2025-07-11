import streamlit as st

def app():
    st.title("🏥 Introduction to LPA (Localized Potential Accessibility)")

    st.markdown("""
    The **LPA** indicator measures the spatial match between the supply of general-practice care and local demand
    at a fine geographic level. It is essential for identifying medical deserts and planning public-health policy.

    This dashboard offers a step-by-step exploration of the relationship between:
    - LPA
    - mortality before age 65
    - mortality after age 65
    - and the poverty rate
    """)