from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from admin_routes import admin_bp
from imagem_routes import imagem_bp
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta
import re
from init_db import get_db_connection 

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mais_segura_e_unica'

app.register_blueprint(admin_bp)
app.register_blueprint(imagem_bp)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thiagomonsuet@gmail.com'
app.config['MAIL_PASSWORD'] = 'zlko lorv qnyg szat'
app.config['MAIL_DEFAULT_SENDER'] = 'thiagomonsuet@gmail.com'

mail = Mail(app)
def get_db_connection():
    conn = sqlite3.connect('adega.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rota principal
@app.route('/')
def index():
    conn = get_db_connection()
    vinhos = conn.execute('SELECT * FROM vinhos').fetchall()

    is_admin = False
    if 'user_id' in session:
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        if user and user['role'] == 'admin':
            is_admin = True

    conn.close()
    return render_template('index.html', vinhos=vinhos, is_admin=is_admin)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('user_input', '').strip()
        password = request.form.get('password', '')

        if not user_input or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        try:
            user = conn.execute('''
                SELECT * FROM usuarios 
                WHERE username = ? OR email = ?
            ''', (user_input, user_input)).fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['role'] == 'admin'

                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('admin_dashboard' if session['is_admin'] else 'index'))
            else:
                flash('Credenciais inválidas!', 'error')
        except Exception as e:
            app.logger.error(f"Erro no login: {str(e)}")
            flash('Ocorreu um erro ao processar seu login.', 'error')
        finally:
            conn.close()

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
    session.pop('user_id', None)  
    session.pop('username', None) 
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))  # Redireciona para a página de login

# Sistema de Cadastro
@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validações
        if not all([username, email, password, confirm_password]):
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('account.html')

        if password != confirm_password:
            flash('As senhas não coincidem!', 'error')
            return render_template('account.html')

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('E-mail inválido!', 'error')
            return render_template('account.html')

        if len(password) < 8:
            flash('A senha deve ter pelo menos 8 caracteres!', 'error')
            return render_template('account.html')

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO usuarios (username, email, password) 
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            conn.commit()
            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Nome de usuário ou e-mail já existe!', 'error')
        except Exception as e:
            app.logger.error(f"Erro no cadastro: {str(e)}")
            flash('Ocorreu um erro ao criar sua conta.', 'error')
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

import secrets

