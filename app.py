import streamlit as st
from PIL import Image

st.set_page_config(page_title="Mapa de Acumulação de Fluxo", layout="wide")
st.title("🗺️ Mapa de Acumulação de Fluxo com Delimitação")
st.markdown("Método D8 - WhiteboxTools")

# Caminho para a imagem gerada previamente
output_path = "dados/fluxo_acumulado_com_limite.png"

try:
    st.subheader("🖼️ Exibindo imagem gerada")
    image = Image.open(output_path)
    st.image(image, caption="Fluxo acumulado com limite", use_column_width=True)
except Exception as e:
    st.error(f"Erro ao carregar a imagem: {e}")
