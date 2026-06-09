$(document).ready(function() {
    // Автоматическая отправка формы при изменении количества записей (если есть такой элемент)
    $('#id_per_page').on('change', function() {
        $(this).closest('form').submit();
    });

    // Подсветка строки таблицы при наведении
    $('#employeesTable tbody tr').hover(
        function() {
            $(this).addClass('table-hover');
        },
        function() {
            $(this).removeClass('table-hover');
        }
    );

    // Обработка формы поиска - предотвращение отправки пустого запроса
    $('.search-form').on('submit', function() {
        var searchInput = $(this).find('input[name="search"]');
        if (searchInput.val().trim() === '') {
            var url = new URL(window.location.href);
            url.searchParams.delete('search');
            window.location.href = url.toString();
            return false;
        }
        return true;
    });

    // Поддержка Enter в поле поиска
    $('#search-input').on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            $(this).closest('form').submit();
        }
    });
});
