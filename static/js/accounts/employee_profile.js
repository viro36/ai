document.addEventListener('DOMContentLoaded', function() {
    // ========== Скрытие блока организации для безработных ==========
    const isUnemployed = document.getElementById('id_is_unemployed');
    const organizationBlock = document.getElementById('organizationBlock');
    const organizationField = document.getElementById('id_organization');
    const positionField = document.getElementById('id_position');
    const positionLevelField = document.getElementById('id_position_level');

    function toggleUnemployedFields() {
        if (!isUnemployed || !organizationBlock) return;

        if (isUnemployed.checked) {
            organizationBlock.style.display = 'none';

            if (organizationField) {
                organizationField.value = '';
                organizationField.disabled = true;
            }
            if (positionField) {
                positionField.value = '';
                positionField.disabled = true;
            }
            if (positionLevelField) {
                positionLevelField.value = '';
                positionLevelField.disabled = true;
            }
        } else {
            organizationBlock.style.display = 'block';

            if (organizationField) organizationField.disabled = false;
            if (positionField) positionField.disabled = false;
            if (positionLevelField) positionLevelField.disabled = false;
        }
    }

    if (isUnemployed) {
        isUnemployed.addEventListener('change', toggleUnemployedFields);
        toggleUnemployedFields();
    }

    // ========== Модальное окно выбора организации ==========
    const districtSelect = document.getElementById('modal-district-select');
    const orgTypeSelect = document.getElementById('modal-org-type-select');
    const organizationSelect = document.getElementById('modal-organization-select');
    const saveOrgBtn = document.getElementById('save-org-btn');

    function updateOrganizations() {
        const districtId = districtSelect ? districtSelect.value : '';
        const orgTypeId = orgTypeSelect ? orgTypeSelect.value : '';

        const url = '/accounts/get-organizations-ajax/';
        const params = new URLSearchParams();

        if (districtId) params.append('district_id', districtId);
        if (orgTypeId) params.append('org_type_id', orgTypeId);

        fetch(url + '?' + params.toString())
            .then(response => response.json())
            .then(data => {
                if (!organizationSelect) return;

                organizationSelect.innerHTML = '<option value="">---------</option>';
                data.organizations.forEach(org => {
                    const option = document.createElement('option');
                    option.value = org.id;
                    option.textContent = org.text;
                    option.setAttribute('data-inn', org.inn);
                    organizationSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Ошибка загрузки организаций:', error);
            });
    }

    if (districtSelect) districtSelect.addEventListener('change', updateOrganizations);
    if (orgTypeSelect) orgTypeSelect.addEventListener('change', updateOrganizations);

    // Загружаем при открытии модалки
    const orgModal = document.getElementById('orgModal');
    if (orgModal) {
        orgModal.addEventListener('show.bs.modal', function() {
            updateOrganizations();
        });
    }

    // Сохранение выбранной организации
    function saveSelectedOrganization() {
        if (!organizationSelect) return;

        const selectedOption = organizationSelect.options[organizationSelect.selectedIndex];

        if (!selectedOption || !selectedOption.value) return;

        const orgId = selectedOption.value;
        const orgName = selectedOption.textContent;
        const orgInn = selectedOption.getAttribute('data-inn') || '';

        const orgIdInput = document.getElementById('organization-id');
        const orgNameSpan = document.getElementById('organization-name');
        const orgInnSpan = document.getElementById('organization-inn');

        if (orgIdInput) orgIdInput.value = orgId;
        if (orgNameSpan) orgNameSpan.textContent = orgName;
        if (orgInnSpan) orgInnSpan.textContent = orgInn;

        const modal = bootstrap.Modal.getInstance(orgModal);
        if (modal) modal.hide();
    }

    if (saveOrgBtn) {
        saveOrgBtn.addEventListener('click', saveSelectedOrganization);
    }
});
