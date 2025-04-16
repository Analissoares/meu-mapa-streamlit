import os
import requests
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Mapa de Fluxo - GitHub",
    layout="wide",
    page_icon="🌍"
)

# URLs do GitHub (corrigido)
BASE_GITHUB_URL = "https://github.com/Analissoares/meu-mapa-streamlit/raw/main/"
SHAPEFILE_URL = BASE_GITHUB_URL + "dados/coromandel_limite.shp"
SHX_URL       = BASE_GITHUB_URL + "dados/coromandel_limite.shx"
DBF_URL       = BASE_GITHUB_URL + "dados/coromandel_limite.dbf"
RASTER_URL    = BASE_GITHUB_URL + "dados/fluxo_acumulado.tif"
PNG_URL       = BASE_GITHUB_URL + "dados/fluxo_acumulado_com_limite.png"

def download_file(url, local_filename):
    """Baixa arquivo do GitHub"""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        return True
    except Exception as e:
        st.error(f"Erro ao baixar {url}: {e}")
        return False

def main():
    st.title("🌊 Mapa de Fluxo do GitHub")
    st.markdown("Visualização de dados hidrológicos carregados diretamente do repositório")

    view_mode = st.sidebar.radio(
        "Modo de visualização",
        ["Visualização Rápida (PNG)", "Processamento Completo (TIFF)"],
        index=0
    )

    if view_mode == "Visualização Rápida (PNG)":
        try:
            img_path = "temp_fluxo.png"
            if download_file(PNG_URL, img_path):
                img = Image.open(img_path)
                st.image(img, caption="Mapa de Fluxo Acumulado", use_column_width=True)

                with st.sidebar:
                    st.header("Ajustes de Imagem")
                    brightness = st.slider("Brilho", 0.5, 1.5, 1.0)
                    contrast = st.slider("Contraste", 0.5, 1.5, 1.0)

                    enhancer = ImageEnhance.Brightness(img)
                    img_adj = enhancer.enhance(brightness)
                    enhancer = ImageEnhance.Contrast(img_adj)
                    img_adj = enhancer.enhance(contrast)

                    st.image(img_adj, caption="Imagem Ajustada", use_column_width=True)

                os.remove(img_path)

        except Exception as e:
            st.error(f"Erro ao processar imagem PNG: {e}")

    else:
        try:
            import rasterio
            import geopandas as gpd
            from contextlib import closing

            raster_path = "temp_fluxo.tif"
            shape_path = "temp_boundary.shp"
            shx_path = "temp_boundary.shx"
            dbf_path = "temp_boundary.dbf"

            raster_ok = download_file(RASTER_URL, raster_path)
            shape_ok = (
                download_file(SHAPEFILE_URL, shape_path) and
                download_file(SHX_URL, shx_path) and
                download_file(DBF_URL, dbf_path)
            )

            if not raster_ok:
                st.error("❌ Falha ao baixar o raster.")
                return

            # Abre o raster e plota
            with closing(rasterio.open(raster_path)) as src:
                acc = src.read(1)
                bounds = src.bounds

            acc = np.where(acc < 0, np.nan, acc)
            acc_log = np.log1p(acc)
            acc_norm = (acc_log - np.nanmin(acc_log)) / (np.nanmax(acc_log) - np.nanmin(acc_log))

            fig, ax = plt.subplots(figsize=(10, 8))
            img = ax.imshow(acc_norm, cmap='Blues')
            plt.colorbar(img, ax=ax, label='Fluxo Acumulado (log)')

            if shape_ok:
                try:
                    gdf = gpd.read_file(shape_path)
                    gdf.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao carregar shapefile: {e}")
            else:
                st.warning("Shapefile de limite não disponível")

            ax.set_title('Mapa de Fluxo Acumulado')
            ax.axis('off')
            st.pyplot(fig)

            # Limpa arquivos temporários
            os.remove(raster_path)
            for ext in ['.shp', '.shx', '.dbf']:
                f = shape_path.replace('.shp', ext)
                if os.path.exists(f):
                    os.remove(f)

        except Exception as e:
            st.error(f"Erro no processamento completo: {e}")
            st.exception(e)

    st.markdown("---")
    st.markdown("""
    **Dados carregados de:**  
    [Repositório no GitHub](https://github.com/Analissoares/meu-mapa-streamlit)
    """)

if __name__ == "__main__":
    main()

