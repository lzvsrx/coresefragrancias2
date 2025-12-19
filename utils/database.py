# ====================================================================
# ARQUIVO: utils/database.py
# Sistema completo de Estoque + Usuários + CSV + PDF
# ====================================================================

import sqlite3
import os
import hashlib
import csv
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ====================================================================
# CONFIGURAÇÕES
# ====================================================================

DATABASE_DIR = "data"
ASSETS_DIR = "assets"
DATABASE = os.path.join(DATABASE_DIR, "estoque.db")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ====================================================================
# LISTAS DE CATEGORIAS (ATUALIZADAS)
# ====================================================================

MARCAS = [
    "Eudora", "O Boticário", "Jequiti", "Avon", "Mary Kay", "Natura",
    "Oui-Original-Unique-Individuel", "Pierre Alexander",
    "Tupperware", "Outra"
]

ESTILOS = [
    "Perfumaria", "Skincare", "Cabelo", "Corpo e Banho", "Make",
    "Masculinos", "Femininos Nina Secrets", "Marcas", "Infantil",
    "Casa", "Solar", "Maquiage", "Teen", "Kits e Presentes",
    "Cuidados com o Corpo", "Lançamentos",
    "Acessórios de Casa", "Outro"
]

TIPOS = [
    "Perfumaria masculina", "Perfumaria feminina", "Body splash",
    "Body spray", "Eau de parfum", "Desodorantes",
    "Perfumaria infantil", "Perfumaria vegana", "Família olfativa",
    "Clareador de manchas", "Anti-idade", "Protetor solar facial",
    "Rosto", "Tratamento para o rosto", "Acne", "Limpeza",
    "Esfoliante", "Tônico facial",
    "Kits de tratamento", "Tratamento para cabelos", "Shampoo",
    "Condicionador", "Leave-in e Creme para Pentear",
    "Finalizador", "Modelador", "Acessórios",
    "Kits e looks", "Boca", "Olhos", "Pincéis", "Paleta",
    "Unhas", "Sobrancelhas",
    "Hidratante", "Cuidados pós-banho", "Cuidados para o banho",
    "Barba", "Óleo corporal", "Cuidados íntimos", "Unissex",
    "Bronzeamento",
    "Protetor solar", "Depilação", "Mãos", "Lábios", "Pés",
    "Pós sol", "Protetor solar corporal",
    "Colônias", "Estojo", "Sabonetes", "Sabonete líquido",
    "Sabonete em barra",
    "Creme hidratante para as mãos",
    "Creme hidratante para os pés",
    "Miniseries", "Kits de perfumes", "Antissinais",
    "Máscara", "Creme bisnaga",
    "Roll On Fragranciado", "Roll On On Duty",
    "Shampoo 2 em 1", "Spray corporal",
    "Booster de Tratamento", "Creme para Pentear",
    "Óleo de Tratamento", "Pré-shampoo",
    "Sérum de Tratamento", "Shampoo e Condicionador",
    "Garrafas", "Armazenamentos", "Micro-ondas",
    "Servir", "Preparo",
    "Lazer/Outdoor", "Presentes", "Outro"
]

# ====================================================================
# FUNÇÕES UTILITÁRIAS
# ====================================================================

def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default

def safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except:
        return default

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ====================================================================
# CRIAÇÃO DAS TABELAS
# ====================================================================

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            marca TEXT,
            estilo TEXT,
            tipo TEXT,
            foto TEXT,
            data_validade TEXT,
            vendido INTEGER DEFAULT 0,
            data_ultima_venda TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", hash_password("123"), "admin")
        )
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()

create_tables()

# ====================================================================
# PRODUTOS
# ====================================================================

def add_produto(nome, preco, quantidade, marca, estilo, tipo, foto=None, data_validade=None):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO produtos
        (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade))
    conn.commit()
    conn.close()

def get_all_produtos(include_sold=True):
    conn = get_db_connection()
    cur = conn.cursor()
    if include_sold:
        cur.execute("SELECT * FROM produtos ORDER BY nome")
    else:
        cur.execute("SELECT * FROM produtos WHERE quantidade > 0 ORDER BY nome")
    data = [dict(r) for r in cur.fetchall()]
    conn.close()
    return data

