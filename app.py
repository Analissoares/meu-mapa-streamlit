from PIL import Image
import numpy as np
import streamlit as st
import geopandas as gpd
import rasterio
from contextlib import closing
import folium
from folium.raster_layers import ImageOverlay
from streamlit_folium import st_folium
from matplotlib import colormaps
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
    with closing(rasterio.open(raster_path)) as src:
        acc = src.read(1)
        bounds = src.bounds
        transform = src.transform

    # --- Processamento do raster ---
    acc = np.where(acc < 0, np.nan, acc)
    acc_log = np.log1p(acc)
    
    # Normalização
    acc_norm = (acc_log - np.nanmin(acc_log)) / (np.nanmax(acc_log) - np.nanmin(acc_log))
    
    # Configurações interativas
    with st.sidebar:
        st.header("Configurações do Mapa")
        opacity = st.slider("Opacidade do raster", 0.1, 1.0, 0.6)
        colormap_name = st.selectbox("Escala de cores", 
                                   ['viridis', 'plasma', 'cubehelix', 'magma', 'inferno'],
                                   index=2)

    # Aplica colormap
    cmap = colormaps[colormap_name]
    rgba_img = (cmap(acc_norm) * 255).astype(np.uint8)

    # --- Converte a imagem de numpy para PIL ---
    rgba_img_pil = Image.fromarray(rgba_img)

    # Salva a imagem em um buffer de memória
    img_buf = BytesIO()
    rgba_img_pil.save(img_buf, format='PNG')
    img_buf.seek(0)  # Retorna ao início do buffer

    # --- Coordenadas do raster ---
    image_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]

    # --- Cria mapa Folium ---
    m = folium.Map(location=[-18.5, -47.2], zoom_start=11, 
                  tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                  attr='OpenTopoMap')

    # Raster como sobreposição
    ImageOverlay(
        name="Fluxo acumulado",
        image=img_buf,
        bounds=image_bounds,
        opacity=opacity,
        interactive=True,
        cross_origin=False,
    ).add_to(m)

    # Adiciona shapefile
    folium.GeoJson(gdf, name="Limite", style_function=lambda x: {
        'color': 'red',
        'weight': 2,
        'fillOpacity': 0
    }).add_to(m)

    # Adiciona controle de camadas e escala
    folium.LayerControl().add_to(m)
    folium.plugins.MiniMap().add_to(m)
    folium.plugins.Fullscreen().add_to(m)
    folium.plugins.MeasureControl().add_to(m)

    # --- Exibe o mapa ---
    st.subheader("🗺️ Mapa interativo")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st_folium(m, width=800, height=600, returned_objects=[])
    
    with col2:
        st.markdown("**Legenda**")
        # Gera uma legenda simples
        plt.figure(figsize=(3, 6))
        plt.imshow(np.linspace(0, 1, 256).reshape(-1, 1), 
                  cmap=colormap_name, aspect='auto')
        plt.colorbar(label='Fluxo acumulado (log)')
        plt.axis('off')
        st.pyplot(plt.gcf(), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao gerar o mapa: {str(e)}")
    st.exception(e)
