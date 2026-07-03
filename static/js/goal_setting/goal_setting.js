document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для всех radio-кнопок, у которых имя начинается с "question_"
    document.querySelectorAll('input[type="radio"][name^="question_"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            const nameParts = this.name.split('_');
            const qNum = nameParts[1];
            const wrapper = document.getElementById('custom_wrapper_' + qNum);
            const customInput = document.getElementById('id_' + nameParts[0] + '_' + qNum + '_custom');

            if (this.value === 'custom') {
                if (wrapper) wrapper.style.display = 'block';
                if (customInput) customInput.required = true;
            } else {
                if (wrapper) wrapper.style.display = 'none';
                if (customInput) customInput.required = false;
            }
        });
    });

    // При загрузке страницы проверить, не выбрана ли уже опция "custom"
    document.querySelectorAll('input[type="radio"][name^="question_"]:checked').forEach(function(radio) {
        if (radio.value === 'custom') {
            const nameParts = radio.name.split('_');
            const qNum = nameParts[1];
            const wrapper = document.getElementById('custom_wrapper_' + qNum);
            const customInput = document.getElementById('id_' + nameParts[0] + '_' + qNum + '_custom');

            if (wrapper) wrapper.style.display = 'block';
            if (customInput) customInput.required = true;
        }
    });
});
