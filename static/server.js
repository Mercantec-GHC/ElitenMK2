const MAX_POINTS = 60;

const cpuData  = Array(MAX_POINTS).fill(null);
const ramData  = Array(MAX_POINTS).fill(null);
const diskData = Array(MAX_POINTS).fill(null);

function drawSparkline(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width  = w;
    canvas.height = h;
    ctx.clearRect(0, 0, w, h);

    const filled = data.filter(v => v !== null);
    if (filled.length < 2) return;

    const step = w / (MAX_POINTS - 1);

    // Fill area
    ctx.beginPath();
    let first = true;
    data.forEach((val, i) => {
        if (val === null) return;
        const x = i * step;
        const y = h - (val / 100) * (h - 4) - 2;
        if (first) { ctx.moveTo(x, y); first = false; }
        else ctx.lineTo(x, y);
    });
    const lastIdx = data.map((v, i) => v !== null ? i : -1).filter(i => i >= 0).pop();
    ctx.lineTo(lastIdx * step, h);
    ctx.lineTo(data.indexOf(filled[0]) * step, h);
    ctx.closePath();
    ctx.fillStyle = color + '28';
    ctx.fill();

    // Line
    ctx.beginPath();
    first = true;
    data.forEach((val, i) => {
        if (val === null) return;
        const x = i * step;
        const y = h - (val / 100) * (h - 4) - 2;
        if (first) { ctx.moveTo(x, y); first = false; }
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.stroke();
}

function push(arr, val) {
    arr.push(val);
    arr.shift();
}

async function fetchStats() {
    try {
        const res = await fetch('/api/server-stats');
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
    } catch (_) {}
}

fetchStats();
setInterval(fetchStats, 2000);
