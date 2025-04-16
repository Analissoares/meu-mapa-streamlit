import streamlit as st
import geopandas as gpd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

st.set_page_config(page_title="Mapa de Acumulação de Fluxo", layout="wide")
st.title("🗺️ Mapa de Acumulação de Fluxo com Delimitação")
st.markdown("Método D8 - WhiteboxTools")

# Caminhos
shapefile_path = "dados/coromandel_limite.shp"
raster_path = "dados/fluxo_acumulado.tif"
output_path = "dados/fluxo_acumulado_com_limite.png"

try:
    st.subheader("📂 Carregando shapefile e raster...")

    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs("EPSG:4326")

    with rasterio.open(raster_path) as src:
        acc = src.read(1)
        bounds = src.bounds

    st.subheader("🎨 Gerando imagem...")

    plt.figure(figsize=(12, 8))
    img = plt.imshow(np.log1p(acc), cmap='cubehelix',
                     extent=[bounds.left, bounds.right, bounds.bottom, bounds.top])
    gdf.boundary.plot(ax=plt.gca(), color='red', linewidth=1.5, label='Limite')

    cbar = plt.colorbar(img)
    cbar.set_label('log(Fluxo acumulado por célula)', fontsize=11)

    plt.title('Mapa de Acumulação de Fluxo com Delimitação\nMétodo D8 - WhiteboxTools', fontsize=14)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend()
    plt.tight_layout()
    plt.axis('on')

    plt.savefig(output_path, dpi=300)
    plt.close()

    st.image(output_path, caption="Fluxo acumulado com limite", use_column_width=True)

except Exception as e:
    st.error(f"Erro ao carregar ou processar os dados: {e}")