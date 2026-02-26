ymaps.ready(function() {
    var companyMap = new ymaps.Map('company-map', {
        center: [53.768544, 87.127878],
        zoom: 17,
        controls: ['zoomControl']
    });

    var placemark = new ymaps.Placemark([53.768544, 87.127878], {
        hintContent: 'ООО "Новый город"',
        balloonContent: 'ул. Павловского, 11А'
    }, {
        preset: 'islands#circleIcon',
        iconColor: '#E2725B'
    });

    companyMap.geoObjects.add(placemark);
});