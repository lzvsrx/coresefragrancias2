import streamlit as st
import os
from datetime import datetime, date
from utils.database import (
    add_produto, get_all_produtos, update_produto, delete_produto, get_produto_by_id,
    export_produtos_to_csv_content, import_produtos_from_csv_buffer, generate_stock_pdf_bytes,
    mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS, ASSETS_DIR, safe_int, safe_float
)

st.set_page_config(page_title="Gerenciar Produtos", page_icon="🛠️", layout="wide")

def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

def format_to_brl(value):
    try:
        num = safe_float(value)
        formatted = f"{num:_.2f}".replace(".", "X").replace("_", ".").replace("X", ",")
        return "R$ " + formatted
    except Exception:
        return "R$ N/A"

load_css("style.css")

if not st.session_state.get("logged_in"):
    st.error("Acesso restrito. Faça login na Área Administrativa.")
    st.stop()

if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False
if "edit_product_id" not in st.session_state:
    st.session_state["edit_product_id"] = None
if "role" not in st.session_state:
    st.session_state["role"] = "staff"

st.title("🛠️ Gerenciar Produtos")
st.markdown("---")

def add_product_form():
    st.subheader("➕ Adicionar Novo Produto")
    with st.form("add_product_form", clear_on_submit=True):
        nome = st.text_input("Nome do Produto", max_chars=150)
        col1, col2 = st.columns([2, 1])
        with col1:
            marca = st.selectbox("Marca", ["Selecionar"] + MARCAS)
            estilo = st.selectbox("Estilo", ["Selecionar"] + ESTILOS)
            tipo = st.selectbox("Tipo", ["Selecionar"] + TIPOS)
            preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f", step=0.5)
            quantidade = st.number_input("Quantidade", min_value=0, step=1, value=1)
            data_validade = st.date_input("Validade (opcional)", value=None, min_value=date.today())
        with col2:
            foto = st.file_uploader("Foto do Produto", type=["png", "jpg", "jpeg"])
            if foto:
                st.image(foto, use_container_width=True)
        submitted = st.form_submit_button("Salvar Produto")
        if submitted:
            if not nome or preco <= 0 or marca == "Selecionar" or tipo == "Selecionar":
                st.error("Preencha Nome, Preço > 0, Marca e Tipo.")
                return
            photo_name = None
            if foto:
                photo_name = f"{int(datetime.now().timestamp())}_{foto.name}"
                with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                    f.write(foto.getbuffer())
            validade_iso = data_validade.isoformat() if data_validade else None
            try:
                add_produto(nome, preco, quantidade, marca, estilo, tipo, photo_name, validade_iso)
                st.success(f"Produto '{nome}' cadastrado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar produto: {e}")

