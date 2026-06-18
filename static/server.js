const MAX_POINTS = 60;

const cpuData  = Array(MAX_POINTS).fill(null);
const ramData  = Array(MAX_POINTS).fill(null);
const diskData = Array(MAX_POINTS).fill(null);

function drawSparkline(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const wrapper = canvas.parentElement;
    const w = wrapper.offsetWidth  || 300;
    const h = wrapper.offsetHeight || 80;

    canvas.width  = w;
    canvas.height = h;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);

    const filled = data.filter(v => v !== null);
    if (filled.length < 2) return;

    const step = w / (MAX_POINTS - 1);
    const scaleY = val => h - (val / 100) * (h - 6) - 3;

    const firstIdx = data.indexOf(filled[0]);
    const lastIdx  = data.map((v, i) => v !== null ? i : -1).filter(i => i >= 0).pop();

    // Filled area
    ctx.beginPath();
    let moved = false;
    data.forEach((val, i) => {
        if (val === null) return;
        if (!moved) { ctx.moveTo(i * step, scaleY(val)); moved = true; }
        else ctx.lineTo(i * step, scaleY(val));
    });
    ctx.lineTo(lastIdx * step, h);
    ctx.lineTo(firstIdx * step, h);
    ctx.closePath();
    ctx.fillStyle = color + '30';
    ctx.fill();

    // Line
    ctx.beginPath();
    moved = false;
    data.forEach((val, i) => {
        if (val === null) return;
        if (!moved) { ctx.moveTo(i * step, scaleY(val)); moved = true; }
        else ctx.lineTo(i * step, scaleY(val));
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.stroke();
}

function push(arr, val) { arr.push(val); arr.shift(); }

async function fetchStats() {
    try {
        const res = await fetch('/api/server-stats');
        if (!res.ok) return;
        const d = await res.json();

        push(cpuData,  d.cpu);
        push(ramData,  d.ram);
        push(diskData, d.disk);

        drawSparkline('cpu-chart',  cpuData,  '#FF3A20');
        drawSparkline('ram-chart',  ramData,  '#aaaaaa');
        drawSparkline('disk-chart', diskData, '#555555');

        document.getElementById('cpu-pct').textContent  = d.cpu  + '%';
        document.getElementById('ram-pct').textContent  = d.ram  + '%';
        document.getElementById('disk-pct').textContent = d.disk + '%';
    } catch (e) {
        console.error('server-stats fetch failed:', e);
    }
}

window.addEventListener('load', function () {
    fetchStats();
    setInterval(fetchStats, 2000);
});
