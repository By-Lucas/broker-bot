
document.addEventListener("DOMContentLoaded", function () {
    const notificationsContainer = document.querySelector(".wg-chart-default-aviso");
    const startBotButton = document.getElementById("start-bot");
    const pauseBotButton = document.getElementById("pause-bot");

    const socket = new WebSocket("ws://" + window.location.host + "/ws/notifications/");

    socket.onopen = function () {
        console.log("✅ WebSocket de notificações conectado com sucesso!");
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (!data.type) {
            console.error("⚠ Notificação inválida recebida.");
            return;
        }

        let notificationHTML = "";
        let shouldDisableBot = false; // Flag para definir se o robô será desativado

        if (data.type === "stop_gain" || data.type === "stop_loss") {
            // Stop Gain / Stop Loss atingido
            const color = data.type === "stop_gain" ? "#28a745" : "#dc3545"; // Verde para Gain, Vermelho para Loss
            notificationHTML = `
                <div class="flex items-center justify-between">
                    <h6 class="white-color" style="color: ${color};">${data.title} - R$ ${data.value ? data.value.toFixed(2) : "0.00"}</h6>
                </div>
            `;
            shouldDisableBot = false; // Define para desativar o robô
        } else if (data.type === "maximum_profit") {
            // Lucro Máximo Atingido
            notificationHTML = `
                <div class="flex items-center justify-between">
                    <h6 class="white-color" style="color: #ffc107;">${data.title}</h6>
                    ${data.url_redirect ? `<a href="${data.url_redirect}" class="tf-button w208">Falar com Suporte</a>` : ""}
                </div>
                ${data.description ? `<p style="color: #ffff;">${data.description}</p>` : ""}
            `;
            shouldDisableBot = true; // Define para desativar o robô
        } else {
            // Notificação genérica
            notificationHTML = `
                <div class="flex items-center justify-between">
                    <h6 class="white-color" style="color: #6c757d;">${data.title}</h6>
                    ${data.url_redirect ? `<a href="${data.url_redirect}" class="tf-button w208">Ação</a>` : ""}
                </div>
                ${data.description ? `<p style="color: #ffff;">${data.description}</p>` : ""}
            `;
        }
        
        if (notificationsContainer != null){
            // Exibe a notificação
            notificationsContainer.style.display = "block";
            notificationsContainer.innerHTML = notificationHTML;
        }

        // 🔥 Se for uma notificação de "Stop Win", "Stop Loss" ou "Maximum Profit", desabilita os botões do robô
        if (shouldDisableBot) {
            disableBotButtons();
        }
    };

    socket.onclose = function () {
        console.error("❌ WebSocket de notificações desconectado.");
    };

    // 🔹 Função para desativar os botões do robô quando necessário
    function disableBotButtons() {
        startBotButton.classList.add("disabled");
        pauseBotButton.classList.add("disabled");

        // 🔥 Atualiza a opacidade e cor dos botões para indicar que estão desativados
        startBotButton.querySelector(".text").style.opacity = "0.5";
        startBotButton.querySelector(".icon i").style.opacity = "0.5";
        startBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
        startBotButton.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza

        pauseBotButton.querySelector(".text").style.opacity = "0.5";
        pauseBotButton.querySelector(".icon i").style.opacity = "0.5";
        pauseBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
        pauseBotButton.querySelector(".icon i").style.color = "#6c757d"; // Ícone cinza
    }
});
