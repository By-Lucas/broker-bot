document.addEventListener("DOMContentLoaded", function () {
    const notificationsContainer = document.getElementById("profit-notification");
    const profitNotification = document.getElementById("profit-notification");
    const profitMessage = document.getElementById("profit-message");
    const startBotButton = document.getElementById("start-bot");
    const pauseBotButton = document.getElementById("pause-bot");

    const socket = new WebSocket("ws://" + window.location.host + "/ws/notifications/");

    socket.onopen = function () {
        console.log("✅ WebSocket de notificações conectado com sucesso!");
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log(data)

        if (!data.type) {
            console.error("⚠ Notificação inválida recebida.");
            return;
        }

        // Oculta notificações quando necessário
        if (data.type === "clean_notification") {
            notificationsContainer.style.display = "none";
            profitNotification.classList.add("d-none");
            return;
        }

        let notificationHTML = "";
        let shouldDisableBot = false; // Flag para definir se o robô será desativado

        if (data.type === "stop_gain" || data.type === "stop_loss") {
            // 🔥 Stop Gain ou Stop Loss
            const color = data.type === "stop_gain" ? "#28a745" : "#dc3545"; // Verde para ganho, Vermelho para perda
            const bgColor = data.type === "stop_gain" ? "bg-success" : "bg-danger";

            notificationHTML = `
                <div class="flex items-center justify-between">
                    <h6 class="white-color" >${data.title} - R$ ${data.value ? data.value.toFixed(2) : "0.00"}</h6>
                </div>
            `;

            // 🎯 Atualiza a barra central com lucro/prejuízo
            profitMessage.innerHTML = `${data.title} - R$ ${data.value ? data.value.toFixed(2) : "0.00"}`;
            profitNotification.classList.remove("bg-success", "bg-danger", "d-none");
            profitNotification.classList.add(bgColor);

            shouldDisableBot = false;
        } else if (data.type === "maximum_profit") {
            // 🔥 Lucro Máximo Atingido
            notificationHTML = `
                <div class="flex items-center justify-between">
                    <h6 class="white-color">${data.title}</h6>
                    ${data.url_redirect ? `<a href="${data.url_redirect}" class="tf-button w208">Falar com Suporte</a>` : ""}
                </div>
                ${data.description ? `<p style="color: #ffff;">${data.description}</p>` : ""}
            `;

            shouldDisableBot = true;
        } else {
            // 🔹 Notificação Genérica
            notificationHTML = `
                <div class="flex items-center justify-between">
                    <h6 class="white-color">${data.title}</h6>
                    ${data.url_redirect ? `<a href="${data.url_redirect}" class="tf-button w208">Ação</a>` : ""}
                </div>
                ${data.description ? `<p style="color: #ffff;">${data.description}</p>` : ""}
            `;
        }

        if (notificationsContainer != null) {
            // Exibe a notificação normal
            notificationsContainer.style.display = "block";
            notificationsContainer.innerHTML = notificationHTML;
        }

        // 🔥 Se for "Stop Gain", "Stop Loss" ou "Maximum Profit", desabilita os botões do robô
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
        startBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado

        pauseBotButton.querySelector(".text").style.opacity = "0.5";
        pauseBotButton.querySelector(".text").style.color = "#6c757d"; // Cinza desativado
    }
});
