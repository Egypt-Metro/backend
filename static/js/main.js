// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Metro map interactivity
    const map = document.querySelector('.metro-map');
    const stations = document.querySelectorAll('.station-point');
    
    stations.forEach(station => {
        station.addEventListener('click', () => {
            showStationInfo(station.dataset.stationId);
        });
    });

    // API documentation search
    const searchInput = document.querySelector('.api-search');
    const apiEndpoints = document.querySelectorAll('.api-list li');
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            apiEndpoints.forEach(endpoint => {
                const text = endpoint.textContent.toLowerCase();
                endpoint.style.display = text.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});