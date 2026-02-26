ymaps.ready(function() {
    var contactMap = new ymaps.Map('contact-map', {
        center: [53.768544, 87.127878],
        zoom: 17,
        controls: ['zoomControl', 'fullscreenControl']
    });

    var placemark = new ymaps.Placemark([53.768544, 87.127878], {
        hintContent: 'ООО "Новый город"',
        balloonContent: '<strong>УК "Новый город"</strong><br>ул. Павловского, 11А<br>+7 3843 20-02-82'
    }, {
        preset: 'islands#circleIcon',
        iconColor: '#E2725B'
    });

    contactMap.geoObjects.add(placemark);
});