# my_pages/carte_apl_mortalite.py
"""
Carte choroplèthe des APL et barres 3‑D de mortalité prématurée
Couleurs inversées : **rouge = favorable**, **vert = critique**.
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from pathlib import Path
import matplotlib.cm as cm
import re

# ────────────────────────────────────────────────────────────────────────
# 1. Chargement des données
# ────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_geo():
    g = gpd.read_file(Path("data") / "departements.geojson")[["code", "nom", "geometry"]]
    g["code"] = g["code"].astype(str).str.upper()
    if g.crs is None or g.crs.to_epsg() != 4326:
        g = g.to_crs(epsg=4326)
    return g


@st.cache_data
def load_ind():
    df = pd.read_csv(Path("data") / "dept_vulnerabilite_2022.csv",
                     dtype={"code_dep": "string"})
    df = df.rename(columns={
        "code_dep":       "code",       # identifiant département
        "apl_med":        "apl_med",    # accessibilité médecins
        "apl_inf":        "apl_inf",    # accessibilité infirmiers
        "taux_pauvrete":  "taux_pauvrete",
        "mortalite_0_64": "mort_premat" # mortalité prématurée
    })
    # Nettoie codes → format à 2 caractères, majuscules
    df["code"] = df["code"].apply(
        lambda c: re.sub(r"\s+", "", str(c)).upper().zfill(2)
        if str(c).isdigit() and len(str(c)) == 1 else str(c).upper()
    )
    return df


# ────────────────────────────────────────────────────────────────────────
# 2. Palette discrète selon seuils
# ────────────────────────────────────────────────────────────────────────

def classify_color(values, thresholds, cmap_name, reverse=False):
    """Associe chaque valeur à une couleur RGBA selon des classes discrètes."""
    cmap = cm.get_cmap(cmap_name + ("_r" if reverse else ""))
    n_cls = len(thresholds) + 1
    bounds = [-float("inf")] + thresholds + [float("inf")]

    # Couleurs prélevées régulièrement dans la cmap
    color_steps = [cmap(i / (n_cls - 1)) for i in range(n_cls)]

    def get_color(v):
        for i in range(n_cls):
            if bounds[i] < v <= bounds[i + 1]:
                r, g, b, a = color_steps[i]
                return [int(r * 255), int(g * 255), int(b * 255), 220]
        return [0, 0, 0, 0]

    return values.apply(get_color)


# ────────────────────────────────────────────────────────────────────────
# 3. Application Streamlit
# ────────────────────────────────────────────────────────────────────────

def app():
    st.title("🗺️ Carte APL + mortalité prématurée (barres 3‑D)")

    # Choix de l'indicateur pour la surface
    col_id = st.selectbox(
        "Indicateur pour la surface :",
        options=[("apl_med", "APL médecins"), ("apl_inf", "APL infirmiers"),
                 ("taux_pauvrete", "Taux de pauvreté")],
        format_func=lambda x: x[1]
    )[0]

    # Palettes & seuils (couleurs inversées : rouge = favorable, vert = critique)
    if col_id == "apl_med":
        palette, thr, reverse = "RdYlGn", [1.9, 2.5, 3, 3.5, 4.5, 5.2], False  # plus de reverse ➜ rouge=favor.
    elif col_id == "apl_inf":
        palette, thr, reverse = "RdYlGn", [60, 100, 150, 200, 250, 300], False
    else:  # taux de pauvreté
        palette, thr, reverse = "YlOrRd", [9, 13, 17, 21, 25, 30], True        # reverse ➜ rouge=favor.

    # Fusion données géographiques + indicateurs
    gdf = load_geo().merge(load_ind(), on="code", how="left")

    # Couleur discrète sur la surface
    gdf["fill_color"] = classify_color(gdf[col_id], thr, palette, reverse)

    # Hauteur des barres (mortalité prématurée)
    MAX_H = 100_000  # 100 km en "vrai" Deck.gl
    mort_min, mort_max = gdf["mort_premat"].min(), gdf["mort_premat"].max()
    gdf["bar_elev"] = (gdf["mort_premat"] - mort_min) / (mort_max - mort_min) * MAX_H

    # Centroïdes (WGS84) pour positionner les barres
    cent_l93 = gdf.to_crs(2154).centroid
    gdf["lon"], gdf["lat"] = (
        gpd.GeoSeries(cent_l93, crs=2154).to_crs(4326).x,
        gpd.GeoSeries(cent_l93, crs=2154).to_crs(4326).y,
    )

    # Couche surface (départements)
    poly_layer = pdk.Layer(
        "GeoJsonLayer",
        data=gdf.__geo_interface__,
        stroked=True,
        get_line_color="[80,80,80]",
        line_width_min_pixels=0.5,
        filled=True,
        get_fill_color="properties.fill_color",
        pickable=False,
    )

    # Couche barres cylindriques
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=gdf,
        get_position="[lon, lat]",
        get_elevation="bar_elev",
        elevation_scale=1,
        radius=8_000,
        get_fill_color="[190,190,190,190]",
        pickable=True,
        auto_highlight=True,
    )

    # Légende sous le titre
    palette_name = palette + (" inversé" if reverse else "")
    st.markdown(
        f"*Surface : palette **{palette_name}** – seuils {thr}*  \n"
        f"*Barres : hauteur → mortalité prématurée (0 → {MAX_H/1000:.0f} km)*"
    )

    # Carte Deck.gl
    deck = pdk.Deck(
        layers=[poly_layer, column_layer],
        map_style="mapbox://styles/mapbox/light-v11",
        initial_view_state=pdk.ViewState(
            latitude=46.6, longitude=2.5, zoom=5.2, pitch=65, bearing=15
        ),
        tooltip={
            "html": (
                "<b>{nom}</b><br/>"
                f"{col_id} : {{{col_id}}}<br/>"
                "Mortalité prématurée : {mort_premat} ‰"
            ),
            "style": {"max-width": "220px"}
        }
    )

    st.pydeck_chart(deck, use_container_width=True)
