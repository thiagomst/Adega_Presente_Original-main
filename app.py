from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import time
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from difflib import get_close_matches
from admin_routes import admin_bp
from imagem_routes import imagem_bp
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta
import re
from init_db import verificar_esquema, get_db_connection 

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mais_segura_e_unica'

# Configurações para upload de imagens
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'img', 'product', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(admin_bp)
app.register_blueprint(imagem_bp)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thiagomonsuet@gmail.com'
app.config['MAIL_PASSWORD'] = 'zlko lorv qnyg szat'
app.config['MAIL_DEFAULT_SENDER'] = 'thiagomonsuet@gmail.com'

mail = Mail(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('adega.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # Adicionando categoria na consulta
    vinhos = conn.execute('SELECT id, nome, preco, imagem, categoria, descricao FROM vinhos').fetchall()
    is_admin = False
    
    if 'user_id' in session:
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        if user and user['role'] == 'admin':
            is_admin = True
    
    conn.close()
    return render_template('index.html', vinhos=vinhos, is_admin=is_admin)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not user or user['role'] != 'admin':
        conn.close()
        flash('Acesso restrito a administradores', 'error')
        return redirect(url_for('index'))
    
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    
    return render_template("produtos.html",
                         produtos=produtos,
                         usuario_logado=user,  # Mantive este nome
                         is_admin=True)

# Rota para detalhes do produto
@app.route('/produto/<int:produto_id>')
def detalhes_produto(produto_id):
    # Aqui você buscaria o produto do banco de dados
    # Estou usando dados mockados como exemplo
    produto = {
        'id': produto_id,
        'nome': 'Vinho Finca La Anita Malbec 2021',
        'tipo': 'Tinto',
        'descricao': 'O Vinho Finca La Anita Malbec apresenta uma cor vermelho rubi intensa e brilhante...',
        'produtor': 'Finca La Anita',
        'regiao': 'Mendoza',
        'uva': 'Malbec',
        'teor_alcoolico': '14,5%',
        'pontuacao': '93 pontos Guia Descorchados',
        'harmonizacao': 'Carnes vermelhas, queijos e massas',
        'preco': '172,00',
        'preco_parcelado': '57,33',
        'preco_pix': '166,84',
        'imagem': 'product-1.jpg'  # Nome do arquivo de imagem
    }
    return render_template('detalhes_produto.html', produto=produto)

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
                session['email'] = user['email']
                session['is_admin'] = user['role'] == 'admin'
                session['usuario_logado'] = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }

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


@app.route('/adicionar/<int:vinho_id>', methods=['POST'])
def adicionar_ao_carrinho(vinho_id):
    if 'carrinho' not in session:
        session['carrinho'] = []

    conn = get_db_connection()
    vinho = conn.execute('SELECT id FROM vinhos WHERE id = ?', (vinho_id,)).fetchone()
    conn.close()

    if not vinho:
        return jsonify({'status': 'error', 'message': 'Vinho não encontrado'}), 404

    # Verifica se o item já está no carrinho
    item_existente = next((item for item in session['carrinho'] if item['id'] == vinho_id), None)

    if item_existente:
        item_existente['quantidade'] += 1
    else:
        session['carrinho'].append({
            'id': vinho_id,
            'quantidade': 1
        })

    session.modified = True
    total_itens = sum(item['quantidade'] for item in session['carrinho'])
    return jsonify({'status': 'success', 'total_itens': total_itens})

def get_carrinho():
    return session.get('carrinho', [])

def salvar_pedido(user_id, endereco, metodo_pagamento, carrinho, total, status='pendente'):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO pedidos (user_id, endereco, metodo_pagamento, status, total) VALUES (?, ?, ?, ?, ?)',
        (user_id, endereco, metodo_pagamento, status, total)
    )
    pedido_id = cursor.lastrowid

    for item in carrinho:
        cursor.execute(
            'INSERT INTO itens_pedido (pedido_id, vinho_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)',
            (pedido_id, item['id'], item['quantidade'], item['preco'])
        )

    conn.commit()
    conn.close()
    return pedido_id

