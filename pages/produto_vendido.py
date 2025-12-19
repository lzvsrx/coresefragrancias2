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
        return "R$ 0,00"

def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

load_css("style.css")

# =========================
# CABEÇALHO
# =========================
st.title("💰 Produtos Vendidos")
st.markdown("---")

# =========================
# DADOS
# =========================
produtos = get_all_produtos(include_sold=True)

# Apenas produtos que tiveram venda
vendidos = [p for p in produtos if p.get("data_ultima_venda")]

if not vendidos:
    st.success("Nenhum produto vendido até o momento.")
    st.stop()

# =========================
# CÁLCULO DO VALOR TOTAL
# (SOMA DO PREÇO UNITÁRIO)
# =========================
valor_total_produtos_vendidos = 0.0

for p in vendidos:
    preco_unitario = safe_float(p.get("preco", 0))
    valor_total_produtos_vendidos += preco_unitario

# =========================
# MÉTRICA PRINCIPAL
# =========================
st.metric(
    "💰 Valor total dos produtos vendidos (soma do preço unitário)",
    format_to_brl(valor_total_produtos_vendidos)
)

st.success(
    f"💰 **VALOR TOTAL DOS PRODUTOS VENDIDOS:** "
    f"{format_to_brl(valor_total_produtos_vendidos)}"
)

st.markdown("---")

# =========================
# LISTAGEM DOS PRODUTOS
# =========================
for p in vendidos:
    preco_unitario = safe_float(p.get("preco", 0))

    with st.container(border=True):
        col_info, col_img = st.columns([3, 1])

        with col_info:
            st.markdown(f"### 🛒 {p.get('nome', 'Produto')}")
            st.write(f"💲 **Preço unitário:** {format_to_brl(preco_unitario)}")

            st.caption(
                f"Marca: {p.get('marca', 'N/A')} • "
                f"Tipo: {p.get('tipo', 'N/A')}"
            )

            if p.get("data_ultima_venda"):
                st.caption(f"🕒 Última venda: {p['data_ultima_venda']}")

        with col_img:
            foto = p.get("foto")
            if foto:
                caminho = os.path.join(ASSETS_DIR, foto)
                if os.path.exists(caminho):
                    st.image(caminho, use_container_width=True)
                else:
                    st.caption("Imagem não encontrada")
            else:
                st.caption("Sem imagem")

# =========================
# RODAPÉ
# =========================
st.markdown("---")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
