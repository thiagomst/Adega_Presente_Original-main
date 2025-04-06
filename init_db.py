import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('adega.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Ativa chaves estrangeiras
    return conn

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

    # Inserir vinhos de exemplo
    vinhos_exemplo = [
        ('Vinho Tinto', 50.00, 'vinho_tinto.jpg', 'Um vinho tinto encorpado com notas de frutas vermelhas.'),
        ('Vinho Branco', 40.00, 'vinho_branco.jpg', 'Um vinho branco leve e refrescante.'),
        ('Vinho Rosé', 35.00, 'vinho_rose.jpg', 'Um vinho rosé suave e frutado.')
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

    conn.commit()
    print("Banco de dados configurado com sucesso!")

except sqlite3.Error as e:
    print(f"Erro no banco de dados: {e}")

finally:
    if conn:
        conn.close()