@app.route('/carrinho')
def ver_carrinho():
    # Inicializa o carrinho se não existir
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    # Prepara lista de itens com informações completas
    carrinho_completo = []
    total = 0
    
    conn = get_db_connection()
    
    for item in session['carrinho']:
        try:
            # Busca informações completas do vinho no banco
            vinho = conn.execute(
                'SELECT id, nome, preco, categoria, imagem FROM vinhos WHERE id = ?',
                (item['id'],)
            ).fetchone()
            
            if vinho:
                vinho_dict = dict(vinho)
                item_completo = {
                    'id': vinho_dict['id'],
                    'nome': vinho_dict['nome'],
                    'preco': float(vinho_dict['preco']),
                    'quantidade': item['quantidade'],
                    'categoria': vinho_dict['categoria'],
                    'imagem': vinho_dict['imagem']
                }
                carrinho_completo.append(item_completo)
                total += item_completo['preco'] * item_completo['quantidade']
        except Exception as e:
            print(f"Erro ao processar item do carrinho: {e}")
    
    conn.close()
    return render_template('carrinho.html', carrinho=carrinho_completo, total=total)

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
        # Remove o item
        session['carrinho'] = [
            item for item in session['carrinho']
            if isinstance(item, dict) and item.get('id') != item_id
        ]
        session.modified = True

        # Recalcular o novo total
        novo_total = sum(item['preco'] * item.get('quantidade', 1) for item in session['carrinho'])

        return jsonify({
            'status': 'success',
            'message': 'Item removido com sucesso!',
            'novo_total': round(novo_total, 2)
        })
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

# Rota para a página de pagamento (checkout)
@app.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    # Verificação de login
    if 'user_id' not in session:
        flash('Você precisa fazer login para finalizar a compra.', 'warning')
        return redirect(url_for('login'))

    # Verificação do carrinho
    if 'carrinho' not in session or not session['carrinho']:
        flash('Seu carrinho está vazio!', 'error')
        return redirect(url_for('ver_carrinho'))

    # Obter informações completas dos itens do carrinho (como feito na rota /carrinho)
    carrinho_completo = []
    total = 0
    conn = get_db_connection()
    
    for item in session['carrinho']:
        try:
            vinho = conn.execute(
                'SELECT id, nome, preco, categoria, imagem FROM vinhos WHERE id = ?',
                (item['id'],)
            ).fetchone()
            
            if vinho:
                vinho_dict = dict(vinho)
                item_completo = {
                    'id': vinho_dict['id'],
                    'nome': vinho_dict['nome'],
                    'preco': float(vinho_dict['preco']),
                    'quantidade': item['quantidade'],
                    'categoria': vinho_dict['categoria'],
                    'imagem': vinho_dict['imagem']
                }
                carrinho_completo.append(item_completo)
                total += item_completo['preco'] * item_completo['quantidade']
        except Exception as e:
            print(f"Erro ao processar item do carrinho: {e}")
    
    conn.close()

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            
            # Processamento do pagamento
            endereco = request.form.get('endereco')
            metodo_pagamento = request.form.get('metodo_pagamento')
            
            # Inserir pedido no banco
            cursor = conn.execute(
                'INSERT INTO pedidos (user_id, endereco, metodo_pagamento, status, total) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], endereco, metodo_pagamento, 'processando', total)
            )
            pedido_id = cursor.lastrowid
            
            # Inserir itens do pedido
            for item in session['carrinho']:
                conn.execute(
                    'INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)',
                    (pedido_id, item['id'], item['quantidade'], item['preco'])
                )
            
            conn.commit()
            
            # Limpar carrinho e redirecionar
            session.pop('carrinho', None)
            session.modified = True
            
            flash('Pagamento realizado com sucesso!', 'success')
            return redirect(url_for('pedido_sucesso', pedido_id=pedido_id))

        except Exception as e:
            print(f"Erro no pagamento: {str(e)}")
            conn.rollback()
            flash('Erro ao processar seu pagamento. Tente novamente.', 'error')
            return redirect(url_for('pagamento'))
        
        finally:
            conn.close()

    # GET request - mostrar página de pagamento
    return render_template('pagamento.html', 
                     carrinho=carrinho_completo,  # Usar a versão com preços
                     total=total,
                     frete=0.00)

# Rota de sucesso após pagamento
@app.route('/pedido/sucesso/<int:pedido_id>')
def pedido_sucesso(pedido_id):
    return render_template('sucesso.html', pedido_id=pedido_id)


