const socket = new WebSocket(`ws://${window.location.host}/ws/trader/quotex/`);

socket.onopen = function () {
    console.log("✅ WebSocket para {{request.user}} conectado com sucesso!");
};

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    // console.log("📡 Dados recebidos via WebSocket");

    if (!data.data.trade_details || !Array.isArray(data.data.trade_details)) {
        console.error("⚠ Nenhum trade disponível ou formato inválido.");
        return;
    }

    // ✅ Elementos do DOM
    const totalResultsElement = document.getElementById("total-results");
    const winsCountElement = document.getElementById("wins-count");
    const lossCountElement = document.getElementById("loss-count");
    const winRateElement = document.getElementById("win-rate");
    const accountTypeElement = document.getElementById("account-type");
    const accountBalanceElement = document.getElementById("account-balance");

    // ✅ Definição do saldo e tipo de conta
    const balanceData = data.data.account_balance || { type: "DESCONHECIDO", balance: 0, currency: "R$" };

    if (accountTypeElement) {
        accountTypeElement.innerText = `CONTA ${balanceData.type}`;
    }

    if (accountBalanceElement) {
        accountBalanceElement.innerText = `${balanceData.currency} ${balanceData.balance.toFixed(2)}`;
    }

    if (totalResultsElement) {
        totalResultsElement.innerText = `${balanceData.currency} ${data.data.total_results ? data.data.total_results.toFixed(2) : "0.00"}`;
    }

    // ✅ Cálculo de Win Rate
    const totalWins = data.data.status_counts.WIN || 0;
    const totalTrades = data.data.total_trades || 0;
    const winRate = totalTrades > 0 ? ((totalWins / totalTrades) * 100).toFixed(2) : "0.00";

    if (winsCountElement) {
        winsCountElement.innerText = totalWins;
    }

    if (lossCountElement) {
        lossCountElement.innerText = data.data.status_counts.LOSS || "0";
    }

    if (winRateElement) {
        winRateElement.innerText = `${winRate}%`;
    }

    // ✅ Atualizar tabela de WIN e LOSS
    const winLossTable = document.querySelector("#win-loss-table");
    if (winLossTable) {
        winLossTable.innerHTML = "";

        data.data.trade_details.forEach((trade) => {
            // Define as classes e textos com base no resultado da ordem
            let itemClass;
            let statusText;

            if (trade.order_result_status === "WIN") {
                itemClass = "block-available"; // Classe para vitória
                statusText = "WIN"; // Texto para vitória
            } else if (trade.order_result_status === "LOSS") {
                itemClass = "block-not-available"; // Classe para perda
                statusText = "LOSS"; // Texto para perda
            } else if (trade.order_result_status === "DOGI") {
                itemClass = "block-neutral"; // Classe para empate (cinza)
                statusText = "EMPATE"; // Texto para empate
            } else {
                itemClass = "block-pending"; // Classe para casos desconhecidos
                statusText = "PENDENTE"; // Texto para casos desconhecidos
            }

            const imageUrl = "/static/images/quotex.svg";

            const item = `
                    <li class="product-item gap14">
                        <div class="image">
                            <img src="${imageUrl}" alt="${trade.asset_order || 'Trade'}">
                        </div>
                        <div class="flex items-center justify-between flex-grow">
                            <div class="name">
                                <span class="body-text">${trade.asset_order || "N/A"}</span>
                            </div>
                            <div class="body-text">${balanceData.currency} ${trade.amount ? trade.amount.toFixed(2) : "--"}</div>
                            <div class="body-text">${trade.percent_profit || "--"}%</div>
                            <div class="body-text">${balanceData.currency} ${trade.result ? trade.result.toFixed(2) : "--"}</div>
                            <div class="${itemClass}">${statusText}</div>
                        </div>
                    </li>
                `;
            winLossTable.innerHTML += item;
        });
    }
};

socket.onclose = function () {
    console.error("❌ WebSocket desconectado.");
    // Tente reconectar automaticamente
    setTimeout(() => {
        window.location.reload();
    }, 30000);
};