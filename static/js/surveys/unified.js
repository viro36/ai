(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initUnifiedChart();
        animateCards();
        initTooltips();
    });

    function initUnifiedChart() {
        const chartCanvas = document.getElementById('unifiedProfileChart');
        if (!chartCanvas) return;

        const surveyType = chartCanvas.dataset.surveyType || 'custom';
        let chartLabels = [], chartScores = [];

        if (chartCanvas.dataset.chart) {
            try {
                const chartData = JSON.parse(chartCanvas.dataset.chart);
                chartLabels = chartData.labels || [];
                chartScores = chartData.scores || [];
            } catch(e) {
                console.error('Error parsing chart data:', e);
            }
        }

        const colors = {
            digcomp: 'rgba(54, 162, 235, 0.7)',
            riasec: 'rgba(75, 192, 192, 0.7)',
            default: 'rgba(102, 126, 234, 0.7)'
        };
        const bgColor = colors[surveyType] || colors.default;

        const ctx = chartCanvas.getContext('2d');
        if (window.unifiedChart) window.unifiedChart.destroy();

        window.unifiedChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Ваши баллы',
                    data: chartScores,
                    backgroundColor: bgColor,
                    borderColor: bgColor.replace('0.7', '1'),
                    borderWidth: 2,
                    borderRadius: 8,
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} из 50 баллов` } },
                    legend: { position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true, max: 50, ticks: { stepSize: 10, callback: v => v + ' баллов' }, title: { display: true, text: 'Баллы' } },
                    x: { ticks: { rotation: 0, autoSkip: false, font: { size: 10 } }, title: { display: true, text: 'Компетенции / Типы' } }
                },
                animation: { duration: 1000, easing: 'easeOutQuart' }
            }
        });
    }

    function animateCards() {
        const cards = document.querySelectorAll('.unified-block-card');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    const card = entry.target;
                    card.style.opacity = '0';
                    card.style.transform = 'translateX(-20px)';
                    setTimeout(() => {
                        card.style.transition = 'all 0.4s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateX(0)';
                    }, i * 100);
                    observer.unobserve(card);
                }
            });
        }, { threshold: 0.1 });
        cards.forEach(card => observer.observe(card));
    }

    function initTooltips() {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
        }
    }
})();