# Mapeamento de categorias para templates
CATEGORIAS_PAGINAS = {
    'tinto': 'vinho_tinto.html',
    'branco': 'vinho_branco.html',
    'rose': 'vinho_rose.html',
    'espumante': 'espumantes.html',
    'embalagem': 'embalagens.html',
    'produto': 'produtos.html',
    'presente': 'presentes.html',
    'sobre': 'sobre.html',
    'contato': 'contato.html'
}

@app.route('/buscar', methods=['GET'])
def buscar():
    termo = request.args.get('q', '').strip().lower()
    
    # Verifica correspondência exata com as categorias
    if termo in CATEGORIAS_PAGINAS:
        return redirect(url_for('exibir_categoria', categoria=termo))
    
    # Busca por aproximação
    correspondencias = get_close_matches(termo, CATEGORIAS_PAGINAS.keys(), n=1, cutoff=0.6)
    if correspondencias:
        categoria_corrigida = correspondencias[0]
        return redirect(url_for('exibir_categoria', categoria=categoria_corrigida))
    
    # Busca no banco
    conn = get_db_connection()
    produtos = conn.execute('''
        SELECT DISTINCT categoria FROM produtos 
        WHERE categoria LIKE ? OR nome LIKE ?
    ''', (f'%{termo}%', f'%{termo}%')).fetchall()

    vinhos = conn.execute('''
        SELECT DISTINCT categoria FROM vinhos 
        WHERE categoria LIKE ? OR nome LIKE ?
    ''', (f'%{termo}%', f'%{termo}%')).fetchall()
    conn.close()

    categorias_encontradas = {p['categoria'] for p in produtos} | {v['categoria'] for v in vinhos}

    if len(categorias_encontradas) == 1:
        categoria = categorias_encontradas.pop()
        if categoria in CATEGORIAS_PAGINAS:
            return redirect(url_for('exibir_categoria', categoria=categoria))
    
    elif categorias_encontradas:
        correspondencias = get_close_matches(termo, categorias_encontradas, n=1, cutoff=0.5)
        if correspondencias:
            categoria = correspondencias[0]
            if categoria in CATEGORIAS_PAGINAS:
                return redirect(url_for('exibir_categoria', categoria=categoria))
    
    return render_template('index.html',
                           mensagem=f"Nenhum resultado encontrado para '{termo}'",
                           sugestoes=list(CATEGORIAS_PAGINAS.keys()))

# Rota dinâmica por categoria (URLs como /tinto, /branco, etc)
@app.route('/<categoria>')
def exibir_categoria(categoria):
    if categoria not in CATEGORIAS_PAGINAS:
        return render_template('index.html', mensagem="Página não encontrada")
    
    nome_template = CATEGORIAS_PAGINAS[categoria]
    
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos WHERE categoria = ?', (categoria,)).fetchall()
    vinhos = conn.execute('SELECT * FROM vinhos WHERE categoria = ?', (categoria,)).fetchall()
    conn.close()

    return render_template(nome_template, produtos=produtos, vinhos=vinhos)

@app.route('/sugestoes')
def sugestoes():
    termo = request.args.get('q', '').strip().lower()
    if not termo:
        return jsonify([])

    sugestoes = [categoria for categoria in CATEGORIAS_PAGINAS.keys() if termo in categoria]
    return jsonify(sugestoes)


@app.route('/espumantes')
def espumantes():
    return render_template('espumantes.html')

