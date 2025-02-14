// Image loading optimization
document.addEventListener('DOMContentLoaded', function() {
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.onload = () => img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Responsive image sizing
    function handleResponsiveImages() {
        const contentWidth = document.querySelector('.container').offsetWidth;
        const images = document.querySelectorAll('.responsive-img');
        
        images.forEach(img => {
            if (contentWidth < 768) {
                img.style.maxWidth = '100%';
            } else {
                img.style.maxWidth = '75%';
            }
        });
    }

    window.addEventListener('resize', handleResponsiveImages);
    handleResponsiveImages();
});