// Общие скрипты для опросов

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initScaleOptions();
        initOptionGroups();
        initFormValidation();
        initAutoSave();
    });

    // ============================================================
    // Шкала 1–5
    // ============================================================
    function initScaleOptions() {
        const scaleOptions = document.querySelectorAll('.scale-option');

        scaleOptions.forEach(option => {
            option.addEventListener('click', function (e) {
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

            const radio = option.querySelector('input[type="radio"]');
            if (radio) {
                radio.addEventListener('change', function () {
                    document.querySelectorAll('.scale-option').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    if (this.checked) {
                        option.classList.add('selected');
                    }
                });
            }
        });
    }

    // ============================================================
    // Опции (группы А/Б/В/Г)
    // ============================================================
    function initOptionGroups() {
        const optionItems = document.querySelectorAll('.option-item');

        optionItems.forEach(item => {
            item.addEventListener('click', function (e) {
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

            const radio = item.querySelector('input[type="radio"]');
            if (radio) {
                radio.addEventListener('change', function () {
                    // Внутри одной группы — убираем класс selected у соседей.
                    // Группа определяется по имени input: option_А / option_Б / ...
                    const groupName = this.name;
                    document
                        .querySelectorAll(`.option-item input[name="${groupName}"]`)
                        .forEach(otherRadio => {
                            otherRadio.closest('.option-item')?.classList.remove('selected');
                        });
                    if (this.checked) {
                        item.classList.add('selected');
                    }
                });

                // При загрузке страницы — восстановить подсветку
                if (radio.checked) {
                    item.classList.add('selected');
                }
            }
        });
    }

    // ============================================================
    // Валидация формы
    // ============================================================
    function initFormValidation() {
        const form = document.getElementById('surveyForm');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            // Обычная шкала 1–5
            const scoreRadios = document.querySelectorAll('input[name="score"]');
            if (scoreRadios.length > 0) {
                const selected = document.querySelector('input[name="score"]:checked');
                if (!selected) {
                    e.preventDefault();
                    showAlert('Пожалуйста, выберите вариант ответа', 'warning');
                    return;
                }
                return;
            }

            // Опрос с опциями (диагностический комплект):
            // каждая группа А/Б/В/Г должна иметь выбранный radio.
            const groupNames = new Set();
            document
                .querySelectorAll('.option-item input[type="radio"]')
                .forEach(r => groupNames.add(r.name));

            for (const name of groupNames) {
                const checked = document.querySelector(`input[name="${name}"]:checked`);
                if (!checked) {
                    e.preventDefault();
                    const letter = name.replace('option_', '');
                    showAlert(`Выберите вариант в группе «${letter}»`, 'warning');
                    return;
                }
            }
        });
    }

    // ============================================================
    // Автосохранение
    // ============================================================
    let autosaveTimeout = null;

    function initAutoSave() {
        const autosaveEnabled = document.body.dataset.autosave === 'true';
        if (!autosaveEnabled) return;

        const radios = document.querySelectorAll(
            'input[type="radio"][name="score"], ' +
            'input[type="radio"][name^="option_"]'
        );
        radios.forEach(radio => {
            radio.addEventListener('change', function () {
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
            if (!form) return;

            showSavingIndicator(true);

            const formData = new FormData(form);
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
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
        }, 1000);
    }

    // ============================================================
    // Индикаторы
    // ============================================================
    let savingIndicator = null;

    function showSavingIndicator(show) {
        if (!savingIndicator) {
            savingIndicator = document.createElement('div');
            savingIndicator.className =
                'position-fixed bottom-0 end-0 m-3 p-2 bg-info text-white rounded shadow';
            savingIndicator.style.zIndex = '9999';
            savingIndicator.style.fontSize = '0.875rem';
            savingIndicator.innerHTML =
                '<i class="fa-solid fa-spinner fa-spin me-1"></i> Сохранение...';
            document.body.appendChild(savingIndicator);
        }
        savingIndicator.style.display = show ? 'block' : 'none';
    }

    function showAutoSaveSuccess() {
        const successMsg = document.createElement('div');
        successMsg.className =
            'position-fixed bottom-0 end-0 m-3 p-2 bg-success text-white rounded shadow';
        successMsg.style.zIndex = '9999';
        successMsg.style.fontSize = '0.875rem';
        successMsg.innerHTML =
            '<i class="fa-solid fa-check-circle me-1"></i> Ответ сохранён';
        document.body.appendChild(successMsg);

        setTimeout(() => {
            successMsg.remove();
        }, 2000);
    }

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

    // ============================================================
    // Утилиты
    // ============================================================
    window.printResults = function () {
        window.print();
    };

    window.downloadResults = function (format = 'pdf') {
        alert(
            `Скачивание результатов в формате ${format.toUpperCase()} будет доступно в ближайшее время`
        );
    };
})();
