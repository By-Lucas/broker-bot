

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

        if (startBotButton.querySelector(".text")) startBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
        if (startBotButton.querySelector(".icon i")) startBotButton.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza

        if (pauseBotButton.querySelector(".text")) pauseBotButton.querySelector(".text").style.color = "#dc3545"; // Vermelho ativo
        if (pauseBotButton.querySelector(".icon i")) pauseBotButton.querySelector(".icon i").style.color = "#dc3545"; // Ícone vermelho
    } else {
        // 🔥 Se o robô está inativo:
        startBotButton.classList.remove("disabled"); // Habilita o botão "Iniciar"
        pauseBotButton.classList.add("disabled"); // Desativa o botão "Pausar"

        if (startBotButton.querySelector(".text")) startBotButton.querySelector(".text").style.color = "#28a745"; // Verde ativo
        if (startBotButton.querySelector(".icon i")) startBotButton.querySelector(".icon i").style.color = "#28a745"; // Ícone verde

        if (pauseBotButton.querySelector(".text")) pauseBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
        if (pauseBotButton.querySelector(".icon i")) pauseBotButton.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza
    }
}


function setLoadingState(button, isLoading) {
    if (isLoading) {
        button.dataset.defaultHTML = button.innerHTML; // Salva o conteúdo original
        button.innerHTML = `<span class="loader"></span> ${button.dataset.defaultHTML}`; // Adiciona o spinner

        if (button.querySelector(".text")) {
            button.querySelector(".text").style.opacity = "0.6"; // Diminui a opacidade do texto
            button.querySelector(".text").style.color = "#6c757d"; // Texto cinza
        }
        if (button.querySelector(".icon i")) {
            button.querySelector(".icon i").style.opacity = "0.6"; // Diminui a opacidade do ícone
            button.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza
        }
        button.disabled = true; // Desativa o botão temporariamente
    } else {
        button.innerHTML = button.dataset.defaultHTML; // Restaura o conteúdo original

        if (button.querySelector(".text")) {
            button.querySelector(".text").style.opacity = "1"; // Restaura a opacidade do texto
            button.querySelector(".text").style.color = "#000"; // Texto preto
        }
        if (button.querySelector(".icon i")) {
            button.querySelector(".icon i").style.opacity = "1"; // Restaura a opacidade do ícone
            button.querySelector(".icon i").style.color = "#000"; // Ícone preto
        }
        button.disabled = false; // Reativa o botão
    }
}