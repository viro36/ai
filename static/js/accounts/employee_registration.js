document.addEventListener('DOMContentLoaded', function() {
    // ========== Фильтрация организаций ==========
    const districtSelect = document.getElementById('id_district');
    const orgTypeSelect = document.getElementById('id_organization_type');
    const organizationSelect = document.getElementById('id_organization');

    function updateOrganizations() {
        if (!organizationSelect) return;

        const districtId = districtSelect ? districtSelect.value : '';
        const orgTypeId = orgTypeSelect ? orgTypeSelect.value : '';

        const params = new URLSearchParams();
        if (districtId) params.append('district_id', districtId);
        if (orgTypeId) params.append('org_type_id', orgTypeId);

        fetch('/accounts/get-organizations-ajax/?' + params.toString())
            .then(response => response.json())
            .then(data => {
                organizationSelect.innerHTML = '<option value="">---------</option>';
                data.organizations.forEach(org => {
                    const option = document.createElement('option');
                    option.value = org.id;
                    option.textContent = org.text;
                    organizationSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Ошибка загрузки организаций:', error);
            });
    }

    if (districtSelect) districtSelect.addEventListener('change', updateOrganizations);
    if (orgTypeSelect) orgTypeSelect.addEventListener('change', updateOrganizations);

    // Загружаем все организации при загрузке страницы
    updateOrganizations();

    // ========== Скрытие блока организации для безработных ==========
    const isUnemployed = document.getElementById('id_is_unemployed');
    const organizationBlock = document.getElementById('organizationBlock');
    const positionField = document.getElementById('id_position');
    const positionLevelField = document.getElementById('id_position_level');

    function toggleUnemployedFields() {
        if (!isUnemployed || !organizationBlock) return;

        if (isUnemployed.checked) {
            organizationBlock.style.display = 'none';

            if (organizationSelect) {
                organizationSelect.value = '';
                organizationSelect.disabled = true;
            }
            if (districtSelect) districtSelect.disabled = true;
            if (orgTypeSelect) orgTypeSelect.disabled = true;
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

            if (organizationSelect) organizationSelect.disabled = false;
            if (districtSelect) districtSelect.disabled = false;
            if (orgTypeSelect) orgTypeSelect.disabled = false;
            if (positionField) positionField.disabled = false;
            if (positionLevelField) positionLevelField.disabled = false;
        }
    }

    if (isUnemployed) {
        isUnemployed.addEventListener('change', toggleUnemployedFields);
        toggleUnemployedFields();
    }
});
