import streamlit as st
from datetime import datetime
from utils.database import (
    add_produto, get_all_produtos, mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS, safe_int, safe_float
)

st.set_page_config(page_title="Chatbot Estoque", page_icon="🤖", layout="wide")

def load_css(file_name="style.css"):
    import os
    if os.path.exists(file_name):
        try:
            with open(file_name, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

load_css("style.css")

if not st.session_state.get("logged_in"):
    st.error("Acesso negado. Faça login na Área Administrativa.")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "assistant", "content": "Olá! Sou o assistente de estoque. Digite `ajuda` para ver comandos."}
    ]
if "chat_state" not in st.session_state:
    st.session_state["chat_state"] = {"step": "idle", "data": {}}

st.title("🤖 Chatbot Operacional")
st.caption("Gerencie estoque por comandos de texto.")

def process_command(user_input: str) -> str:
    text = user_input.strip().lower()
    state = st.session_state["chat_state"]

    if text == "cancelar":
        st.session_state["chat_state"] = {"step": "idle", "data": {}}
        return "Operação cancelada. Digite `ajuda` para ver o que posso fazer."

    if state["step"] == "idle":
        if "ajuda" in text:
            return (
                "Comandos:\n"
                "- `adicionar produto`\n"
                "- `estoque`\n"
                "- `vender [ID]`\n"
                "- `cancelar`"
            )
        if "adicionar produto" in text:
            state["step"] = "add_nome"
            return "Qual o nome do novo produto?"
        if text.startswith("vender"):
            partes = text.split()
            if len(partes) > 1 and partes[1].isdigit():
                try:
                    mark_produto_as_sold(int(partes[1]), 1)
                    return f"Venda registrada para ID {partes[1]}."
                except Exception as e:
                    return f"Erro na venda: {e}"
            else:
                state["step"] = "vender_id"
                return "Informe o ID do produto para vender 1 unidade."
        if "estoque" in text:
            prods = get_all_produtos(include_sold=False)
            if not prods:
                return "Nenhum produto em estoque."
            resp = "Itens em estoque:\n"
            for p in prods[:10]:
                resp += f"- ID {p['id']}: {p['nome']} ({p['quantidade']} un)\n"
            return resp

    if state["step"] == "vender_id":
        if text.isdigit():
            try:
                mark_produto_as_sold(int(text), 1)
                st.session_state["chat_state"] = {"step": "idle", "data": {}}
                return f"Venda registrada para ID {text}."
            except Exception as e:
                return f"Erro na venda: {e}"
        return "ID inválido. Digite apenas o número ou `cancelar`."

    if state["step"] == "add_nome":
        state["data"]["nome"] = user_input.strip()
        state["step"] = "add_preco"
        return "Preço do produto? (ex: 59.90)"

    if state["step"] == "add_preco":
        try:
            preco = safe_float(user_input.replace(",", "."))
            if preco <= 0:
                return "Preço deve ser maior que zero."
            state["data"]["preco"] = preco
            state["step"] = "add_qtd"
            return "Quantidade inicial?"
        except Exception:
            return "Preço inválido. Ex: 59.90"

    if state["step"] == "add_qtd":
        try:
            qtd = safe_int(user_input)
            if qtd < 0:
                return "Quantidade não pode ser negativa."
            state["data"]["quantidade"] = qtd
            state["step"] = "add_marca"
            return f"Marca? Sugestões: {', '.join(MARCAS[:5])}"
        except Exception:
            return "Quantidade inválida. Digite um número inteiro."

    if state["step"] == "add_marca":
        if user_input.strip() in MARCAS:
            state["data"]["marca"] = user_input.strip()
            state["step"] = "add_estilo"
            return "Estilo? (ex: Perfumaria, Skincare)"
        return "Marca não reconhecida. Use uma das cadastradas ou `cancelar`."

    if state["step"] == "add_estilo":
        if user_input.strip() in ESTILOS:
            state["data"]["estilo"] = user_input.strip()
            state["step"] = "add_tipo"
            return "Tipo? (ex: Perfumaria feminina)"
        return "Estilo inválido. Tente novamente."

    if state["step"] == "add_tipo":
        if user_input.strip() in TIPOS:
            state["data"]["tipo"] = user_input.strip()
            state["step"] = "add_finaliza"
            return "Cadastro quase pronto. Confirme com `ok` ou `cancelar`."
        return "Tipo inválido. Tente novamente."

    if state["step"] == "add_finaliza":
        if text == "ok":
            d = state["data"]
            try:
                add_produto(d["nome"], d["preco"], d["quantidade"], d["marca"], d["estilo"], d["tipo"], None, None)
                st.session_state["chat_state"] = {"step": "idle", "data": {}}
                return f"Produto '{d['nome']}' cadastrado com sucesso."
            except Exception as e:
                return f"Erro ao salvar no banco: {e}"
        return "Digite `ok` para confirmar ou `cancelar`."

    return "Não entendi. Digite `ajuda` para ver os comandos."

for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite um comando..."):
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    resposta = process_command(prompt)
    st.session_state["chat_history"].append({"role": "assistant", "content": resposta})
    with st.chat_message("assistant"):
        st.markdown(resposta)
