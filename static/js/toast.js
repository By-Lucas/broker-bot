function showToast(message, type = "success") {
    const toastContainer = document.getElementById("toast-container");

    if (!toastContainer) {
        console.error("❌ Toast container não encontrado!");
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${type === "success" ? "✅" : "⚠️"}</div>
        <div class="toast-message">${message}</div>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}
