$(document).ready(function() {
    // Пытаемся найти поля разными способами
    var districtSelect = $('#id_district');
    if (!districtSelect.length) {
        districtSelect = $('#district');
    }
    if (!districtSelect.length) {
        districtSelect = $('select[name="district"]');
    }

    var orgTypeSelect = $('#id_organization_type');
    if (!orgTypeSelect.length) {
        orgTypeSelect = $('#organization_type');
    }
    if (!orgTypeSelect.length) {
        orgTypeSelect = $('select[name="organization_type"]');
    }

    var organizationSelect = $('#id_organization');
    if (!organizationSelect.length) {
        organizationSelect = $('#organization');
    }
    if (!organizationSelect.length) {
        organizationSelect = $('select[name="organization"]');
    }

    // Функция обновления списка организаций
    function updateOrganizations() {
        var districtId = districtSelect.val();
        var orgTypeId = orgTypeSelect.val();

        console.log('Фильтрация: район=' + districtId + ', тип=' + orgTypeId);

        var url = '/accounts/get-organizations-ajax/';
        var params = {};

        if (districtId && districtId !== '') {
            params.district_id = districtId;
        }
        if (orgTypeId && orgTypeId !== '') {
            params.org_type_id = orgTypeId;
        }

        $.ajax({
            url: url,
            data: params,
            dataType: 'json',
            success: function(data) {
                console.log('Получено организаций:', data.organizations.length);
                organizationSelect.empty();
                organizationSelect.append('<option value="">---------</option>');
                $.each(data.organizations, function(index, org) {
                    organizationSelect.append('<option value="' + org.id + '">' + org.text + '</option>');
                });
            },
            error: function(xhr, status, error) {
                console.error('Ошибка загрузки организаций:', error);
            }
        });
    }

    // Обновляем при изменении района или типа организации
    districtSelect.on('change', function() {
        console.log('Район изменён');
        updateOrganizations();
    });

    orgTypeSelect.on('change', function() {
        console.log('Тип организации изменён');
        updateOrganizations();
    });

    // Загружаем все организации при загрузке страницы
    updateOrganizations();
});