@app.route("/produtos", methods=['GET', 'POST'])
def produtos():
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            # Verifica se é admin e está logado para adicionar produtos
            if 'user_id' not in session or not session.get('is_admin'):
                flash('Acesso não autorizado.', 'error')
                return redirect(url_for('produtos'))
                
            # Processar adição de novo produto (apenas para admin)
            nome = request.form.get('nome')
            preco = float(request.form.get('preco'))
            imagem = request.form.get('imagem')
            descricao = request.form.get('descricao')
            categoria = request.form.get('categoria')

            conn.execute('''
                INSERT INTO produtos (nome, preco, imagem, descricao, categoria)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, preco, imagem, descricao, categoria))
            conn.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('produtos'))

        # Busca todos os produtos (acesso livre)
        produtos = conn.execute('SELECT * FROM produtos').fetchall()
        
        # Busca informações do usuário logado (se estiver logado)
        user = None
        is_admin = False
        if 'user_id' in session:
            user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
            is_admin = user and user['role'] == 'admin'
        
        return render_template("produtos.html",
                            produtos=produtos,
                            usuario_logado=user,
                            is_admin=is_admin)
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'Erro ao acessar o banco de dados: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/upload-image/<int:id>', methods=['POST'])
def upload_image(id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403

    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

    if file and allowed_file(file.filename):
        try:
            # Garante que a pasta de upload existe
            upload_folder = os.path.join(app.static_folder, 'img', 'product', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            # Gera nome único para o arquivo
            ext = os.path.splitext(file.filename)[1].lower()
            timestamp = int(time.time())
            filename = secure_filename(f"prod_{id}_{timestamp}{ext}")
            filepath = os.path.join(upload_folder, filename)

            # Salva o arquivo
            file.save(filepath)
            
            # Caminho para o banco de dados (relativo à pasta static)
            db_image_path = f"img/product/uploads/{filename}"
            
            # Atualiza o banco de dados
            conn = get_db_connection()
            try:
                conn.execute('UPDATE produtos SET imagem = ? WHERE id = ?', (db_image_path, id))
                conn.commit()
                
                # Verifica se a atualização foi bem-sucedida
                updated = conn.execute('SELECT imagem FROM produtos WHERE id = ?', (id,)).fetchone()
                if not updated or updated['imagem'] != db_image_path:
                    raise Exception("Falha ao verificar a atualização no banco de dados")
                
                return jsonify({
                    'success': True, 
                    'imageUrl': url_for('static', filename=db_image_path),
                    'dbImagePath': db_image_path,
                    'productId': id
                })
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            # Remove o arquivo se foi parcialmente salvo
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
                
            app.logger.error(f"Erro no upload: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'Erro ao processar imagem: {str(e)}'
            }), 500

    return jsonify({
        'success': False, 
        'message': 'Tipo de arquivo não permitido'
    }), 400


@app.route('/editar_produto/<int:id>', methods=['POST'])
def editar_produto(id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    conn = get_db_connection()
    try:
        update_fields = []
        update_values = []
        
        if 'nome' in data:
            update_fields.append('nome = ?')
            update_values.append(data['nome'])
        
        if 'preco' in data:
            update_fields.append('preco = ?')
            update_values.append(float(data['preco']))
        
        if 'imagem' in data:
            update_fields.append('imagem = ?')
            update_values.append(data['imagem'])
        
        if 'descricao' in data:
            update_fields.append('descricao = ?')
            update_values.append(data['descricao'])
        
        if 'categoria' in data:
            update_fields.append('categoria = ?')
            update_values.append(data['categoria'])
        
        if not update_fields:
            return jsonify({'success': False, 'message': 'Nada para atualizar'}), 400
        
        update_values.append(id)
        query = f"UPDATE produtos SET {', '.join(update_fields)} WHERE id = ?"
        
        conn.execute(query, update_values)
        conn.commit()
        return jsonify({'success': True, 'message': 'Produto atualizado com sucesso'})
    
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/adicionar_estoque/<int:produto_id>", methods=['POST'])
def adicionar_estoque(produto_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não logado'}), 401
    
    # Verificar se o usuário é admin
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    if not user or user['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    try:
        data = request.get_json()
        quantidade = int(data.get('quantidade', 0))
        
        if quantidade <= 0:
            return jsonify({'success': False, 'message': 'Quantidade inválida'}), 400
        
        # Atualizar o estoque no banco de dados
        conn.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?', 
                    (quantidade, produto_id))
        conn.commit()
        
        # Obter o novo valor do estoque para retornar
        produto = conn.execute('SELECT estoque FROM produtos WHERE id = ?', 
                             (produto_id,)).fetchone()
        
        return jsonify({
            'success': True,
            'message': f'Estoque atualizado para {produto["estoque"]} unidades'
        })
        
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Erro no banco de dados: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    conn = get_db_connection()
    try:
        # Primeiro verifica se o produto existe
        produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Exclui o produto
        conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Produto excluído com sucesso'})
    
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

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

@app.route('/presentes')
def presentes():
    return render_template('presentes.html')



if __name__ == '__main__':
    from init_db import verificar_esquema
    verificar_esquema()
    app.run(debug=True)
