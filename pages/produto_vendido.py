import streamlit as st
import os
from datetime import datetime
from utils.database import (
    get_all_produtos,
    ASSETS_DIR,
    safe_int,
    safe_float
)

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Produtos Vendidos",
    page_icon="💰",
    layout="wide"
)

# =========================
# FUNÇÕES AUXILIARES
# =========================
def format_to_brl(value):
    try:
        num = safe_float(value)
        formatted = f"{num:_.2f}".replace(".", "X").replace("_", ".").replace("X", ",")
        return f"R$ {formatted}"
    except Exception:
        return "R$ N/A"

def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

# =========================
# ESTILO
# =========================
load_css("style.css")

# =========================
# CABEÇALHO
# =========================
st.title("💰 Histórico de Produtos Vendidos")
st.markdown("---")
st.info("Lista de produtos que já tiveram vendas, com quantidade vendida calculada automaticamente.")

# =========================
# DADOS
# =========================
todos = get_all_produtos(include_sold=True)

# Produtos que já tiveram venda
vendidos = [p for p in todos if p.get("data_ultima_venda")]

if not vendidos:
    st.success("Nenhum produto vendido até o momento.")
    st.stop()

# =========================
# MÉTRICAS
# =========================
total_produtos_vendidos = len(vendidos)
total_unidades_vendidas = 0
faturamento_estimado = 0.0

for p in vendidos:
    qtd_inicial = safe_int(p.get("quantidade_inicial", 0))
    qtd_atual = safe_int(p.get("quantidade", 0))
    qtd_vendida = max(qtd_inicial - qtd_atual, 0)

    total_unidades_vendidas += qtd_vendida
    faturamento_estimado += qtd_vendida * safe_float(p.get("preco", 0))

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Produtos vendidos", total_produtos_vendidos)
with col2:
    st.metric("Unidades vendidas", total_unidades_vendidas)
with col3:
    st.metric("Faturamento estimado", format_to_brl(faturamento_estimado))

st.markdown("---")

# =========================
# LISTAGEM DOS PRODUTOS
# =========================
for p in vendidos:
    qtd_inicial = safe_int(p.get("quantidade_inicial", 0))
    qtd_atual = safe_int(p.get("quantidade", 0))
    qtd_vendida = max(qtd_inicial - qtd_atual, 0)

    with st.container(border=True):
        col_info, col_img = st.columns([3, 1])

        with col_info:
            st.markdown(f"### {p.get('nome', 'N/A')}")
            st.write(f"💲 **Preço unitário:** {format_to_brl(p.get('preco', 0))}")

            st.write(
                f"""
                📦 **Quantidade inicial:** {qtd_inicial}  
                📉 **Quantidade atual:** {qtd_atual}  
                ✅ **Quantidade vendida:** **{qtd_vendida}**
                """
            )

            st.caption(
                f"Marca: {p.get('marca', 'N/A')} • "
                f"Tipo: {p.get('tipo', 'N/A')}"
            )

            if p.get("data_ultima_venda"):
                st.caption(f"🕒 Última venda: {p['data_ultima_venda']}")

        with col_img:
            foto = p.get("foto")
            if foto:
                path = os.path.join(ASSETS_DIR, foto)
                if os.path.exists(path):
                    st.image(path, use_container_width=True)
                else:
                    st.caption("Sem foto")
            else:
                st.caption("Sem foto")

# =========================
# RODAPÉ
# =========================
st.markdown("---")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
