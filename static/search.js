document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('search');
    const tableId = input ? input.dataset.table : null;
    if (!input || !tableId) return;

    const table = document.getElementById(tableId);
    if (!table) return;

    input.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        table.querySelectorAll('tr:not(:first-child)').forEach(function (row) {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
});
