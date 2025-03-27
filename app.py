from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from admin_routes import admin_bp
from imagem_routes import imagem_bp
from init_db import get_db_connection  # Importa do init_db.py

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mais_segura_e_unica'

app.register_blueprint(admin_bp)
app.register_blueprint(imagem_bp)

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('adega.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rota principal (index)
@app.route('/')
def index():
    if 'user_id' not in session:
        flash('Você precisa fazer login para acessar esta página.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    vinhos = conn.execute('SELECT * FROM vinhos').fetchall()

    is_admin = False
    if 'user_id' in session:
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        if user and user['role'] == 'admin':
            is_admin = True  # Se for admin, define como True

    conn.close()

    return render_template('index.html', vinhos=vinhos, is_admin=is_admin)



# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user:
            if check_password_hash(user['password'], password):
                # Login bem-sucedido: cria a sessão
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['role'] == 'admin'  # Verifica se é admin

                flash('Login realizado com sucesso!', 'success')

                # Redireciona para o painel administrativo se for admin
                if session['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('index'))  # Redireciona para a página principal
            else:
                flash('Senha incorreta!', 'error')
        else:
            flash('Usuário não encontrado!', 'error')

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    return render_template('index.html')


# Rota para logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove o user_id da sessão
    session.pop('username', None)  # Remove o username da sessão
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))  # Redireciona para a página de login

# Rota para a página de criação de conta
@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)',
                         (username, hashed_password))
            conn.commit()
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Nome de usuário já existe!', 'error')
        finally:
            conn.close()

    return render_template('account.html')

# Rota para a página de recuperação de senha
@app.route('/password', methods=['GET', 'POST'])
def password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()

        if user:
            conn.execute('UPDATE usuarios SET password = ? WHERE id = ?',
                         (hashed_password, user['id']))
            conn.commit()
            flash('Senha atualizada com sucesso!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Usuário não encontrado!', 'error')
        conn.close()

    return render_template('password.html')

# Rota para adicionar itens ao carrinho
@app.route('/adicionar/<int:vinho_id>', methods=['POST'])
def adicionar_ao_carrinho(vinho_id):
    if 'carrinho' not in session:
        session['carrinho'] = []

    # Busca o vinho no banco de dados
    conn = get_db_connection()
    vinho = conn.execute('SELECT * FROM vinhos WHERE id = ?', (vinho_id,)).fetchone()
    conn.close()

    if vinho:
        # Verifica se o item já está no carrinho
        item_existente = next((item for item in session['carrinho'] if item['id'] == vinho_id), None)

        if item_existente:
            item_existente['quantidade'] += 1  # Aumenta a quantidade
        else:
            session['carrinho'].append({
                'id': vinho['id'],
                'nome': vinho['nome'],
                'preco': float(vinho['preco']),
                'quantidade': 1
            })

        session.modified = True

        # Retorna o número total de itens no carrinho
        total_itens = sum(item['quantidade'] for item in session['carrinho'])
        return jsonify({'status': 'success', 'total_itens': total_itens})
    else:
        return jsonify({'status': 'error', 'message': 'Vinho não encontrado'}), 404

@app.route('/carrinho')
def ver_carrinho():
    if 'user_id' not in session:  # Verifica se o usuário não está logado
        flash('Você precisa fazer login para acessar esta página.', 'error')
        return redirect(url_for('login'))  # Redireciona para a página de login

    # Inicializa o carrinho como uma lista vazia se não existir
    if 'carrinho' not in session or not isinstance(session['carrinho'], list):
        session['carrinho'] = []

    # Calcula o total do carrinho
    carrinho = []
    total = 0

    for item in session['carrinho']:
        if isinstance(item, dict):
            carrinho.append(item)
            total += item['preco'] * item['quantidade']
        else:
            print(f"Erro: item inválido no carrinho -> {item}")

    return render_template('carrinho.html', carrinho=carrinho, total=total)

