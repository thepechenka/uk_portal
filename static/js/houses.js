let mainMap;
let mainPlacemarks = {};
let housesData = [];

// Загрузка домов из API
async function loadHouses() {
    try {
        const response = await fetch('/api/houses/');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        housesData = await response.json();

        document.getElementById('totalHouses').textContent = housesData.length;
        const totalApartments = housesData.reduce((sum, house) => sum + (house.apartments_count || 0), 0);
        document.getElementById('totalApartments').textContent = totalApartments.toLocaleString();

        renderHouses();
        if (mainMap) addMarkersToMap();

    } catch (error) {
        document.getElementById('housesContainer').innerHTML = `
            <div class="col-12 text-center text-danger">
                <p>Ошибка загрузки данных. Пожалуйста, обновите страницу.</p>
            </div>
        `;
    }
}

// Генерация карточек домов
function renderHouses() {
    const container = document.getElementById('housesContainer');
    if (!container) return;
    container.innerHTML = '';

    if (housesData.length === 0) {
        container.innerHTML = `<div class="col-12 text-center"><p class="text-muted">Нет добавленных домов</p></div>`;
        return;
    }

    housesData.forEach(house => {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-4';
        card.innerHTML = `
            <div class="card h-100 shadow-sm house-card" data-house-id="${house.id}">
                <div class="card-body">
                    <h5 class="card-title" style="color: #E2725B;">${house.address}</h5>
                    <div class="mini-map mb-3" id="miniMap${house.id}" style="height: 150px; border-radius: 8px; overflow: hidden;"></div>
                    <div class="row">
                        <div class="col-6"><p class="mb-1"><small class="text-muted">Год постройки:</small></p><p class="fw-bold">${house.built_year || 'н/д'}</p></div>
                        <div class="col-6"><p class="mb-1"><small class="text-muted">Этажность:</small></p><p class="fw-bold">${house.floor_count || 'н/д'} этажей</p></div>
                    </div>
                    <div class="row">
                        <div class="col-6"><p class="mb-1"><small class="text-muted">Квартиры:</small></p><p class="fw-bold">${house.apartments_count || 'н/д'}</p></div>
                        <div class="col-6"><p class="mb-1"><small class="text-muted">Подъезды:</small></p><p class="fw-bold">${house.entrance_count || 'н/д'}</p></div>
                    </div>
                    <div class="d-grid">
                        <button class="btn btn-outline-primary btn-sm btn-show-details" data-house-id="${house.id}">
                            <i class="bi bi-info-circle me-1"></i>Подробные характеристики
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
    setTimeout(createMiniMaps, 500);
}

// Создание мини-карт
function createMiniMaps() {
    housesData.forEach(house => {
        if (!house.coords) return;
        const mapContainer = document.getElementById(`miniMap${house.id}`);
        if (!mapContainer) return;
        try {
            new ymaps.Map(mapContainer, {
                center: house.coords,
                zoom: 16,
                controls: []
            }).geoObjects.add(new ymaps.Placemark(house.coords, {}, {
                preset: 'islands#circleDotIcon',
                iconColor: '#E2725B'
            }));
        } catch (e) {}
    });
}

// Добавление меток на карту
function addMarkersToMap() {
    housesData.forEach(house => {
        if (!house.coords) return;
        const placemark = new ymaps.Placemark(
            house.coords,
            {
                balloonContent: `
                    <div style="padding: 10px;">
                        <h6 style="margin: 0 0 10px; color: #E2725B;">${house.address}</h6>
                        <div><small>Год:</small> <strong>${house.built_year || 'н/д'}</strong></div>
                        <div><small>Этажей:</small> <strong>${house.floor_count || 'н/д'}</strong></div>
                        <div><small>Квартир:</small> <strong>${house.apartments_count || 'н/д'}</strong></div>
                        <button class="btn btn-sm btn-primary mt-2 w-100" onclick="showHouseDetails(${house.id})">Подробнее</button>
                    </div>
                `,
                hintContent: house.address
            },
            { preset: 'islands#circleIcon', iconColor: '#E2725B' }
        );
        mainMap.geoObjects.add(placemark);
        mainPlacemarks[house.id] = placemark;
    });
}

// Показать все дома
function showAllHouses() {
    if (!mainMap) return;
    const bounds = mainMap.geoObjects.getBounds();
    if (bounds) mainMap.setBounds(bounds, { checkZoomRange: true, zoomMargin: 50 });
    document.getElementById('map').scrollIntoView({ behavior: 'smooth' });
}

// Открыть модалку
function showHouseDetails(houseId) {
    const house = housesData.find(h => h.id == houseId);
    if (!house) return;

    let reportsHtml = '';
    if (house.reports?.length) {
        reportsHtml = `
            <div class="details-section">
                <h6>ГОДОВЫЕ ОТЧЕТЫ</h6>
                <div class="reports-grid">
                    ${house.reports.map(report => `
                        <a href="${report.file_url}" target="_blank" class="report-item">
                            <i class="bi bi-file-pdf"></i>
                            <span class="report-year">${report.year}</span>
                        </a>
                    `).join('')}
                </div>
            </div>
        `;
    }

    document.getElementById('modalTitle').innerText = `${house.address} - Характеристики дома`;
    document.getElementById('modalBody').innerHTML = `
        <div class="house-details">
            <div class="details-section">
                <h6>ОСНОВНАЯ ИНФОРМАЦИЯ</h6>
                <div class="details-grid">
                    <div class="detail-item"><span class="detail-label">Год постройки</span><span class="detail-value">${house.built_year || 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Этажность</span><span class="detail-value">${house.floor_count || 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Тип дома</span><span class="detail-value">${house.house_type || 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Парадных</span><span class="detail-value">${house.entrance_count || 'н/д'}</span></div>
                </div>
            </div>

            <div class="details-section">
                <h6>ХАРАКТЕРИСТИКИ</h6>
                <div class="details-grid">
                    <div class="detail-item"><span class="detail-label">Тип перекрытий</span><span class="detail-value">${house.ceiling_type || 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Квартир</span><span class="detail-value">${house.apartments_count || 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Высота потолков</span><span class="detail-value">${house.ceiling_height ? house.ceiling_height + ' м' : 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Лифтов</span><span class="detail-value">${house.elevator_count || 'н/д'}</span></div>
                </div>
            </div>

            <div class="details-section">
                <h6>КОММУНИКАЦИИ И СОСТОЯНИЕ</h6>
                <div class="details-grid">
                    <div class="detail-item"><span class="detail-label">Газ</span><span class="detail-value">${house.has_gas ? 'Да' : 'Нет'}</span></div>
                    <div class="detail-item"><span class="detail-label">Мусоропровод</span><span class="detail-value">${house.has_garbage_chute ? 'Да' : 'Нет'}</span></div>
                    <div class="detail-item"><span class="detail-label">Отопление</span><span class="detail-value">${house.heating_type || 'н/д'}</span></div>
                    <div class="detail-item"><span class="detail-label">Аварийность</span><span class="detail-value">${house.is_emergency ? 'Да' : 'Нет'}</span></div>
                    <div class="detail-item"><span class="detail-label">Под снос</span><span class="detail-value">${house.is_demolition ? 'Да' : 'Нет'}</span></div>
                </div>
            </div>

            ${reportsHtml}
        </div>
    `;
    new bootstrap.Modal(document.getElementById('houseModal')).show();
}

// Инициализация карты
ymaps.ready(function() {
    mainMap = new ymaps.Map('map', {
        center: [53.757, 87.12],
        zoom: 12,
        controls: ['zoomControl', 'fullscreenControl']
    });
    loadHouses();
});

// Обработчики
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('showAllHousesBtn')?.addEventListener('click', showAllHouses);

    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.btn-show-details');
        if (btn) showHouseDetails(btn.getAttribute('data-house-id'));
    });

    new MutationObserver(() => {
        document.querySelectorAll('.house-card').forEach(card => {
            const houseId = card.getAttribute('data-house-id');
            card.addEventListener('mouseenter', () => {
                mainPlacemarks[houseId]?.options.set('iconColor', '#ff4444');
                card.style.transform = 'translateY(-5px)';
                card.style.boxShadow = '0 10px 20px rgba(226, 114, 91, 0.3)';
            });
            card.addEventListener('mouseleave', () => {
                mainPlacemarks[houseId]?.options.set('iconColor', '#E2725B');
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '';
            });
        });
    }).observe(document.getElementById('housesContainer'), { childList: true, subtree: true });
});