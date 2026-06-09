// Общие скрипты для опросов

(function() {
    'use strict';

    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {

        // Обработка выбора вариантов ответа
        initScaleOptions();

        // Валидация формы перед отправкой
        initFormValidation();

        // Автосохранение (опционально)
        initAutoSave();

    });

    // Обработка кликов по вариантам ответа
    function initScaleOptions() {
        const scaleOptions = document.querySelectorAll('.scale-option');

        scaleOptions.forEach(option => {
            // Добавляем обработчик клика на карточку
            option.addEventListener('click', function(e) {
                // Игнорируем если клик был на инпуте или лейбле (чтобы избежать двойного срабатывания)
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'LABEL') {
                    return;
                }

                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change'));
                    triggerAutosave(radio);
                }
            });

            // Добавляем класс selected при выборе
            const radio = option.querySelector('input[type="radio"]');
            if (radio) {
                radio.addEventListener('change', function() {
                    // Убираем класс selected у всех опций
                    document.querySelectorAll('.scale-option').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    // Добавляем класс selected текущей опции
                    if (this.checked) {
                        option.classList.add('selected');
                    }
                });
            }
        });
    }

    // Валидация формы
    function initFormValidation() {
        const form = document.getElementById('surveyForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            const selected = document.querySelector('input[name="score"]:checked');
            if (!selected) {
                e.preventDefault();
                showAlert('Пожалуйста, выберите вариант ответа', 'warning');
            }
        });
    }

    // Автосохранение (сохраняет ответ при выборе)
    let autosaveTimeout = null;

    function initAutoSave() {
        // Проверяем, включено ли автосохранение
        const autosaveEnabled = document.body.dataset.autosave === 'true';
        if (!autosaveEnabled) return;

        const radioButtons = document.querySelectorAll('input[type="radio"][name="score"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                triggerAutosave(this);
            });
        });
    }

    function triggerAutosave(radio) {
        if (autosaveTimeout) {
            clearTimeout(autosaveTimeout);
        }

        autosaveTimeout = setTimeout(() => {
            const form = document.getElementById('surveyForm');
            if (form) {
                // Показываем индикатор сохранения
                showSavingIndicator(true);

                // Отправляем форму через fetch
                const formData = new FormData(form);
                fetch(window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    showSavingIndicator(false);
                    if (response.ok) {
                        showAutoSaveSuccess();
                    }
                })
                .catch(error => {
                    showSavingIndicator(false);
                    console.error('Autosave error:', error);
                });
            }
        }, 1000);
    }

    // Показ индикатора сохранения
    let savingIndicator = null;

    function showSavingIndicator(show) {
        if (!savingIndicator) {
            savingIndicator = document.createElement('div');
            savingIndicator.className = 'position-fixed bottom-0 end-0 m-3 p-2 bg-info text-white rounded shadow';
            savingIndicator.style.zIndex = '9999';
            savingIndicator.style.fontSize = '0.875rem';
            savingIndicator.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Сохранение...';
            document.body.appendChild(savingIndicator);
        }

        savingIndicator.style.display = show ? 'block' : 'none';
    }

    function showAutoSaveSuccess() {
        const successMsg = document.createElement('div');
        successMsg.className = 'position-fixed bottom-0 end-0 m-3 p-2 bg-success text-white rounded shadow';
        successMsg.style.zIndex = '9999';
        successMsg.style.fontSize = '0.875rem';
        successMsg.innerHTML = '<i class="fa-solid fa-check-circle me-1"></i> Ответ сохранён';
        document.body.appendChild(successMsg);

        setTimeout(() => {
            successMsg.remove();
        }, 2000);
    }

    // Показ уведомлений
    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    // Функция для печати результатов
    window.printResults = function() {
        window.print();
    };

    // Функция для скачивания результатов (заглушка)
    window.downloadResults = function(format = 'pdf') {
        alert(`Скачивание результатов в формате ${format.toUpperCase()} будет доступно в ближайшее время`);
    };

})();
