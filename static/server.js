const MAX_POINTS = 40;

function emptyData() {
    return Array(MAX_POINTS).fill(null);
}

function makeChart(canvasId, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: emptyData(),
            datasets: [{
                data: emptyData(),
                borderColor: color,
                backgroundColor: color + '22',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.4,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: { display: false },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: '#1e1e1e' },
                    ticks: { color: '#444', font: { size: 10 }, callback: v => v + '%' }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

const cpuChart  = makeChart('cpu-chart',  '#FF3A20');
const ramChart  = makeChart('ram-chart',  '#aaaaaa');
const diskChart = makeChart('disk-chart', '#555555');

function push(chart, value) {
    chart.data.datasets[0].data.push(value);
    chart.data.datasets[0].data.shift();
    chart.update('none');
}

async function fetchStats() {
    try {
        const res = await fetch('/api/server-stats');
        const d = await res.json();
        push(cpuChart,  d.cpu);
        push(ramChart,  d.ram);
        push(diskChart, d.disk);
        document.getElementById('cpu-pct').textContent  = d.cpu  + '%';
        document.getElementById('ram-pct').textContent  = d.ram  + '%';
        document.getElementById('disk-pct').textContent = d.disk + '%';
    } catch (_) {}
}

fetchStats();
setInterval(fetchStats, 2000);
