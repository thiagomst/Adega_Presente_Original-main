document.addEventListener("DOMContentLoaded", function () {
  // Ocultar a div vazia ao carregar a página
  esconderFlashContainer();
});

async function atualizarQuantidade(itemId, novaQuantidade) {
  try {
    const response = await fetch(`/atualizar_quantidade/${itemId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ quantidade: novaQuantidade }),
    });

    const data = await response.json();

    if (data.status === "success") {
      // Atualiza o contador de itens no carrinho
      document.getElementById("contador-carrinho").innerText = data.total_itens;

      // Atualiza o localStorage para refletir o total atualizado
      localStorage.setItem("contadorCarrinho", data.total_itens);

      // Atualiza o total do carrinho
      atualizarTotal();
    } else {
      alert(data.message);
    }
  } catch (error) {
    console.error("Erro ao atualizar a quantidade:", error);
  }
}

// Função para fechar a mensagem manualmente
function fecharMensagem(botao) {
  let mensagem = botao.parentElement;
  mensagem.style.animation = "fadeOut 0.5s ease-in-out";
  setTimeout(() => {
    mensagem.remove();
    esconderFlashContainer(); // Esconder a div container
  }, 500);
}

// Fechar automaticamente após 3 segundos
setTimeout(() => {
  document.querySelectorAll(".flash").forEach((mensagem) => {
    mensagem.style.animation = "fadeOut 0.5s ease-in-out";
    setTimeout(() => {
      mensagem.remove();
      esconderFlashContainer(); // Esconder a div container
    }, 500);
  });
}, 3000);

// Função para esconder a div flash-messages se não houver mais mensagens
function esconderFlashContainer() {
  let flashContainer = document.querySelector(".flash-messages");
  if (flashContainer && flashContainer.children.length === 0) {
    flashContainer.style.display = "none";
  }
}

// Função para adicionar ao carrinho
function adicionarAoCarrinho(vinhoId) {
  fetch(`/adicionar/${vinhoId}`, {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        // Atualiza o contador do carrinho com o valor total de itens
        document.getElementById("contador-carrinho").innerText =
          data.total_itens;

        // Salva a nova quantidade no localStorage
        localStorage.setItem("contadorCarrinho", data.total_itens);

        // Atualiza o total do carrinho
        atualizarTotal();
      } else {
        alert(data.message);
      }
    })
    .catch((error) => console.error("Erro:", error));
}

// Função para remover um item
async function removerItem(itemId) {
  if (confirm("Tem certeza que deseja remover este item?")) {
    const resposta = await enviarRequisicao(`/remover_item/${itemId}`, {});

    if (resposta.status === "success") {
      // Remover o item da interface
      const itemElemento = document.querySelector(`[data-id="${itemId}"]`);
      if (itemElemento) {
        itemElemento.remove(); // Remove o item da lista
      }
      atualizarTotal(); // Recalcula o total
      alert("Item removido com sucesso!");

      // Atualiza o contador de itens
      const carrinho = await obterCarrinho(); // Obtém o carrinho atualizado
      const totalItens = carrinho.reduce(
        (total, item) => total + item.quantidade,
        0
      );
      document.getElementById("contador-carrinho").innerText = totalItens;

      // Atualiza o localStorage
      localStorage.setItem("contadorCarrinho", totalItens);
    } else {
      alert(resposta.message);
    }
  }
}

// Função para atualizar o total do carrinho
function atualizarTotal() {
  const itens = document.querySelectorAll(".carrinho-item");
  let total = 0;

  // Soma o valor dos itens no carrinho
  itens.forEach((item) => {
    const preco = parseFloat(item.getAttribute("data-preco"));
    const quantidade = parseInt(item.querySelector(".quantidade").textContent);
    total += preco * quantidade;
  });

  // Adiciona o valor do frete ao total (se existir)
  const valorFreteElemento = document.getElementById("valor-frete");
  if (valorFreteElemento) {
    const valorFrete =
      parseFloat(
        valorFreteElemento.textContent.replace("R$ ", "").replace(",", ".")
      ) || 0;
    total += valorFrete;
  }

  // Atualiza o total na página
  const totalElemento = document.getElementById("total-carrinho");
  if (totalElemento) {
    totalElemento.textContent = `R$ ${total.toFixed(2).replace(".", ",")}`;
  }
}

// Função para calcular o frete
async function calcularFrete() {
  const cep = document.getElementById("cep").value;

  if (!cep || cep.length !== 8) {
    alert("Por favor, insira um CEP válido.");
    return;
  }

  try {
    const resposta = await fetch("/calcular_frete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ cep: cep }),
    });

    const data = await resposta.json();

    if (data.status === "success") {
      const freteContainer = document.getElementById("frete-container");
      const valorFrete = document.getElementById("valor-frete");
      if (freteContainer && valorFrete) {
        valorFrete.textContent = `R$ ${data.frete.toFixed(2)}`;
        freteContainer.style.display = "block";
      }

      // Atualiza o total do carrinho incluindo o frete
      atualizarTotal();
    } else {
      alert(data.message);
    }
  } catch (erro) {
    console.error("Erro ao calcular frete:", erro);
    alert("Erro ao calcular frete. Tente novamente.");
  }
}

// Função para enviar requisições
async function enviarRequisicao(url, dados) {
  try {
    const resposta = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(dados),
    });
    return await resposta.json();
  } catch (erro) {
    console.error("Erro na requisição:", erro);
    return { status: "error", message: "Erro na requisição." };
  }
}

// Função para obter o carrinho
async function obterCarrinho() {
  try {
    const resposta = await fetch("/carrinho/contador");
    const data = await resposta.json();
    return data.carrinho || [];
  } catch (erro) {
    console.error("Erro ao obter carrinho:", erro);
    return [];
  }
}
