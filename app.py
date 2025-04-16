import streamlit as st
import geopandas as gpd
import rasterio
import folium
import numpy as np
from folium.raster_layers import ImageOverlay
from streamlit_folium import st_folium
from matplotlib import pyplot as plt
from matplotlib import cm
from io import BytesIO

st.set_page_config(page_title="Mapa Interativo de Fluxo", layout="wide")
st.title("🗺️ Mapa de Acumulação de Fluxo com Delimitação")
st.markdown("Visualização interativa com Folium")

# Caminhos dos arquivos
shapefile_path = "dados/coromandel_limite.shp"
raster_path = "dados/fluxo_acumulado.tif"

try:
    # --- Carrega shapefile ---
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs("EPSG:4326")  # Garante o CRS correto

    # --- Carrega raster ---
    with rasterio.open(raster_path) as src:
        acc = src.read(1)
        bounds = src.bounds
        transform = src.transform

    # --- Normaliza e aplica colormap ---
    acc_log = np.log1p(acc)
    acc_norm = (acc_log - np.nanmin(acc_log)) / (np.nanmax(acc_log) - np.nanmin(acc_log))

    cmap = cm.get_cmap('cubehelix')
    rgba_img = (cmap(acc_norm) * 255).astype(np.uint8)

    # --- Salva imagem em memória ---
    img_buf = BytesIO()
    plt.imsave(img_buf, rgba_img, format='png')
    img_buf.seek(0)

    # --- Coordenadas do raster ---
    image_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]

    # --- Cria mapa Folium ---
    m = folium.Map(location=[-18.5, -47.2], zoom_start=11)

    # Raster como sobreposição
    ImageOverlay(
        name="Fluxo acumulado",
        image=img_buf,
        bounds=image_bounds,
        opacity=0.6,
        interactive=True,
        cross_origin=False,
    ).add_to(m)

    # Adiciona shapefile
    folium.GeoJson(gdf, name="Limite", style_function=lambda x: {
        'color': 'red',
        'weight': 2
    }).add_to(m)

    # Camadas
    folium.LayerControl().add_to(m)

    # --- Exibe o mapa ---
    st.subheader("🗺️ Mapa interativo")
    st_folium(m, width=1000, height=600)

except Exception as e:
    st.error(f"Erro ao gerar o mapa: {e}")
