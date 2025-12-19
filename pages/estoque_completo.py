import streamlit as st
import os
from datetime import datetime
from utils.database import get_all_produtos, ASSETS_DIR, MARCAS, ESTILOS, TIPOS, safe_int, safe_float

st.set_page_config(page_title="Estoque Completo", page_icon="📦", layout="wide")

def format_to_brl(value):
    try:
        num = safe_float(value)
        formatted = f"{num:_.2f}".replace(".", "X").replace("_", ".").replace("X", ",")
        return "R$ " + formatted
    except Exception:
        return "R$ N/A"

def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

load_css("style.css")

st.title("📦 Estoque Completo - Cores e Fragrâncias")
st.markdown("---")

produtos = get_all_produtos(include_sold=True)
if not produtos:
    st.info("Nenhum produto cadastrado.")
    st.stop()

def get_unique(field):
    return sorted(list(set(p.get(field, "") for p in produtos if p.get(field))))

marcas = get_unique("marca") or MARCAS
estilos = get_unique("estilo") or ESTILOS
tipos = get_unique("tipo") or TIPOS

col1, col2, col3 = st.columns(3)
with col1:
    marca_f = st.selectbox("Filtrar por Marca", ["Todas"] + marcas)
with col2:
    estilo_f = st.selectbox("Filtrar por Estilo", ["Todos"] + estilos)
with col3:
    tipo_f = st.selectbox("Filtrar por Tipo", ["Todos"] + tipos)

col4, col5 = st.columns(2)
with col4:
    qtd_min = st.number_input("Quantidade mínima", min_value=0, value=0)
with col5:
    busca = st.text_input("Buscar por nome")

produtos_filtrados = produtos[:]
if marca_f != "Todas":
    produtos_filtrados = [p for p in produtos_filtrados if p.get("marca") == marca_f]
if estilo_f != "Todos":
    produtos_filtrados = [p for p in produtos_filtrados if p.get("estilo") == estilo_f]
if tipo_f != "Todos":
    produtos_filtrados = [p for p in produtos_filtrados if p.get("tipo") == tipo_f]
if qtd_min > 0:
    produtos_filtrados = [p for p in produtos_filtrados if safe_int(p.get("quantidade", 0)) >= qtd_min]
if busca:
    produtos_filtrados = [p for p in produtos_filtrados if busca.lower() in p.get("nome", "").lower()]

if not produtos_filtrados:
    st.warning("Nenhum produto encontrado com esses filtros.")
    st.stop()

total = 0.0
for p in produtos_filtrados:
    total += safe_float(p.get("preco", 0)) * safe_int(p.get("quantidade", 0))

colm1, colm2 = st.columns(2)
with colm1:
    st.metric("Produtos filtrados", len(produtos_filtrados))
with colm2:
    st.metric("Valor total filtrado", format_to_brl(total))

st.markdown("---")

for p in produtos_filtrados:
    with st.container(border=True):
        col_img, col_info = st.columns([1, 3])
        with col_img:
            foto = p.get("foto")
            if foto:
                path = os.path.join(ASSETS_DIR, foto)
                if os.path.exists(path):
                    st.image(path, width=120, use_container_width=True)
                else:
                    st.caption("Sem foto")
            else:
                st.caption("Sem foto")
        with col_info:
            st.markdown(f"**{p.get('nome', 'N/A')}**")
            st.caption(f"{p.get('marca', 'N/A')} • {p.get('estilo', 'N/A')} • {p.get('tipo', 'N/A')}")
            qtd = safe_int(p.get("quantidade", 0))
            preco = safe_float(p.get("preco", 0))
            st.write(f"Preço: {format_to_brl(preco)} | Quantidade: {qtd} | Total: {format_to_brl(preco * qtd)}")

st.markdown("---")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