@app.route('/calcular_frete', methods=['POST'])
def calcular_frete():
    data = request.get_json()
    cep = data.get('cep')

    # Verifica se o CEP foi fornecido
    if not cep or len(cep) != 8:
        return jsonify({
            'status': 'error',
            'message': 'CEP inválido. O CEP deve ter 8 dígitos.'
        }), 400

    # Aqui você pode integrar com uma API de cálculo de frete
    # Por exemplo, usando a API dos Correios ou outra similar
    # Para este exemplo, vamos usar um valor fixo de frete
    frete = 35.00  # Valor fixo de frete

    return jsonify({
        'status': 'success',
        'frete': frete
    })

@app.route('/carrinho/contador')
def contador_carrinho():
    total_itens = sum(item['quantidade'] for item in session.get('carrinho', []))
    return jsonify({'total_itens': total_itens})


@app.route('/atualizar_quantidade/<int:item_id>', methods=['POST'])
def atualizar_quantidade(item_id):
    nova_quantidade = request.json.get('quantidade', 1)  # Padrão = 1

    if isinstance(nova_quantidade, int) and nova_quantidade > 0:
        if 'carrinho' in session and isinstance(session['carrinho'], list):
            total_itens = 0  # Inicializa o total
            for item in session['carrinho']:
                if isinstance(item, dict) and item.get('id') == item_id:
                    item['quantidade'] = nova_quantidade
                    session.modified = True
                
                # Soma a quantidade de todos os itens no carrinho
                total_itens += item.get('quantidade', 0)

            return jsonify({
                'status': 'success',
                'message': 'Quantidade atualizada com sucesso!',
                'total_itens': total_itens  # Retorna o total atualizado
            })

        return jsonify({'status': 'error', 'message': 'Item não encontrado no carrinho.'}), 404
    else:
        return jsonify({'status': 'error', 'message': 'Quantidade inválida.'}), 400


# Rota para remover um item do carrinho
@app.route('/remover_item/<int:item_id>', methods=['POST'])
def remover_item(item_id):
    if 'carrinho' in session and isinstance(session['carrinho'], list):
        session['carrinho'] = [item for item in session['carrinho'] if isinstance(item, dict) and item.get('id') != item_id]
        session.modified = True
        return jsonify({'status': 'success', 'message': 'Item removido com sucesso!'})
    else:
        return jsonify({'status': 'error', 'message': 'Carrinho não encontrado.'}), 404

# Rota para finalizar a compra
@app.route('/finalizar')
def finalizar_compra():
    session.pop('carrinho', None)
    session.modified = True
    return render_template('finalizar.html')

@app.route('/espumantes')
def espumantes():
    return render_template('espumantes.html')

@app.route('/vinhos')  # Define the missing route
def vinhos():
    return render_template('vinhos.html') 

@app.route('/vinho_branco')
def vinho_branco():
    return render_template('vinho_branco.html')  

@app.route('/vinho_rose')
def vinho_rose():
    return render_template('vinho_rose.html')

@app.route('/vinho_tinto')
def vinho_tinto():
    return render_template('vinho_tinto.html', current_page=1)

@app.route('/vinho_tinto/pagina-2')
def vinho_tinto1():
    return render_template('vinho_tinto1.html', current_page=2)

@app.route('/vinho_tinto/pagina-3')
def vinho_tinto2():
    return render_template('vinho_tinto2.html', current_page=3)

@app.route('/embalagens')
def embalagens():
    return render_template('embalagens.html', current_page=1)

@app.route('/embalagens2')
def embalagens2():
    return render_template('embalagens2.html', current_page=2)

@app.route('/novidades')
def novidades():
    return render_template('novidades.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/quem-somos')
def quem_somos():
    return render_template('quem_somos.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/vinho_rose')
def vinhos_rose():
    return render_template('vinho_rose.html')



if __name__ == '__main__':
    app.run(debug=True)