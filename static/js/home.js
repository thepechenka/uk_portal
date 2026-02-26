// Анимация появления элементов при скролле
document.addEventListener('DOMContentLoaded', function() {
    const fadeElements = document.querySelectorAll('.fade-in-up');

    const fadeInOnScroll = function() {
        fadeElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;

            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('active');
            }
        });
    };

    fadeInOnScroll();
    window.addEventListener('scroll', fadeInOnScroll);
});

// Карусель отзывов
document.addEventListener('DOMContentLoaded', function() {
    const track = document.getElementById('reviewsTrack');
    const prevBtn = document.getElementById('prevReview');
    const nextBtn = document.getElementById('nextReview');
    const indicatorsContainer = document.getElementById('reviewIndicators');

    if (!track || !prevBtn || !nextBtn) return;

    function initCarousel() {
        const items = document.querySelectorAll('.review-item');
        if (items.length === 0) return;

        const itemsPerView = window.innerWidth <= 768 ? 1 : window.innerWidth <= 992 ? 2 : 3;
        const totalItems = items.length;
        const maxIndex = Math.max(0, totalItems - itemsPerView);
        let currentIndex = 0;

        indicatorsContainer.innerHTML = '';
        for (let i = 0; i <= maxIndex; i++) {
            const dot = document.createElement('button');
            dot.className = `indicator-dot ${i === 0 ? 'active' : ''}`;
            dot.addEventListener('click', () => {
                currentIndex = i;
                updateCarousel(items, itemsPerView, maxIndex, currentIndex);
            });
            indicatorsContainer.appendChild(dot);
        }

        function updateCarousel(items, itemsPerView, maxIndex, currentIndex) {
            const containerWidth = document.querySelector('.reviews-container').offsetWidth;
            const gap = 20;
            const itemWidth = (containerWidth - (itemsPerView - 1) * gap) / itemsPerView;
            const translateX = -currentIndex * (itemWidth + gap);
            track.style.transform = `translateX(${translateX}px)`;

            const dots = document.querySelectorAll('.indicator-dot');
            dots.forEach((dot, idx) => {
                dot.classList.toggle('active', idx === currentIndex);
            });

            prevBtn.classList.toggle('disabled', currentIndex === 0);
            nextBtn.classList.toggle('disabled', currentIndex >= maxIndex);
        }

        prevBtn.onclick = () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateCarousel(items, itemsPerView, maxIndex, currentIndex);
            }
        };

        nextBtn.onclick = () => {
            if (currentIndex < maxIndex) {
                currentIndex++;
                updateCarousel(items, itemsPerView, maxIndex, currentIndex);
            }
        };

        window.addEventListener('resize', () => {
            const newItemsPerView = window.innerWidth <= 768 ? 1 : window.innerWidth <= 992 ? 2 : 3;
            if (newItemsPerView !== itemsPerView) {
                location.reload();
            } else {
                updateCarousel(items, itemsPerView, maxIndex, currentIndex);
            }
        });

        updateCarousel(items, itemsPerView, maxIndex, currentIndex);
    }

    initCarousel();
});