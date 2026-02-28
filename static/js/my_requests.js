// Восстановление выбранных значений из URL
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);

    // Восстанавливаем статус
    const statusSelect = document.querySelector('select[name="status"]');
    if (urlParams.has('status')) {
        statusSelect.value = urlParams.get('status');
    }

    // Восстанавливаем тип заявки
    const typeSelect = document.querySelector('select[name="request_type"]');
    if (urlParams.has('request_type')) {
        typeSelect.value = urlParams.get('request_type');
    }

    // Восстанавливаем приоритет
    const prioritySelect = document.querySelector('select[name="priority"]');
    if (urlParams.has('priority')) {
        prioritySelect.value = urlParams.get('priority');
    }

    // Восстанавливаем дату
    const dateInput = document.querySelector('input[name="date"]');
    if (urlParams.has('date')) {
        dateInput.value = urlParams.get('date');
    }

    // Автоматическое скрытие алертов через 5 секунд
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});