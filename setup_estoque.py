# setup_estoque.py
import sqlite3

DB = "estoque.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# =========================
# CRIAÇÃO DAS TABELAS
# =========================

# Tabela de Usuários
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha TEXT
)
""")

# Tabela de Produtos
cur.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE,
    numero_ca TEXT,
    estoque_minimo INTEGER DEFAULT 0
)
""")

# Estoque por Setores (Centralizado no ALMOXARIFADO)
cur.execute("""
CREATE TABLE IF NOT EXISTS estoque_setores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT NOT NULL,
    setor TEXT NOT NULL,
    quantidade INTEGER DEFAULT 0,
    UNIQUE(produto, setor)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS embalagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS entradas_unidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    quantidade INTEGER,
    usuario TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_movimentacao TEXT DEFAULT 'ENTRADA'
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS saídas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    quantidade INTEGER,
    observacao TEXT,
    usuario TEXT,
    responsavel TEXT, 
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_movimentacao TEXT DEFAULT 'SAIDA',
    data_hora_saida DATETIME, -- <--- ADICIONE ESTA LINHA AQUI
    FOREIGN KEY(produto_id) REFERENCES produtos(id)
)
""")

# NOVA TABELA: logs_admin para rastrear edições do lápis
cur.execute("""
CREATE TABLE IF NOT EXISTS logs_admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operador TEXT,
    acao TEXT,
    detalhe TEXT
)
""")

# =========================
# MIGRAÇÕES E SEGURANÇA
# =========================

# Garante que a coluna 'responsavel' exista para rastreabilidade
try:
    cur.execute("ALTER TABLE saídas ADD COLUMN responsavel TEXT")
    print("📢 Coluna 'responsavel' garantida.")
except: pass

# Garante coluna de tipo para entradas antigas
try:
    cur.execute("ALTER TABLE entradas_unidade ADD COLUMN tipo_movimentacao TEXT DEFAULT 'ENTRADA'")
except: pass

# Cria usuário admin padrão para acesso às funções de edição
cur.execute("INSERT OR IGNORE INTO usuarios (username, senha) VALUES (?,?)", ("admin", "123"))

conn.commit()
conn.close()

print("-" * 30)
print("✅ SETUP ATUALIZADO COM SUCESSO!")
print("✅ Tabela 'logs_admin' pronta para registro de edições.")
print("✅ Sistema pronto para o novo fluxo do Diário de Bordo.")
print("-" * 30)