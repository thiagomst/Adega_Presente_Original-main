
// Mostrar/ocultar menu admin
function openEditModal(productId) {
    const menu = document.getElementById(`admin-menu-${productId}`);
    const allMenus = document.querySelectorAll('.admin-menu');

    // Fecha todos os outros menus
    allMenus.forEach(m => {
        if (m.id !== `admin-menu-${productId}`) m.style.display = 'none';
    });

    // Alterna o menu atual
    if (menu.style.display === 'block') {
        menu.style.display = 'none';
    } else {
        menu.style.display = 'block';
    }
}

// Fechar menus quando clicar fora
document.addEventListener('click', function (e) {
    if (!e.target.closest('.admin-actions')) {
        document.querySelectorAll('.admin-menu').forEach(menu => {
            menu.style.display = 'none';
        });
    }
});

// Função para editar imagem
// Função para editar imagem - Versão Modernizada
function editImage(productId) {
    const imgElement = document.querySelector(`[data-setbg*="product-${productId}"]`);
    const currentImage = imgElement.getAttribute('data-setbg');

    Swal.fire({
        title: '<span style="font-size: 1.5rem; font-weight: 600; color: #1a1a1a; font-family: \'Inter\', sans-serif">Alterar Imagem</span>',
        html: `
<div style="font-family: 'Inter', sans-serif; max-width: 100%; color: #333;">
<div style="margin-bottom: 1.5rem; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">
<img id="current-image" src="${currentImage}" alt="Imagem Atual"
style="width: 100%; max-height: 280px; object-fit: contain; border-radius: 12px;">
</div>

<div style="text-align: center; color: #999; font-size: 0.8rem; text-transform: uppercase; margin: 1rem 0; position: relative;">
<span style="background: #fff; padding: 0 12px; position: relative; z-index: 1;">ou</span>
<div style="position: absolute; top: 50%; left: 0; width: 100%; height: 1px; background: #e0e0e0; z-index: 0;"></div>
</div>

<div style="display: flex; flex-direction: column; gap: 1rem;">
<!-- Upload por arquivo -->
<label for="image-upload" style="cursor: pointer; border: 2px dashed #6c63ff; border-radius: 12px; background: #fdfdfd; padding: 1.5rem; text-align: center; transition: all 0.3s ease;">
<i class="fas fa-cloud-upload-alt" style="font-size: 1.75rem; color: #6c63ff; margin-bottom: 0.5rem;"></i>
<p style="margin: 0; font-size: 0.9rem; color: #666;">Clique ou arraste uma imagem aqui</p>
<input type="file" id="image-upload" accept="image/*" style="display: none;">
</label>

<!-- Ou colar URL -->
<input type="text" id="image-url" placeholder="Ou cole a URL da imagem"
style="width: 100%; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 12px; font-size: 0.95rem; background: #fafafa; outline: none; transition: border 0.2s ease;">
</div>
</div>
`,
        showCancelButton: true,
        confirmButtonText: 'Salvar Alterações',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            const fileInput = document.getElementById('image-upload');
            const urlInput = document.getElementById('image-url');

            if (fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('image', fileInput.files[0]);

                return fetch(`/upload-image/${productId}`, {
                    method: 'POST',
                    body: formData
                })
                    .then(response => {
                        if (!response.ok) throw new Error('Erro no servidor');
                        return response.json();
                    })
                    .then(data => {
                        if (!data.success) throw new Error(data.message);
                        return data.dbImagePath; // Usa o caminho relativo do banco
                    });
            } else if (urlInput.value) {
                return urlInput.value;
            } else {
                Swal.showValidationMessage('Por favor, selecione uma imagem ou forneça uma URL');
                return false;
            }
        }
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            // Prepara o valor para enviar ao servidor
            const dbImagePath = result.value.startsWith('http') ?
                result.value.split('/static/')[1] :
                result.value;

            fetch(`/editar_produto/${productId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ imagem: dbImagePath })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Atualiza a exibição na página
                        const displayUrl = result.value.startsWith('http') ?
                            result.value :
                            `/static/${result.value}`;

                        imgElement.setAttribute('data-setbg', displayUrl);
                        imgElement.style.backgroundImage = `url(${displayUrl})`;

                        Swal.fire({
                            title: '<span style="font-size: 1.25rem; font-weight: 600; color: #1a1a1a; font-family: \'Inter\', sans-serif">Sucesso!</span>',
                            html: '<span style="font-family: \'Inter\', sans-serif; color: #555;">Imagem atualizada com sucesso</span>',
                            icon: 'success',
                            timer: 2000
                        });
                    } else {
                        Swal.fire({
                            title: '<span style="font-size: 1.25rem; font-weight: 600; color: #1a1a1a; font-family: \'Inter\', sans-serif">Erro!</span>',
                            html: `<span style="font-family: 'Inter', sans-serif; color: #555;">${data.message || 'Erro ao atualizar imagem'}</span>`,
                            icon: 'error'
                        });
                    }
                });
        }
    });
}

// Função para editar preço
function editPrice(productId) {
    const currentPrice = document.querySelector(`.product__item:has(#admin-menu-${productId}) .product-price`).textContent.replace('R$ ', '');

    Swal.fire({
        title: 'Alterar Preço',
        input: 'number',
        inputValue: currentPrice,
        inputAttributes: {
            step: "0.01",
            min: "0"
        },
        showCancelButton: true,
        confirmButtonText: 'Salvar',
        cancelButtonText: 'Cancelar',
        inputValidator: (value) => {
            if (!value || isNaN(value) || parseFloat(value) <= 0) {
                return 'Por favor, insira um valor válido maior que zero';
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const newPrice = parseFloat(result.value).toFixed(2);

            fetch(`/editar_produto/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ preco: newPrice })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Atualizar o preço na página sem recarregar
                        document.querySelector(`.product__item:has(#admin-menu-${productId}) .product-price`).textContent = `R$ ${newPrice}`;
                        Swal.fire('Sucesso!', 'Preço atualizado com sucesso.', 'success');
                    } else {
                        Swal.fire('Erro!', data.message || 'Erro ao atualizar preço', 'error');
                    }
                });
        }
    });
}

// Função para deletar produto
function deleteProduct(productId) {
    Swal.fire({
        title: 'Tem certeza?',
        text: "Você não poderá reverter isso!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sim, excluir!',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/excluir_produto/${productId}`, {
                method: 'POST'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remover o produto da página sem recarregar
                        document.querySelector(`.product__item:has(#admin-menu-${productId})`).closest('.col-lg-4').remove();

                        Swal.fire(
                            'Excluído!',
                            'O produto foi removido com sucesso.',
                            'success'
                        );
                    } else {
                        Swal.fire(
                            'Erro!',
                            data.message || 'Ocorreu um erro ao excluir o produto.',
                            'error'
                        );
                    }
                });
        }
    });
}

// Função para adicionar estoque
function addStock(productId) {
    Swal.fire({
        title: 'Adicionar Estoque',
        input: 'number',
        inputPlaceholder: 'Quantidade a adicionar',
        inputAttributes: {
            min: '1',
            step: '1'
        },
        showCancelButton: true,
        confirmButtonText: 'Adicionar',
        cancelButtonText: 'Cancelar',
        inputValidator: (value) => {
            if (!value || isNaN(value) || parseInt(value) <= 0) {
                return 'Por favor, insira um número válido maior que zero';
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const quantity = parseInt(result.value);

            fetch(`/adicionar_estoque/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ quantidade: quantity })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('Sucesso!', `Estoque atualizado: ${data.message}`, 'success');
                    } else {
                        Swal.fire('Erro!', data.message || 'Erro ao atualizar estoque', 'error');
                    }
                });
        }
    });
}

