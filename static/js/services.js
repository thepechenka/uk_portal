document.addEventListener('DOMContentLoaded', function() {
    // Плавный скролл до разделов (если есть якорные ссылки)
    const sectionTitles = document.querySelectorAll('.services-section-title');

    if (sectionTitles.length > 0) {
        console.log('Страница услуг загружена. Найдено разделов:', sectionTitles.length);
    }

    // Функция для копирования цены (если понадобится)
    const prices = document.querySelectorAll('.services-item-price');
    prices.forEach(price => {
        price.addEventListener('click', function(e) {
            // Создаем временный элемент для копирования
            const tempInput = document.createElement('input');
            tempInput.value = this.textContent;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);

            // Показываем уведомление (можно заменить на всплывашку)
            const originalText = this.textContent;
            this.textContent = '✓ Скопировано';
            this.style.opacity = '0.7';

            setTimeout(() => {
                this.textContent = originalText;
                this.style.opacity = '1';
            }, 1000);
        });
    });

    // Функция для выделения цены при наведении
    const items = document.querySelectorAll('.services-item');
    items.forEach(item => {
        item.addEventListener('mouseenter', function() {
            const price = this.querySelector('.services-item-price');
            if (price) {
                price.style.transform = 'scale(1.05)';
                price.style.transition = 'transform 0.2s ease';
            }
        });

        item.addEventListener('mouseleave', function() {
            const price = this.querySelector('.services-item-price');
            if (price) {
                price.style.transform = 'scale(1)';
            }
        });
    });
});

// Функция для поиска по услугам (если понадобится в будущем)
function filterServices(searchTerm) {
    const sections = document.querySelectorAll('.services-section');
    const items = document.querySelectorAll('.services-item');
    const searchLower = searchTerm.toLowerCase();

    items.forEach(item => {
        const label = item.querySelector('.services-item-label');
        if (label) {
            const text = label.textContent.toLowerCase();
            if (text.includes(searchLower)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        }
    });

    sections.forEach(section => {
        const visibleItems = section.querySelectorAll('.services-item[style="display: flex;"]');
        if (visibleItems.length === 0) {
            section.style.display = 'none';
        } else {
            section.style.display = 'block';
        }
    });
}