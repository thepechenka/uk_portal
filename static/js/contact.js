ymaps.ready(function() {
    const mapElement = document.getElementById('contact-map');

    if (!mapElement) {
        console.error('Элемент #contact-map не найден!');
        return;
    }

    try {
        var contactMap = new ymaps.Map('contact-map', {
            center: [53.768544, 87.127878],
            zoom: 17,
            controls: ['zoomControl', 'fullscreenControl']
        });

        var placemark = new ymaps.Placemark([53.768544, 87.127878], {
            hintContent: 'УК "Новый город"',
            balloonContent: '<strong>ООО "Новый город"</strong><br>ул. Павловского, 11А<br>г. Новокузнецк'
        }, {
            preset: 'islands#circleIcon',
            iconColor: '#E2725B'
        });

        contactMap.geoObjects.add(placemark);

        console.log('Карта успешно загружена!');

    } catch (error) {
        console.error('Ошибка при создании карты:', error);
    }
});