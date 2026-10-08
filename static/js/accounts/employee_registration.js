document.addEventListener('DOMContentLoaded', function () {
    // ========== Элементы ==========
    const districtSelect = document.getElementById('district-select');
    const orgTypeSelect = document.getElementById('org-type-select');
    const organizationSelect = document.getElementById('organization-select');

    const isUnemployed = document.getElementById('id_is_unemployed');
    const organizationBlock = document.getElementById('organizationBlock');

    const positionLevelSelect = document.getElementById('position-level-select');
    const positionWrapper = document.getElementById('position-wrapper');

    const URLS = Object.assign(
        {
            organizations: '/accounts/get-organizations-ajax/',
            positions: '/accounts/get-positions-ajax/',
        },
        window.ACCOUNTS_URLS || {}
    );

    // Типы организаций, для которых нужен выпадающий список должностей.
    const POSITION_SELECT_ORG_TYPES = ['Общее образование'];

    // ========== Фильтрация организаций ==========
    function updateOrganizations() {
        if (!organizationSelect) return;

        const districtId = districtSelect ? districtSelect.value : '';
        const orgTypeId = orgTypeSelect ? orgTypeSelect.value : '';

        const params = new URLSearchParams();
        if (districtId) params.append('district_id', districtId);
        if (orgTypeId) params.append('org_type_id', orgTypeId);

        fetch(URLS.organizations + '?' + params.toString())
            .then(r => (r.ok ? r.json() : Promise.reject(r)))
            .then(data => {
                const currentValue = organizationSelect.value;
                organizationSelect.innerHTML = '<option value="">---------</option>';
                data.organizations.forEach(org => {
                    const option = document.createElement('option');
                    option.value = org.id;
                    option.textContent = org.text;
                    organizationSelect.appendChild(option);
                });
                if (currentValue) organizationSelect.value = currentValue;
            })
            .catch(err => console.error('Ошибка загрузки организаций:', err));
    }

    // ========== Проверка: нужен ли выпадающий список ==========
    function isPositionSelectAllowed() {
        if (!orgTypeSelect) return false;
        const selectedText = (
            orgTypeSelect.options[orgTypeSelect.selectedIndex]?.text || ''
        ).trim();
        return POSITION_SELECT_ORG_TYPES.includes(selectedText);
    }

    // ========== Получить текущее значение поля «Должность» ==========
    function getPositionValue() {
        const input = document.getElementById('position-input');
        const select = document.getElementById('position-select');
        if (input) return input.value;
        if (select) return select.value;
        return '';
    }

    // ========== Экранирование HTML ==========
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    // ========== Рендер поля «Должность» ==========
    // Если тип — «Общее образование» → <select>.
    // Иначе → <input type="text">.
    function renderPositionField(preserveValue) {
        if (!positionWrapper) return;

        const current = preserveValue !== undefined ? preserveValue : getPositionValue();

        if (isPositionSelectAllowed()) {
            positionWrapper.innerHTML =
                '<select id="position-select" name="position" class="form-control">' +
                '<option value="">— Сначала выберите категорию —</option>' +
                '</select>';
            loadPositions(current);
        } else {
            positionWrapper.innerHTML =
                '<input type="text" id="position-input" name="position" ' +
                'class="form-control" placeholder="Введите должность" ' +
                'value="' + escapeHtml(current) + '">';
        }
    }

    // ========== Загрузка должностей в <select> ==========
    function loadPositions(preserveValue) {
        const positionSelect = document.getElementById('position-select');
        if (!positionSelect) return;

        const level = positionLevelSelect ? positionLevelSelect.value : '';
        const orgTypeId = orgTypeSelect ? orgTypeSelect.value : '';

        if (!level) {
            positionSelect.innerHTML =
                '<option value="">— Сначала выберите категорию —</option>';
            return;
        }

        positionSelect.innerHTML = '<option value="">— Загрузка… —</option>';

        const params = new URLSearchParams({ position_level: level });
        if (orgTypeId) params.append('organization_type_id', orgTypeId);

        fetch(URLS.positions + '?' + params.toString())
            .then(r => (r.ok ? r.json() : Promise.reject(r)))
            .then(data => {
                positionSelect.innerHTML =
                    '<option value="">— Выберите должность —</option>';
                data.positions.forEach(p => {
                    const option = document.createElement('option');
                    option.value = p.text;
                    option.textContent = p.text;
                    positionSelect.appendChild(option);
                });
                if (preserveValue) {
                    positionSelect.value = preserveValue;
                    if (positionSelect.value !== preserveValue) {
                        positionSelect.value = '';
                    }
                }
            })
            .catch(err => {
                console.error('Ошибка загрузки должностей:', err);
                positionSelect.innerHTML =
                    '<option value="">— Ошибка загрузки —</option>';
            });
    }

    // ========== Обработчики ==========
    if (districtSelect) {
        districtSelect.addEventListener('change', updateOrganizations);
    }

    if (orgTypeSelect) {
        orgTypeSelect.addEventListener('change', function () {
            updateOrganizations();
            // Сохраняем то, что уже введено, и перерисовываем поле
            const previous = getPositionValue();
            renderPositionField(previous);
        });
    }

    if (positionLevelSelect) {
        positionLevelSelect.addEventListener('change', function () {
            // Перезагрузка списка нужна только для <select>
            if (isPositionSelectAllowed()) loadPositions(null);
        });
    }

    // ========== Скрытие блока для безработных ==========
    function toggleUnemployedFields() {
        if (!isUnemployed || !organizationBlock) return;

        if (isUnemployed.checked) {
            organizationBlock.style.display = 'none';
            if (organizationSelect) organizationSelect.value = '';
            if (districtSelect) districtSelect.value = '';
            if (orgTypeSelect) orgTypeSelect.value = '';
            if (positionLevelSelect) positionLevelSelect.value = '';

            const input = document.getElementById('position-input');
            const select = document.getElementById('position-select');
            if (input) input.value = '';
            if (select) select.value = '';
        } else {
            organizationBlock.style.display = 'block';
        }
    }

    if (isUnemployed) {
        isUnemployed.addEventListener('change', toggleUnemployedFields);
        toggleUnemployedFields();
    }

    // ========== Первичная инициализация ==========
    if (!isUnemployed || !isUnemployed.checked) {
        updateOrganizations();
        // Рисуем поле в зависимости от текущего выбора типа организации.
        // Если тип ещё не выбран — покажется <input type="text">.
        renderPositionField();
    }
});
