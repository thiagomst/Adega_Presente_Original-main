import sqlite3
from werkzeug.security import generate_password_hash

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('adega.db')
    conn.row_factory = sqlite3.Row  # Retorna as linhas como dicionários
    return conn

try:
    conn = get_db_connection()
    c = conn.cursor()

    # Criar tabela de vinhos com a coluna 'imagem' e 'descricao'
    c.execute('''
        CREATE TABLE IF NOT EXISTS vinhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            imagem TEXT NOT NULL,
            descricao TEXT  -- Nova coluna
        )
    ''')
    print("Tabela 'vinhos' criada com sucesso ou já existente.")

    # Inserir vinhos de exemplo apenas se não existirem
    vinhos_exemplo = [
        ('Vinho Tinto', 50.00, 'vinho_tinto.jpg', 'Um vinho tinto encorpado com notas de frutas vermelhas.'),
        ('Vinho Branco', 40.00, 'vinho_branco.jpg', 'Um vinho branco leve e refrescante.'),
        ('Vinho Rosé', 35.00, 'vinho_rose.jpg', 'Um vinho rosé suave e frutado.')
    ]

    for vinho in vinhos_exemplo:
        c.execute("SELECT COUNT(*) FROM vinhos WHERE nome = ?", (vinho[0],))
        if c.fetchone()[0] == 0:  # Só insere se não existir
            c.execute("INSERT INTO vinhos (nome, preco, imagem, descricao) VALUES (?, ?, ?, ?)", vinho)

    print("Vinhos de exemplo inseridos com sucesso.")

    # Criar tabela de usuários com o campo 'role'
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',  -- Campo para definir o papel do usuário
            imagem BLOB NULL  -- Nova coluna para salvar imagens (pode ser nula)
        )
    ''')
    print("Tabela 'usuarios' criada com sucesso ou já existente.")

    # Inserir usuários de exemplo, evitando duplicatas
    usuarios_exemplo = [
        ('admin', generate_password_hash('admin123'), 'admin'),
        ('user1', generate_password_hash('user123'), 'user'),
        ('user2', generate_password_hash('user456'), 'user')
    ]

    for usuario in usuarios_exemplo:
        c.execute("SELECT COUNT(*) FROM usuarios WHERE username = ?", (usuario[0],))
        if c.fetchone()[0] == 0:  # Só insere se o username não existir
            c.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)", usuario)

    print("Usuários de exemplo inseridos com sucesso.")

    conn.commit()

except sqlite3.Error as e:
    print(f"Erro ao acessar o banco de dados: {e}")

finally:
    if conn:
        conn.close()
        print("Conexão com o banco de dados fechada.")
