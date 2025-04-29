document.addEventListener("DOMContentLoaded", function () {
  const mobileToggle = document.querySelector(
    ".header__container__row__mobile-toggle"
  );
  const mobileMenu = document.querySelector(
    ".header__container__row__mobile-menu"
  );
  const menuIcon = document.querySelector(
    ".header__container__row__mobile-toggle__icon"
  );
  const overlay = document.querySelector(".header__overlay");
  const dropdownToggles = document.querySelectorAll(
    ".header__container__row__mobile-menu_list_toggle"
  );

  function closeMenu() {
    mobileMenu.style.transform = "translateX(-100%)";
    overlay.classList.remove("active");
    menuIcon.classList.remove("fa-times");
    menuIcon.classList.add("fa-bars");

    setTimeout(() => {
      mobileMenu.classList.remove("active");
      overlay.style.display = "none";
    }, 300);
  }

  mobileToggle.addEventListener("click", function () {
    if (!mobileMenu.classList.contains("active")) {
      overlay.style.display = "block";
      mobileMenu.style.display = "flex";

      requestAnimationFrame(() => {
        mobileMenu.classList.add("active");
        overlay.classList.add("active");
        menuIcon.classList.remove("fa-bars");
        menuIcon.classList.add("fa-times");
        mobileMenu.style.transform = "translateX(0)";
      });
    } else {
      closeMenu();
    }
  });

  dropdownToggles.forEach((toggle) => {
    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      const parent = this.closest(
        ".header__container__row__mobile-menu_list_dropdown"
      );
      const wasActive = parent.classList.contains("active");

      document
        .querySelectorAll(".header__container__row__mobile-menu_list_dropdown")
        .forEach((dropdown) => {
          dropdown.classList.remove("active");
        });

      if (!wasActive) {
        parent.classList.add("active");
      }
    });
  });

  overlay.addEventListener("click", closeMenu);

  // Função para fechar mensagens flash
  function fecharMensagem(element) {
    element.classList.add("fade-out");
    setTimeout(() => {
      element.remove();
    }, 500);
  }

  // Fazer mensagens flash desaparecerem automaticamente após 5 segundos
  const flashMessages = document.querySelectorAll(
    ".header__container__row__messages__flash"
  );
  flashMessages.forEach((message) => {
    setTimeout(() => {
      fecharMensagem(message);
    }, 5000);
  });

  // Adicionar evento de clique ao botão de fechar
  document
    .querySelectorAll(".header__container__messages__close")
    .forEach((button) => {
      button.addEventListener("click", function () {
        fecharMensagem(this.parentElement);
      });
    });
});

// Contador do carrinho
document.addEventListener("DOMContentLoaded", function () {
  const contador = sessionStorage.getItem("contadorCarrinho");
  const contadorElemento = document.getElementById("contador-carrinho");
  if (contador && contadorElemento) {
    contadorElemento.textContent = contador;
  }
});
