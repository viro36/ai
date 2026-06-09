/**
 * Модуль для динамической загрузки организаций через HTMX
 */
const OrganizationLoader = (function() {
    /**
     * Инициализация модуля
     */
    function init() {
        // Ждем загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupEventListeners);
        } else {
            setupEventListeners();
        }
    }

    /**
     * Настройка обработчиков событий
     */
    function setupEventListeners() {
        const districtSelect = document.getElementById('id_district');

        // Добавляем обработчик события change для отладки
        districtSelect.addEventListener('change', function(e) {
        });

        // Обработчик после запроса HTMX
        document.addEventListener('htmx:afterRequest', handleAfterRequest);
        document.addEventListener('htmx:beforeRequest', function(evt) {
        });
        document.addEventListener('htmx:afterOnLoad', function(evt) {
        });

        // Обработчик для сброса зависимых полей ПЕРЕД запросом
        districtSelect.addEventListener('htmx:beforeRequest', resetDependentFields);
    }

    /**
     * Обработка после запроса HTMX
     */
    function handleAfterRequest(evt) {
        if (evt.detail.target && evt.detail.target.id === 'id_organization_type_container') {
            const responseText = evt.detail.xhr.responseText;
            const container = document.getElementById('id_organization_type_container');

            // Если пришли только option, оборачиваем их в select
            if (responseText.trim().startsWith('<option')) {
                container.innerHTML = `<select name="organization_type" id="id_organization_type" class="form-select">${responseText}</select>`;
            }

            enableTypeSelect();
        }

        if (evt.detail.target && evt.detail.target.id === 'id_organization_container') {
            const responseText = evt.detail.xhr.responseText;
            if (responseText.trim().startsWith('<option')) {
                const container = document.getElementById('id_organization_container');
                container.innerHTML = `<select name="organization" id="id_organization" class="form-select">${responseText}</select>`;
            }
            enableOrganizationSelect();
        }
    }

    /**
     * Активировать и настроить select для типов организаций
     */
    function enableTypeSelect() {
        const typeSelect = document.getElementById('id_organization_type');
        typeSelect.disabled = false;

        // Добавляем атрибуты для HTMX
        typeSelect.setAttribute('hx-get', '/api/get-organizations-html/');
        typeSelect.setAttribute('hx-target', '#id_organization_container');
        typeSelect.setAttribute('hx-trigger', 'change');
        typeSelect.setAttribute('hx-indicator', '#type-indicator');
        typeSelect.setAttribute('hx-swap', 'innerHTML');
        typeSelect.setAttribute('name', 'type');
        typeSelect.setAttribute('hx-include', '#id_district');

        // Инициализируем HTMX для нового элемента
        if (typeof htmx !== 'undefined') {
            htmx.process(typeSelect);
        }
    }

    /**
     * Активировать select для организаций
     */
    function enableOrganizationSelect() {
        const orgSelect = document.getElementById('id_organization');
        orgSelect.disabled = false;
        orgSelect.setAttribute('name', 'organization');
    }

    /**
     * Сброс зависимых полей при изменении района
     */
    function resetDependentFields(evt) {

        // Сбрасываем тип организации
        const typeContainer = document.getElementById('id_organization_type_container');
        if (typeContainer) {
            typeContainer.innerHTML = '<select name="organization_type" id="id_organization_type" class="form-select" disabled><option value="">---------</option></select>';
        }

        // Сбрасываем организацию
        const orgContainer = document.getElementById('id_organization_container');
        if (orgContainer) {
            orgContainer.innerHTML = '<select name="organization" id="id_organization" class="form-select" disabled><option value="">---------</option></select>';
        }
    }

    // Публичный API
    return {
        init: init,
        enableTypeSelect: enableTypeSelect,
        enableOrganizationSelect: enableOrganizationSelect,
        resetDependentFields: resetDependentFields
    };
})();

// Автоматическая инициализация
OrganizationLoader.init();

// Экспорт для использования в других модулях
if (typeof window !== 'undefined') {
    window.OrganizationLoader = OrganizationLoader;
}
