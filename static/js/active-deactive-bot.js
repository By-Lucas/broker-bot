document.addEventListener("DOMContentLoaded", function () {
    const startBotButton = document.getElementById("start-bot");
    const pauseBotButton = document.getElementById("pause-bot");
    const toggleUrl = "/bot/api/toggle-bot-status/";

    async function getBotStatus() {
        try {
            const response = await fetch(toggleUrl, { method: "GET" });
            const data = await response.json();
            if (data.success) {
                updateButtonStates(data.is_bot_active);
            }
        } catch (error) {
            console.error("Erro ao obter status do robô:", error);
        }
    }

    async function toggleBotStatus(button, isActivating) {
        setLoadingState(button, true);

        try {
            const response = await fetch(toggleUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ "status_bot": isActivating }) // 🔥 Envia `true` ou `false`
            });

            const data = await response.json();

            if (data.success) {
                updateButtonStates(data.is_bot_active);
                setTimeout(() => setLoadingState(button, false), 1000);
                showToast(`Robô ${data.is_bot_active ? "ativado" : "pausado"} com sucesso!`, "success");

            } else {
                setTimeout(() => setLoadingState(button, false), 1000);
                showToast(data.error || "Erro ao alterar o status do robô", "error");
            }
        } catch (error) {
            console.error("Erro ao alternar o status do robô:", error);
        }

    }

    startBotButton.addEventListener("click", function (event) {
        event.preventDefault();
        if (!startBotButton.classList.contains("disabled")) {
            startBotButton.classList.add("disabled"); // 🔥 Bloqueia imediatamente
            toggleBotStatus(startBotButton, true);
        }
    });

    pauseBotButton.addEventListener("click", function (event) {
        event.preventDefault();
        if (!pauseBotButton.classList.contains("disabled")) {
            pauseBotButton.classList.add("disabled"); // 🔥 Bloqueia imediatamente
            toggleBotStatus(pauseBotButton, false);
        }
    });

    getBotStatus();
});
