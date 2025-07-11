import streamlit as st
from multiapp import MultiApp
from my_pages import intro, mortalite_0_64, mortalite_65_plus, pauvrete, synthese

app = MultiApp()

app.add_app("🏥 Introduction - APL", intro.app)
app.add_app("⚰️ APL & Mortalité < 65 ans", mortalite_0_64.app)
app.add_app("👵 APL & Mortalité > 65 ans", mortalite_65_plus.app)
app.add_app("💸 APL & Pauvreté", pauvrete.app)
app.add_app("🧩 Synthèse Multifacteurs", synthese.app)

app.run()
