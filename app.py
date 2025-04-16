import os
import requests
import numpy as np
import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Mapa de Fluxo - GitHub",
    layout="wide",
    page_icon="🌍"
)

# URLs dos arquivos no GitHub (substitua com seus URLs reais)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/{seu_usuario}/{seu_repo}/main/"
SHAPEFILE_URL = GITHUB_RAW_URL + "dados/coromandel_limite.shp"
RASTER_URL = GITHUB_RAW_URL + "dados/fluxo_acumulado.tif"
PNG_URL = GITHUB_RAW_URL + "dados/fluxo_acumulado_com_limite.png"

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

    # Modo de visualização (PNG ou processamento completo)
    view_mode = st.sidebar.radio(
        "Modo de visualização",
        ["Visualização Rápida (PNG)", "Processamento Completo (TIFF)"],
        index=0
    )

    if view_mode == "Visualização Rápida (PNG)":
        # Modo simples com PNG
        try:
            # Baixa a imagem do GitHub
            img_path = "temp_fluxo.png"
            if download_file(PNG_URL, img_path):
                img = Image.open(img_path)
                st.image(img, caption="Mapa de Fluxo Acumulado", use_column_width=True)
                
                # Controles de imagem
                with st.sidebar:
                    st.header("Ajustes de Imagem")
                    brightness = st.slider("Brilho", 0.5, 1.5, 1.0)
                    contrast = st.slider("Contraste", 0.5, 1.5, 1.0)
                    
                    # Aplica ajustes
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Brightness(img)
                    img_adj = enhancer.enhance(brightness)
                    enhancer = ImageEnhance.Contrast(img_adj)
                    img_adj = enhancer.enhance(contrast)
                    
                    st.image(img_adj, caption="Imagem Ajustada", use_column_width=True)
                
                # Limpa arquivo temporário
                os.remove(img_path)
        
        except Exception as e:
            st.error(f"Erro ao processar imagem: {e}")

    else:
        # Modo completo com processamento do TIFF
        try:
            # Verifica dependências
            try:
                import rasterio
                import geopandas as gpd
                from contextlib import closing
            except ImportError:
                st.error("Bibliotecas necessárias não encontradas.")
                st.markdown("""
                **Instale com:**
                ```bash
                pip install rasterio geopandas
                ```
                """)
                return

            # Baixa arquivos
            raster_path = "temp_fluxo.tif"
            shape_path = "temp_boundary.shp"
            
            if not (download_file(RASTER_URL, raster_path) and 
                   download_file(SHAPEFILE_URL, shape_path)):
                return

            # Processamento do raster
            with closing(rasterio.open(raster_path)) as src:
                acc = src.read(1)
                bounds = src.bounds
            
            # Processamento básico
            acc = np.where(acc < 0, np.nan, acc)
            acc_log = np.log1p(acc)
            acc_norm = (acc_log - np.nanmin(acc_log)) / (np.nanmax(acc_log) - np.nanmin(acc_log))

            # Visualização
            fig, ax = plt.subplots(figsize=(10, 8))
            img = ax.imshow(acc_norm, cmap='Blues')
            plt.colorbar(img, ax=ax, label='Fluxo Acumulado (log)')
            
            # Adiciona boundary se disponível
            try:
                gdf = gpd.read_file(shape_path)
                gdf.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
            except:
                st.warning("Não foi possível carregar o shapefile de limite")

            ax.set_title('Mapa de Fluxo Acumulado')
            ax.axis('off')
            st.pyplot(fig)

            # Limpa arquivos temporários
            os.remove(raster_path)
            for ext in ['.shp', '.shx', '.dbf']:
                if os.path.exists(shape_path.replace('.shp', ext)):
                    os.remove(shape_path.replace('.shp', ext))

        except Exception as e:
            st.error(f"Erro no processamento completo: {e}")
            st.exception(e)

    # Rodapé
    st.markdown("---")
    st.markdown("""
    **Dados carregados de:**  
    [GitHub Repository]({seu_link_do_repo})  
    """)

if __name__ == "__main__":
    main()

