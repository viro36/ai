document.addEventListener('DOMContentLoaded', function () {
    // ========== Контекст ==========
    const CTX = Object.assign(
        {
            organizationTypeId: '',
            organizationTypeName: '',
            currentPosition: '',
            urls: { positions: '/accounts/get-positions-ajax/' },
        },
        window.EMPLOYEE_PROFILE_CONTEXT || {}
    );

    const POSITION_SELECT_ORG_TYPES = ['Общее образование'];

    // ========== Элементы ==========
    const isUnemployed = document.getElementById('id_is_unemployed');
    const organizationBlock = document.getElementById('organizationBlock');

    const positionWrapper = document.getElementById('position-wrapper');
    const positionLevelSelect = document.getElementById('position-level-select');

    const organizationIdInput = document.getElementById('organization-id');
    const organizationNameSpan = document.getElementById('organization-name');
    const organizationInnSpan = document.getElementById('organization-inn');

    const districtSelect = document.getElementById('modal-district-select');
    const orgTypeSelect = document.getElementById('modal-org-type-select');
    const organizationSelect = document.getElementById('modal-organization-select');
    const saveOrgBtn = document.getElementById('save-org-btn');
    const orgModal = document.getElementById('orgModal');

    // Текущий тип организации. Обновляется при выборе в модалке.
    let currentOrgTypeId = CTX.organizationTypeId || '';
    let currentOrgTypeName = CTX.organizationTypeName || '';

    // ========== Утилиты ==========
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function isPositionSelectAllowed() {
        return POSITION_SELECT_ORG_TYPES.includes((currentOrgTypeName || '').trim());
    }

    function getPositionValue() {
        const input = document.getElementById('position-input');
        const select = document.getElementById('position-select');
        if (input) return input.value;
        if (select) return select.value;
        return '';
    }

    // ========== Рендер поля «Должность» ==========
    function renderPositionField(preserveValue) {
        if (!positionWrapper) return;

        const value = preserveValue !== undefined ? preserveValue : getPositionValue();

        if (isPositionSelectAllowed()) {
            positionWrapper.innerHTML =
                '<select id="position-select" name="position" class="form-control">' +
                '<option value="">— Сначала выберите категорию —</option>' +
                '</select>';
            loadPositions(value);
        } else {
            positionWrapper.innerHTML =
                '<input type="text" id="position-input" name="position" ' +
                'class="form-control" placeholder="Введите должность" ' +
                'value="' + escapeHtml(value) + '">';
        }
    }

    // ========== Загрузка должностей ==========
    function loadPositions(preserveValue) {
        const positionSelect = document.getElementById('position-select');
        if (!positionSelect) return;

        const level = positionLevelSelect ? positionLevelSelect.value : '';
        if (!level) {
            positionSelect.innerHTML =
                '<option value="">— Сначала выберите категорию —</option>';
            return;
        }

        positionSelect.innerHTML = '<option value="">— Загрузка… —</option>';

        const params = new URLSearchParams({ position_level: level });
        if (currentOrgTypeId) params.append('organization_type_id', currentOrgTypeId);

        fetch(CTX.urls.positions + '?' + params.toString())
            .then(r => (r.ok ? r.json() : Promise.reject(r)))
            .then(data => {
                positionSelect.innerHTML =
                    '<option value="">— Выберите должность —</option>';
                data.positions.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.text;
                    opt.textContent = p.text;
                    positionSelect.appendChild(opt);
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

    // ========== Скрытие блока для безработных ==========
    function toggleUnemployedFields() {
        if (!isUnemployed || !organizationBlock) return;

        if (isUnemployed.checked) {
            organizationBlock.style.display = 'none';

            if (organizationIdInput) organizationIdInput.value = '';
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

    // ========== Модалка выбора организации ==========
    function updateOrganizations() {
        if (!organizationSelect) return;

        const districtId = districtSelect ? districtSelect.value : '';
        const orgTypeId = orgTypeSelect ? orgTypeSelect.value : '';

        const params = new URLSearchParams();
        if (districtId) params.append('district_id', districtId);
        if (orgTypeId) params.append('org_type_id', orgTypeId);

        fetch('/accounts/get-organizations-ajax/?' + params.toString())
            .then(r => (r.ok ? r.json() : Promise.reject(r)))
            .then(data => {
                organizationSelect.innerHTML = '<option value="">---------</option>';
                data.organizations.forEach(org => {
                    const opt = document.createElement('option');
                    opt.value = org.id;
                    opt.textContent = org.text;
                    opt.setAttribute('data-inn', org.inn || '');
                    opt.setAttribute(
                        'data-org-type-id',
                        org.organization_type_id || ''
                    );
                    opt.setAttribute(
                        'data-org-type-name',
                        org.organization_type_name || ''
                    );
                    organizationSelect.appendChild(opt);
                });
            })
            .catch(err => console.error('Ошибка загрузки организаций:', err));
    }

    if (districtSelect) districtSelect.addEventListener('change', updateOrganizations);
    if (orgTypeSelect) orgTypeSelect.addEventListener('change', updateOrganizations);

    if (orgModal) {
        orgModal.addEventListener('show.bs.modal', function () {
            updateOrganizations();
        });
    }

    function saveSelectedOrganization() {
        if (!organizationSelect) return;

        const opt = organizationSelect.options[organizationSelect.selectedIndex];
        if (!opt || !opt.value) return;

        const orgId = opt.value;
        const orgName = opt.textContent;
        const orgInn = opt.getAttribute('data-inn') || '';

        if (organizationIdInput) organizationIdInput.value = orgId;
        if (organizationNameSpan) organizationNameSpan.textContent = orgName;
        if (organizationInnSpan) organizationInnSpan.textContent = orgInn;

        // Обновляем тип организации по выбранной опции
        const typeId = opt.getAttribute('data-org-type-id') || '';
        const typeName = opt.getAttribute('data-org-type-name') || '';

        if (typeName) {
            currentOrgTypeId = typeId;
            currentOrgTypeName = typeName;
        } else if (orgTypeSelect && orgTypeSelect.value) {
            // Fallback: берём тип, выбранный в фильтре модалки
            currentOrgTypeId = orgTypeSelect.value;
            currentOrgTypeName =
                orgTypeSelect.options[orgTypeSelect.selectedIndex].textContent.trim();
        } else {
            currentOrgTypeId = '';
            currentOrgTypeName = '';
        }

        // Перерисовываем поле «Должность» с учётом нового типа
        const previous = getPositionValue();
        renderPositionField(previous);

        const modal = bootstrap.Modal.getInstance(orgModal);
        if (modal) modal.hide();
    }

    if (saveOrgBtn) saveOrgBtn.addEventListener('click', saveSelectedOrganization);

    // ========== Смена категории ==========
    if (positionLevelSelect) {
        positionLevelSelect.addEventListener('change', function () {
            if (isPositionSelectAllowed()) loadPositions(null);
        });
    }

    // ========== Первичная инициализация ==========
    if (!isUnemployed || !isUnemployed.checked) {
        renderPositionField(CTX.currentPosition || getPositionValue());
    }
});
