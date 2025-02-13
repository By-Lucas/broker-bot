

function updateButtonStates(isBotActive) {
    const startBotButton = document.getElementById("start-bot");
    const pauseBotButton = document.getElementById("pause-bot");

    if (!startBotButton || !pauseBotButton) {
        console.error("⚠ Botões de controle do robô não encontrados.");
        return;
    }

    if (isBotActive) {
        // 🔥 Se o robô está ativo:
        startBotButton.classList.add("disabled"); // Desativa o botão "Iniciar"
        pauseBotButton.classList.remove("disabled"); // Habilita o botão "Pausar"

        // 🔥 Aplica a cor correta ao texto e ícone
        startBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
        startBotButton.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza

        pauseBotButton.querySelector(".text").style.color = "#dc3545"; // Vermelho ativo
        pauseBotButton.querySelector(".icon i").style.color = "#dc3545"; // Ícone vermelho

    } else {
        // 🔥 Se o robô está inativo:
        startBotButton.classList.remove("disabled"); // Habilita o botão "Iniciar"
        pauseBotButton.classList.add("disabled"); // Desativa o botão "Pausar"

        // 🔥 Aplica a cor correta ao texto e ícone
        startBotButton.querySelector(".text").style.color = "#28a745"; // Verde ativo
        startBotButton.querySelector(".icon i").style.color = "#28a745"; // Ícone verde

        pauseBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
        pauseBotButton.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza
    }
}


function setLoadingState(button, isLoading) {
    if (isLoading) {
        button.dataset.defaultHTML = button.innerHTML; // Salva o conteúdo original
        button.innerHTML = `<span class="loader"></span> ${button.dataset.defaultHTML}`; // Adiciona o spinner
        
        // 🔥 Mantém a cor correta e desabilita o botão corretamente
        button.querySelector(".text").style.opacity = "0.6"; // Diminui a opacidade do texto
        button.querySelector(".icon i").style.opacity = "0.6"; // Diminui a opacidade do ícone
        button.querySelector(".text").style.color = "#6c757d"; // Ícone cinza
        button.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza

    } else {
        button.innerHTML = button.dataset.defaultHTML; // Restaura o conteúdo original
        
        // 🔥 Remove a opacidade reduzida e mantém a cor correta
        button.querySelector(".text").style.opacity = "1"; // Restaura a opacidade do texto
        button.querySelector(".icon i").style.opacity = "1"; // Restaura a opacidade do ícone
        button.querySelector(".text").style.color = "#6c757d"; // Texto cinza
        button.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza
    }
}