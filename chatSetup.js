document.addEventListener('DOMContentLoaded', () => {
    const initChart = () => {
        const ctx = document.getElementById('weather-chart')?.getContext('2d');
        if (!ctx) return;

        const temps = [];
        const times = [];
        
        document.querySelectorAll('.forecast-item').forEach(item => {
            const time = item.querySelector('.forecast-time')?.textContent;
            const temp = item.querySelector('.forecast-temp')?.textContent;
            if (time && temp) {
                times.push(time);
                temps.push(parseFloat(temp));
            }
        });

        if (temps.length === 0) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: times,
                datasets: [{
                    label: 'Temperature (°C)',
                    data: temps,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.4,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        });
    };

    // Initialize chart and retry if elements not ready
    if (document.readyState === 'complete') {
        initChart();
    } else {
        window.addEventListener('load', initChart);
    }
});