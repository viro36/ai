document.addEventListener('DOMContentLoaded', function() {
    // ========== Получаем элементы ==========
    const districtSelect = document.getElementById('district-select');
    const orgTypeSelect = document.getElementById('org-type-select');
    const organizationSelect = document.getElementById('organization-select');

    const isUnemployed = document.getElementById('id_is_unemployed');
    const organizationBlock = document.getElementById('organizationBlock');
    const positionField = document.getElementById('id_position');
    const positionLevelField = document.getElementById('id_position_level');

    // ========== Фильтрация организаций ==========
    function updateOrganizations() {
        if (!organizationSelect) return;

        const districtId = districtSelect ? districtSelect.value : '';
        const orgTypeId = orgTypeSelect ? orgTypeSelect.value : '';

        const params = new URLSearchParams();
        if (districtId) params.append('district_id', districtId);
        if (orgTypeId) params.append('org_type_id', orgTypeId);

        fetch('/accounts/get-organizations-ajax/?' + params.toString())
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                // Сохраняем текущее выбранное значение (если есть)
                const currentValue = organizationSelect.value;

                organizationSelect.innerHTML = '<option value="">---------</option>';
                data.organizations.forEach(org => {
                    const option = document.createElement('option');
                    option.value = org.id;
                    option.textContent = org.text;
                    organizationSelect.appendChild(option);
                });

                // Восстанавливаем выбор, если он ещё доступен
                if (currentValue) {
                    organizationSelect.value = currentValue;
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки организаций:', error);
            });
    }

    if (districtSelect) districtSelect.addEventListener('change', updateOrganizations);
    if (orgTypeSelect) orgTypeSelect.addEventListener('change', updateOrganizations);

    // ========== Скрытие блока организации для безработных ==========
    // ВАЖНО: не используем disabled — отключённые поля не отправляются на сервер.
    // Вместо этого очищаем значения и скрываем блок.
    function toggleUnemployedFields() {
        if (!isUnemployed || !organizationBlock) return;

        if (isUnemployed.checked) {
            organizationBlock.style.display = 'none';

            // Очищаем значения, но НЕ отключаем поля
            if (organizationSelect) organizationSelect.value = '';
            if (districtSelect) districtSelect.value = '';
            if (orgTypeSelect) orgTypeSelect.value = '';
            if (positionField) positionField.value = '';
            if (positionLevelField) positionLevelField.value = '';
        } else {
            organizationBlock.style.display = 'block';
        }
    }

    if (isUnemployed) {
        isUnemployed.addEventListener('change', toggleUnemployedFields);
        toggleUnemployedFields();
    }

    // ========== Загружаем организации при загрузке страницы ==========
    // Не загружаем, если пользователь уже отметил "Безработный"
    if (!isUnemployed || !isUnemployed.checked) {
        updateOrganizations();
    }
});