def get_produto_by_id(pid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM produtos WHERE id=?", (pid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_produto(pid, nome, preco, quantidade, marca, estilo, tipo, foto, data_validade):
    conn = get_db_connection()
    conn.execute("""
        UPDATE produtos
        SET nome=?, preco=?, quantidade=?, marca=?, estilo=?, tipo=?, foto=?, data_validade=?
        WHERE id=?
    """, (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade, pid))
    conn.commit()
    conn.close()

def delete_produto(pid):
    conn = get_db_connection()
    conn.execute("DELETE FROM produtos WHERE id=?", (pid,))
    conn.commit()
    conn.close()
def mark_produto_as_sold(produto_id, quantidade_vendida=1):
    """
    Marca um produto como vendido e atualiza o estoque.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT quantidade FROM produtos WHERE id=?", (produto_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        raise ValueError("Produto não encontrado")

    estoque_atual = row["quantidade"]

    if estoque_atual < quantidade_vendida:
        conn.close()
        raise ValueError("Estoque insuficiente")

    nova_qtd = estoque_atual - quantidade_vendida

    cur.execute("""
        UPDATE produtos
        SET quantidade = ?,
            vendido = 1,
            data_ultima_venda = ?
        WHERE id = ?
    """, (
        nova_qtd,
        datetime.now().isoformat(),
        produto_id
    ))

    conn.commit()
    conn.close()
    return True
# ====================================================================
# USUÁRIOS (CORRIGIDO – ERRO RESOLVIDO)
# ====================================================================

def add_user(username, password, role="staff"):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users ORDER BY role DESC, username")
    users = [dict(r) for r in cur.fetchall()]
    conn.close()
    return users

def update_user_role(user_id, new_role):
    conn = get_db_connection()
    conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()
    conn.close()
    return True

def delete_user(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True
def check_user_login(username, password):
    """
    Valida login do usuário.
    Retorna o dicionário do usuário se estiver correto, senão None.
    """
    user = get_user(username)
    if not user:
        return None

    if user["password"] == hash_password(password):
        return user

    return None

# ====================================================================
# CSV
# ====================================================================

def export_produtos_to_csv_content():
    produtos = get_all_produtos()
    if not produtos:
        return ""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=produtos[0].keys(), delimiter=";")
    writer.writeheader()
    writer.writerows(produtos)
    return buffer.getvalue()
def import_produtos_from_csv_buffer(file_buffer):
    """
    Importa produtos a partir de um arquivo CSV enviado (Streamlit upload).
    Retorna a quantidade de registros importados.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    content = file_buffer.getvalue().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")

    count = 0
    conn.execute("BEGIN")

    try:
        for r in reader:
            if not r.get("nome"):
                continue

            cur.execute("""
                INSERT INTO produtos
                (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade, vendido, data_ultima_venda)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("nome"),
                safe_float(r.get("preco")),
                safe_int(r.get("quantidade")),
                r.get("marca"),
                r.get("estilo"),
                r.get("tipo"),
                r.get("foto"),
                r.get("data_validade"),
                safe_int(r.get("vendido")),
                r.get("data_ultima_venda")
            ))
            count += 1

        conn.commit()
        return count

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()

# ====================================================================
# PDF
# ====================================================================

def generate_stock_pdf_bytes():
    produtos = get_all_produtos(include_sold=False)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(cm, y, "Relatório de Estoque - Cores e Fragrâncias")
    y -= 30

    total = 0.0
    c.setFont("Helvetica", 10)
    for p in produtos:
        if y < 40:
            c.showPage()
            y = h - 50
        total += p["preco"] * p["quantidade"]
        c.drawString(cm, y, f"{p['nome']} | Qtd: {p['quantidade']} | R$ {p['preco']:.2f}")
        y -= 15

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(cm, y, f"TOTAL: R$ {total:.2f}".replace(".", ","))

    c.save()
    buf.seek(0)
    return buf.getvalue()