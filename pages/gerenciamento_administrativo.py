# main.py
import streamlit as st
import os
from datetime import datetime
from utils.database import (
    create_tables,
    get_all_produtos,
    add_user,
    get_user,
    get_all_users,
    hash_password,
    update_user_role,
    delete_user,
)

# Configuração da página
st.set_page_config(page_title="Cores e Fragrâncias", page_icon="🌸", layout="wide")

# Cria tabelas se não existirem
create_tables()

# --- Função para carregar CSS ---
def load_css(file_name):
    """Carrega e aplica o CSS personalizado, forçando a codificação UTF-8."""
    if not os.path.exists(file_name):
        st.warning(f"O arquivo CSS '{file_name}' não foi encontrado.")
        return
    try:
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {e}")

# Carrega CSS
load_css("style.css")

# Inicializa estados de sessão
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = "guest"
if "username" not in st.session_state:
    st.session_state["username"] = None

# --- HEADER PRINCIPAL ---
st.title("🌸 Cores e Fragrâncias by Berenice")
st.markdown("---")

st.write("Use o menu abaixo para acessar funcionalidades:")

col1, col2 = st.columns(2)
with col1:
    st.metric("Produtos cadastrados", len(get_all_produtos()))
with col2:
    st.metric("Status", "Online ✅")

st.caption(f"© {datetime.now().year} Cores e Fragrâncias")
st.markdown("---")

# --- SIDEBAR: STATUS E LOGOUT ---
if st.session_state.get("logged_in"):
    st.sidebar.success(
        f"👤 Logado como: **{st.session_state['username']}** "
        f"({st.session_state['role'].title()})"
    )
    if st.sidebar.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["role"] = "guest"
        st.success("Sessão encerrada com sucesso!")
        st.rerun()

# --- ÁREA ADMINISTRATIVA ---
st.header("🔐 Área Administrativa")
st.markdown("**Faça login ou cadastre um novo usuário normal ou administrador abaixo.**")

# Menu principal
option = st.selectbox(
    "Escolha uma ação",
    ["Login", "Cadastrar Novo Usuário", "Gerenciar Contas (Admins)"]
)

# ---------- 1. LOGIN ----------
if option == "Login":
    st.subheader("🔑 Login")
    username = st.text_input("Nome de usuário", key="login_user")
    password = st.text_input("Senha", type="password", key="login_pass")
    
    if st.button("Entrar", type="primary"):
        if not username or not password:
            st.error("Preencha usuário e senha.")
        else:
            user = get_user(username)
            if not user:
                st.error("❌ Usuário não encontrado.")
            elif hash_password(password) == user.get("password"):
                st.success(f"✅ Bem-vindo(a), **{username}** ({user.get('role').title()})!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user.get('role')
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")

    st.info("👆 **Admin padrão:** `admin` / `123`")

# ---------- 2. CADASTRO ----------
elif option == "Cadastrar Novo Usuário":
    st.subheader("➕ Cadastrar Novo Usuário")
    
    col1, col2 = st.columns(2)
    with col1:
        new_username = st.text_input("Nome de usuário", key="reg_user")
        new_password = st.text_input("Senha", type="password", key="reg_pass")
    with col2:
        confirm_password = st.text_input("Confirme senha", type="password", key="reg_conf")
        role = st.selectbox(
            "Tipo de usuário",
            ["user", "staff", "admin"],
            format_func=lambda x: {
                "user": "👤 Usuário Normal",
                "staff": "🧑‍💼 Funcionário",
                "admin": "👑 Administrador"
            }[x]
        )
    
    if st.button("Criar Usuário", type="primary"):
        if not all([new_username, new_password, confirm_password]):
            st.error("❌ Preencha todos os campos.")
        elif new_password != confirm_password:
            st.error("❌ As senhas não coincidem.")
        elif get_user(new_username):
            st.error("❌ Nome de usuário já existe.")
        else:
            if add_user(new_username, new_password, role=role):
                role_name = {"user": "Usuário Normal", "staff": "Funcionário", "admin": "Administrador"}[role]
                st.success(f"✅ Usuário **'{new_username}'** criado como **{role_name}**! Faça login agora.")
                st.rerun()
            else:
                st.error("❌ Erro ao criar usuário.")

# ---------- 3. GERENCIAR CONTAS (APENAS ADMIN) ----------
elif option == "Gerenciar Contas (Admins)":
    st.subheader("👥 Gerenciar Usuários")
    
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
        st.error(
            "🚫 **Apenas administradores** podem gerenciar contas. "
            "Faça login como `admin` (senha: `123`)"
        )
    else:
        # Lista de usuários
        users = get_all_users()
        if not users:
            st.info("Nenhum usuário cadastrado ainda.")
            st.stop()
        
        st.subheader(f"📋 Usuários cadastrados ({len(users)})")
        
        for user in users:
            col1, col2, col3, col4 = st.columns([3, 1, 1.5, 1])
            
            with col1:
                role_emoji = {"admin": "👑", "staff": "🧑‍💼", "user": "👤"}.get(user["role"], "❓")
                st.write(f"**{user['username']}** {role_emoji} *({user['role'].title()})*")
            
            with col2:
                if st.button("✏️ Editar", key=f"edit_{user['id']}"):
                    st.session_state["editing_user"] = user["id"]
                    st.rerun()
            
            with col3:
                if st.button("🔄 Role", key=f"role_{user['id']}"):
                    current_role = user["role"]
                    new_role = "admin" if current_role != "admin" else "user"
                    if update_user_role(user["id"], new_role):
                        st.success(f"✅ Role de **{user['username']}** alterado para **{new_role.title()}**")
                        st.rerun()
            
            with col4:
                if st.button("🗑️ Del", key=f"del_{user['id']}"):
                    st.warning(f"Tem certeza que quer excluir **{user['username']}**?")
                    if st.button("CONFIRMAR EXCLUSÃO", key=f"confirm_del_{user['id']}"):
                        if delete_user(user["id"]):
                            st.success(f"✅ Usuário **{user['username']}** excluído!")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao excluir usuário.")
        
        # Edição avançada (se clicou em editar)
        if st.session_state.get("editing_user"):
            editing_id = st.session_state["editing_user"]
            user_to_edit = next((u for u in users if u["id"] == editing_id), None)
            if user_to_edit:
                st.subheader(f"✏️ Editando: {user_to_edit['username']}")
                new_role = st.selectbox(
                    "Novo papel",
                    ["user", "staff", "admin"],
                    index=["user", "staff", "admin"].index(user_to_edit["role"]),
                    key=f"edit_role_{editing_id}"
                )
                if st.button("Salvar Alterações", key=f"save_edit_{editing_id}"):
                    if update_user_role(editing_id, new_role):
                        st.success("✅ Alterações salvas!")
                        del st.session_state["editing_user"]
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar.")
        
        st.info("💡 **Dica:** Use '🔄 Role' para alternar rapidamente entre Admin/Usuário Normal")

