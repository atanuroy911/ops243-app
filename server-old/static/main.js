document.addEventListener('DOMContentLoaded', () => {
    const velocityChart = new Chart(document.getElementById('velocity-chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Velocity',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            spanGaps: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    const rangeChart = new Chart(document.getElementById('range-chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Range',
                data: [],
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            spanGaps: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Function to update the chart
    const updateChart = (chart, newData) => {
        const timestamp = new Date().toLocaleTimeString(); // Generate current timestamp
        if (chart.data.labels.length > 50) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(newData);
        chart.update();
    };

    // Fetch data from server
    const fetchData = () => {
        fetch('/get-speed')
            .then(response => response.json())
            .then(data => {
                updateChart(velocityChart, data.speed);
                updateChart(rangeChart, data.range);
            })
            .catch(error => console.error('Error fetching data:', error));
    };

    // Fetch data periodically
    setInterval(fetchData, 200);
});