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

    // Atualizar a tabela de WIN e LOSS
    const winLossTable = document.querySelector("#win-loss-table");
    if (winLossTable) {
        winLossTable.innerHTML = "";

        data.data.trade_details.forEach((trade) => {
            let statusClass;
            let statusText;

            switch (trade.order_result_status) {
                case "WIN":
                    statusClass = "text-success";
                    statusText = "WIN";
                    break;
                case "LOSS":
                    statusClass = "text-danger";
                    statusText = "LOSS";
                    break;
                case "DOGI":
                    statusClass = "text-warning";
                    statusText = "EMPATE";
                    break;
                default:
                    statusClass = "text-white";
                    statusText = "PENDENTE";
            }

            const tradeRow = `
                <tr>
                    <td><input class="form-check-input" type="checkbox"></td>
                    <td>${new Date(trade.timestamp * 1000).toLocaleDateString("pt-BR")}</td>
                    <td>${trade.asset_order || "N/A"}</td>
                    <td>${balanceData.currency} ${trade.amount ? trade.amount.toFixed(2) : "--"}</td>
                    <td>${balanceData.currency} ${trade.result ? trade.result.toFixed(2) : "--"}</td>
                    <td class="${statusClass}">${statusText}</td>
                    <td><a class="btn btn-sm btn-primary" href="#">Detalhes</a></td>
                </tr>
            `;

            winLossTable.innerHTML += tradeRow;
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