# Sistema de Recuperação de Senha
@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Por favor, informe um e-mail válido.', 'error')
            return render_template('password_reset.html')

        conn = get_db_connection()
        try:
            user = conn.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
            
            if not user:
                flash('E-mail não encontrado em nosso sistema.', 'error')
                return render_template('password_reset.html')

            # Gera token e define expiração (1 hora a partir de agora)
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)  # Usando UTC
            
            # Atualiza o usuário com token e expiração
            conn.execute('''
                UPDATE usuarios 
                SET reset_token = ?, 
                    reset_token_expires = ?
                WHERE id = ?
            ''', (token, expires_at, user['id']))
            conn.commit()

            # Prepara e-mail
            reset_url = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message(
                    "Redefinição de Senha - Sua Adega",
                    recipients=[email],
                    body=f'''Para redefinir sua senha, clique no link:
{reset_url}

Este link expira em 1 hora.'''
                )
                mail.send(msg)
                flash('E-mail de recuperação enviado! Verifique sua caixa de entrada.', 'success')
            except Exception as e:
                print(f"ERRO AO ENVIAR E-MAIL: {str(e)}")
                flash('Erro ao enviar e-mail. Por favor, tente novamente mais tarde.', 'error')
                
        except Exception as e:
            print(f"ERRO NO BANCO DE DADOS: {str(e)}")
            flash('Ocorreu um erro ao processar sua solicitação.', 'error')
        finally:
            conn.close()

    return render_template('password_reset.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    try:
        # Verifica se o token existe e não expirou (comparando com UTC agora)
        user = conn.execute('''
            SELECT id, reset_token_expires 
            FROM usuarios 
            WHERE reset_token = ? 
            AND reset_token_expires > ?
        ''', (token, datetime.utcnow())).fetchone()  # Compare com UTC

        if not user:
            flash('Link inválido ou expirado. Solicite um novo.', 'error')
            return redirect(url_for('password_reset'))

        if request.method == 'POST':
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not new_password or len(new_password) < 8:
                flash('A senha deve ter pelo menos 8 caracteres!', 'error')
                return render_template('reset_password.html', token=token)

            if new_password != confirm_password:
                flash('As senhas não coincidem!', 'error')
                return render_template('reset_password.html', token=token)

            # Atualiza a senha e limpa o token
            hashed_password = generate_password_hash(new_password)
            conn.execute('''
                UPDATE usuarios 
                SET password = ?,
                    reset_token = NULL,
                    reset_token_expires = NULL
                WHERE id = ?
            ''', (hashed_password, user['id']))
            conn.commit()
            flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('login'))

    except Exception as e:
        app.logger.error(f"Erro na redefinição de senha: {str(e)}")
        flash('Ocorreu um erro ao redefinir sua senha.', 'error')
    finally:
        conn.close()

    return render_template('reset_password.html', token=token)


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

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():

    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa fazer login ou se cadastrar para finalizar a compra.', 'warning')
        return redirect(url_for('login'))  # Redireciona para login

    # Se o carrinho estiver vazio, redireciona de volta
    if 'carrinho' not in session or not session['carrinho']:
        flash('Seu carrinho está vazio!', 'error')
        return redirect(url_for('ver_carrinho'))

    if request.method == 'POST':
        # Processar dados do formulário (endereço, pagamento, etc.)
        endereco = request.form.get('endereco')
        metodo_pagamento = request.form.get('pagamento')

        # Aqui você pode salvar a compra no banco de dados
        try:
            conn = get_db_connection()
            # Insere o pedido na tabela de pedidos
            conn.execute(
                'INSERT INTO pedidos (user_id, endereco, metodo_pagamento, status) VALUES (?, ?, ?, ?)',
                (session['user_id'], endereco, metodo_pagamento, 'pendente')
            )
            pedido_id = conn.lastrowid  # Pega o ID do pedido recém-criado

            # Insere os itens do carrinho na tabela de itens_pedido
            for item in session['carrinho']:
                conn.execute(
                    'INSERT INTO itens_pedido (pedido_id, vinho_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)',
                    (pedido_id, item['id'], item['quantidade'], item['preco'])
                )

            conn.commit()
            conn.close()

            # Limpa o carrinho após a compra
            session.pop('carrinho', None)
            session.modified = True

            flash('Compra finalizada com sucesso!', 'success')
            return redirect(url_for('finalizar_compra'))  # Redireciona para a página de confirmação

        except Exception as e:
            flash(f'Ocorreu um erro ao processar seu pedido: {str(e)}', 'error')
            return redirect(url_for('checkout'))

    # Se for GET, mostra o formulário de checkout
    return render_template('checkout.html')

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
    
@app.route('/debug_tokens')
def debug_tokens():
    if not app.debug:
        return "Acesso somente em modo desenvolvimento", 403
        
    conn = get_db_connection()
    tokens = conn.execute('''
        SELECT id, email, reset_token, reset_token_expires 
        FROM usuarios 
        WHERE reset_token IS NOT NULL
    ''').fetchall()
    conn.close()
    
    return render_template('debug_tokens.html', tokens=tokens)

# Rota para finalizar a compra
@app.route('/finalizar')
def finalizar_compra():
    session.pop('carrinho', None)
    session.modified = True
    return render_template('finalizar.html')

@app.route('/espumantes')
def espumantes():
    return render_template('espumantes.html')

@app.route('/produtos')  # Esta deve ser sua única rota para vinhos
def produtos():
    return render_template('produtos.html')

@app.route('/produtos/pagina-2')
def produtos1():
    return render_template('produtos1.html', current_page=2)
 

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