def show_edit_form():
    produto_id = st.session_state.get("edit_product_id")
    p = get_produto_by_id(produto_id)
    if not p:
        st.error("Produto não encontrado.")
        st.session_state["edit_mode"] = False
        st.rerun()
    st.subheader(f"✏️ Editando: {p['nome']} (ID {p['id']})")
    with st.form("edit_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            novo_nome = st.text_input("Nome", value=p["nome"])
            novo_preco = st.number_input("Preço", value=safe_float(p["preco"]), format="%.2f")
            nova_qtd = st.number_input("Quantidade", value=safe_int(p["quantidade"]), min_value=0)
            marca_idx = MARCAS.index(p["marca"]) if p.get("marca") in MARCAS else 0
            estilo_idx = ESTILOS.index(p["estilo"]) if p.get("estilo") in ESTILOS else 0
            tipo_idx = TIPOS.index(p["tipo"]) if p.get("tipo") in TIPOS else 0
            nova_marca = st.selectbox("Marca", MARCAS, index=marca_idx)
            novo_estilo = st.selectbox("Estilo", ESTILOS, index=estilo_idx)
            novo_tipo = st.selectbox("Tipo", TIPOS, index=tipo_idx)
        with col2:
            st.info(f"Foto atual: {p.get('foto') or 'Sem foto'}")
            nova_foto = st.file_uploader("Nova foto (opcional)", type=["jpg", "png", "jpeg"])
            if nova_foto:
                st.image(nova_foto, use_container_width=True)
        colb1, colb2 = st.columns(2)
        salvar = colb1.form_submit_button("Salvar Alterações")
        cancelar = colb2.form_submit_button("Cancelar")
        if salvar:
            foto_final = p.get("foto")
            if nova_foto:
                if foto_final:
                    try:
                        os.remove(os.path.join(ASSETS_DIR, foto_final))
                    except Exception:
                        pass
                foto_final = f"{int(datetime.now().timestamp())}_{nova_foto.name}"
                with open(os.path.join(ASSETS_DIR, foto_final), "wb") as f:
                    f.write(nova_foto.getbuffer())
            validade_iso = p.get("data_validade")
            try:
                update_produto(produto_id, novo_nome, novo_preco, nova_qtd,
                               nova_marca, novo_estilo, novo_tipo, foto_final, validade_iso)
                st.success("Produto atualizado.")
                st.session_state["edit_mode"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")
        if cancelar:
            st.session_state["edit_mode"] = False
            st.rerun()

def manage_products_list_actions():
    st.subheader("📋 Lista de Produtos")
    colr1, colr2, colr3 = st.columns(3)
    with colr1:
        csv_content = export_produtos_to_csv_content()
        st.download_button("Exportar CSV", csv_content.encode("utf-8"),
                           "estoque.csv", "text/csv")
    with colr2:
        if st.button("Gerar PDF Estoque Ativo"):
            try:
                pdf_bytes = generate_stock_pdf_bytes()
                st.download_button("Baixar PDF", pdf_bytes,
                                   "estoque_ativo.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
    with colr3:
        csv_file = st.file_uploader("Importar CSV", type=["csv"])
        if csv_file and st.button("Processar CSV"):
            try:
                count = import_produtos_from_csv_buffer(csv_file)
                st.success(f"{count} produtos importados.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

    st.markdown("---")
    produtos = get_all_produtos()
    if not produtos:
        st.info("Nenhum produto cadastrado.")
        return
    total = 0.0
    for p in produtos:
        pid = p["id"]
        preco = safe_float(p["preco"])
        qtd = safe_int(p["quantidade"])
        subtotal = preco * qtd
        total += subtotal
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if p.get("foto"):
                    path = os.path.join(ASSETS_DIR, p["foto"])
                    if os.path.exists(path):
                        st.image(path, use_container_width=True)
                    else:
                        st.caption("Sem foto")
                else:
                    st.caption("Sem foto")
            with col2:
                st.markdown(f"**{p['nome']}** (ID {pid})")
                st.write(f"{format_to_brl(preco)} | Qtd: {qtd} | Total: {format_to_brl(subtotal)}")
                st.caption(f"{p.get('marca', '')} • {p.get('tipo', '')} • Validade: {p.get('data_validade') or '-'}")
            with col3:
                if qtd > 0:
                    if st.button("Vender 1", key=f"sell_{pid}"):
                        try:
                            mark_produto_as_sold(pid, 1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro na venda: {e}")
                if st.button("Editar", key=f"edit_{pid}"):
                    st.session_state["edit_product_id"] = pid
                    st.session_state["edit_mode"] = True
                    st.rerun()
                if st.session_state["role"] == "admin":
                    if st.button("Excluir", key=f"del_{pid}"):
                        try:
                            delete_produto(pid)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")
    st.sidebar.metric("Valor Total em Estoque", format_to_brl(total))

if st.session_state["edit_mode"]:
    show_edit_form()
else:
    menu = st.sidebar.radio("Navegação", ["Listar e Ações", "Cadastrar Novo"])
    if menu == "Cadastrar Novo":
        add_product_form()
    else:
        manage_products_list_actions()
