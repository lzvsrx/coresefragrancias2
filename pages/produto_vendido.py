import streamlit as st
import os
from datetime import datetime
from utils.database import (
    get_all_produtos,
    ASSETS_DIR,
    safe_int,
    safe_float
)
load_css("style.css")
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
        value = safe_float(value)
        return f"R$ {value:_.2f}".replace(".", "X").replace("_", ".").replace("X", ",")
    except Exception:
        return "R$ 0,00"

# =========================
# CABEÇALHO
# =========================
st.title("💰 Relatório de Produtos Vendidos")
st.markdown("---")

# =========================
# BUSCA DE DADOS
# =========================
produtos = get_all_produtos(include_sold=True)

# Apenas produtos com venda registrada
vendidos = [p for p in produtos if p.get("data_ultima_venda")]

if not vendidos:
    st.info("Nenhum produto vendido até o momento.")
    st.stop()

# =========================
# CÁLCULOS
# =========================
total_produtos_vendidos = len(vendidos)
total_unidades_vendidas = 0
valor_total_vendido = 0.0

for p in vendidos:
    qtd_inicial = safe_int(p.get("quantidade_inicial", 0))
    qtd_atual = safe_int(p.get("quantidade", 0))
    qtd_vendida = max(qtd_inicial - qtd_atual, 0)

    preco = safe_float(p.get("preco", 0))

    total_unidades_vendidas += qtd_vendida
    valor_total_vendido += qtd_vendida * preco

# =========================
# MÉTRICAS
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📦 Produtos vendidos", total_produtos_vendidos)

with col2:
    st.metric("📉 Unidades vendidas", total_unidades_vendidas)

with col3:
    st.metric("💰 Valor total vendido", format_to_brl(valor_total_vendido))

# =========================
# DESTAQUE DO FATURAMENTO
# =========================
st.success(
    f"💰 **VALOR TOTAL DOS PRODUTOS VENDIDOS:** {format_to_brl(valor_total_vendido)}"
)

st.markdown("---")

# =========================
# LISTAGEM DETALHADA
# =========================
for p in vendidos:
    qtd_inicial = safe_int(p.get("quantidade_inicial", 0))
    qtd_atual = safe_int(p.get("quantidade", 0))
    qtd_vendida = max(qtd_inicial - qtd_atual, 0)
    preco = safe_float(p.get("preco", 0))

    total_produto = qtd_vendida * preco

    with st.container(border=True):
        col_info, col_img = st.columns([3, 1])

        with col_info:
            st.markdown(f"### 🛒 {p.get('nome', 'Produto')}")
            st.write(f"💲 **Preço unitário:** {format_to_brl(preco)}")
            st.write(f"📦 **Quantidade vendida:** {qtd_vendida}")
            st.write(f"💵 **Total vendido deste produto:** {format_to_brl(total_produto)}")

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

