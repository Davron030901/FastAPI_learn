function formatDateTime(date) {
    return new Date(date).toLocaleString('uz-UZ');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: 'UZS'
    }).format(amount);
}