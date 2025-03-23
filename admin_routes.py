# admin_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from init_db import get_db_connection  # Importa do init_db.py

# Cria um Blueprint para as rotas de administração
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Rota para o painel administrativo
@admin_bp.route('/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    return render_template('admin_dashboard.html')

# Rota para gerenciar produtos
@admin_bp.route('/produtos')
def admin_produtos():
    if not session.get('is_admin'):
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM vinhos').fetchall()
    conn.close()
    return render_template('admin_produtos.html', produtos=produtos)

# Rota para editar um produto
@admin_bp.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    if not session.get('is_admin'):
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM vinhos WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        conn.execute('UPDATE vinhos SET nome = ?, descricao = ?, preco = ? WHERE id = ?',
                     (nome, descricao, preco, id))
        conn.commit()
        conn.close()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin.admin_produtos'))

    conn.close()
    return render_template('editar_produto.html', produto=produto)