import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('adega.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Ativa chaves estrangeiras
    return conn

def verificar_esquema():
    conn = get_db_connection()
    try:
        # Verifica se a coluna estoque existe
        colunas = conn.execute("PRAGMA table_info(produtos)").fetchall()
        colunas_existentes = [col[1] for col in colunas]
        
        if 'estoque' not in colunas_existentes:
            conn.execute('ALTER TABLE produtos ADD COLUMN estoque INTEGER DEFAULT 0')
            conn.commit()
            print("Coluna 'estoque' adicionada à tabela produtos")
            
    except sqlite3.Error as e:
        print(f"Erro ao verificar esquema: {e}")
    finally:
        conn.close()

try:
    conn = get_db_connection()
    c = conn.cursor()

    # Tabela de usuários (DEVE vir antes de 'pedidos' por causa da FK)
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            reset_token TEXT,
            reset_token_expires DATETIME,
            role TEXT DEFAULT 'user',
            imagem TEXT NULL
        )
    ''')

    # Tabela de vinhos
    c.execute('''
        CREATE TABLE IF NOT EXISTS vinhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            imagem TEXT NOT NULL,
            descricao TEXT
        )
    ''')

    # Tabela de pedidos
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            endereco TEXT NOT NULL,
            metodo_pagamento TEXT NOT NULL,
            status TEXT DEFAULT 'pendente',
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )
    ''')

    # Tabela de itens_pedido
    c.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            vinho_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (vinho_id) REFERENCES vinhos(id)
        )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        imagem TEXT NOT NULL,
        descricao TEXT,
        categoria TEXT,
        estoque INTEGER DEFAULT 0
    )
''')    

    # Verificar e atualizar esquema se necessário
    verificar_esquema()

    # Inserir vinhos de exemplo
    vinhos_exemplo = [
        # ('Vinho Tinto', 50.00, 'vinho_tinto.jpg', 'Um vinho tinto encorpado com notas de frutas vermelhas.'),
        # ('Vinho Branco', 40.00, 'vinho_branco.jpg', 'Um vinho branco leve e refrescante.'),
        # ('Vinho Rosé', 35.00, 'vinho_rose.jpg', 'Um vinho rosé suave e frutado.')
    ]
    for vinho in vinhos_exemplo:
        c.execute("INSERT OR IGNORE INTO vinhos (nome, preco, imagem, descricao) VALUES (?, ?, ?, ?)", vinho)

    # Inserir usuários de exemplo (COM EMAIL)
    usuarios_exemplo = [
        ('admin', 'admin@example.com', generate_password_hash('admin123'), 'admin'),
        ('user1', 'user1@example.com', generate_password_hash('user123'), 'user'),
        ('user2', 'user2@example.com', generate_password_hash('user456'), 'user')
    ]
    for user in usuarios_exemplo:
        c.execute('''
            INSERT OR IGNORE INTO usuarios (username, email, password, role) 
            VALUES (?, ?, ?, ?)
        ''', user)

    # E alguns dados de exemplo
    produtos_exemplo = [
        ('Embalagem cilíndrica em papelão branco', 0, 'product-3.jpg', 'Embalagem cilíndrica em papelão branco para garrafas', 'embalagem', 0),
        ('Caixa de papelão preto para 1 garrafa Luiz Argenta', 0, 'product-1.jpg', 'Caixa de papelão preto para 1 garrafa', 'embalagem', 0),
        ('Caixa de papelão preto para 2 garrafas Luiz Argenta', 0, 'product-2.jpg', 'Caixa de papelão preto para 2 garrafas', 'embalagem', 0),
        ('Embalagem cilíndrica em papelão preto', 0, 'product-4.jpg', 'Embalagem cilíndrica em papelão preto para garrafas', 'embalagem', 0),
        ('Embalagem cilíndrica em madeira decorada', 0, 'product-5.jpg', 'Embalagem cilíndrica em madeira decorada', 'embalagem', 0),
        ('Embalagem de couro Montana marrom, reta, com alça de couro', 0, 'product-6.jpg', 'Embalagem de couro Montana marrom com alça', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Aquário', 0, 'product-7.jpg', 'Embalagem temática do signo Aquário', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Áries', 0, 'product-8.jpg', 'Embalagem temática do signo Áries', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Câncer', 0, 'product-9.jpg', 'Embalagem temática do signo Câncer', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Capricórnio', 0, 'product-10.jpg', 'Embalagem temática do signo Capricórnio', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Escorpião', 0, 'product-11.jpg', 'Embalagem temática do signo Escorpião', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Gêmeos', 0, 'product-12.jpg', 'Embalagem temática do signo Gêmeos', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Leão', 0, 'product-13.jpg', 'Embalagem temática do signo Leão', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Libra', 0, 'product-14.jpg', 'Embalagem temática do signo Libra', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Peixes', 0, 'product-15.jpg', 'Embalagem temática do signo Peixes', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Sagitário', 0, 'product-16.jpg', 'Embalagem temática do signo Sagitário', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Touro', 0, 'product-17.jpg', 'Embalagem temática do signo Touro', 'embalagem', 0),
        ('Embalagem em lonita com alças de couro sintético, signo Virgem', 0, 'product-18.jpg', 'Embalagem temática do signo Virgem', 'embalagem', 0)
    ]
    for produto in produtos_exemplo:
        c.execute("""
            INSERT OR IGNORE INTO produtos 
            (nome, preco, imagem, descricao, categoria, estoque) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, produto)

    conn.commit()
    print("Banco de dados configurado com sucesso!")

except sqlite3.Error as e:
    print(f"Erro no banco de dados: {e}")

finally:
    if conn:
        conn.close()