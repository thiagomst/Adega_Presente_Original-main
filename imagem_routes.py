from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import os
from werkzeug.utils import secure_filename
from init_db import get_db_connection  # Importa do init_db.py

# Cria um Blueprint para as rotas de gerenciamento de imagens
imagem_bp = Blueprint('imagem', __name__, url_prefix='/admin/imagens')

# Extensões permitidas para upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Função para verificar se a extensão da imagem é permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@imagem_bp.route('/')
def admin_imagens():
    if not session.get('is_admin'):
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    # Busca os produtos (vinhos) no banco de dados
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM vinhos').fetchall()
    conn.close()

    # Renderiza o template passando os produtos
    return render_template('admin_imagens.html', produtos=produtos)

@imagem_bp.route('/upload/<int:id>', methods=['POST'])
def upload_imagem(id):
    if not session.get('is_admin'):
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    if 'imagem' in request.files:
        imagem = request.files['imagem']
        if imagem.filename != '':
            # Salva a nova imagem na pasta static/img
            caminho = os.path.join('static/img', imagem.filename)
            imagem.save(caminho)

            # Atualiza o caminho da imagem no banco de dados
            conn = get_db_connection()
            conn.execute('UPDATE vinhos SET imagem = ? WHERE id = ?', (imagem.filename, id))
            conn.commit()
            conn.close()

            # Retorna o novo caminho da imagem para o frontend
            return jsonify({"success": True, "new_image_path": url_for('static', filename='img/' + imagem.filename)})
    
    return jsonify({"success": False})


@imagem_bp.route('/upload_background', methods=['POST'])
def upload_background():
    if not session.get('is_admin'):
        flash('Acesso negado! Você precisa ser um administrador.', 'error')
        return redirect(url_for('index'))

    if 'background' in request.files:
        background = request.files['background']
        
        if background.filename != '' and allowed_file(background.filename):
            # Garante que o nome da imagem de fundo seja seguro
            background_filename = secure_filename(background.filename)
            caminho = os.path.join('static/img', background_filename)
            
            # Salva a imagem de fundo no servidor
            background.save(caminho)

            # Aqui você pode atualizar o banco de dados ou outro sistema para armazenar o caminho da imagem de fundo
            flash('Imagem de fundo atualizada com sucesso!', 'success')
        else:
            flash('Formato de imagem de fundo não permitido. Aceite apenas arquivos PNG, JPG, JPEG e GIF.', 'error')

    return redirect(url_for('imagem.admin_imagens'))
