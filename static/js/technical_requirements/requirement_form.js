document.addEventListener('DOMContentLoaded', function() {
    // ========== Подсчет выбранных ВУЗов ==========
    const universityCheckboxes = document.querySelectorAll('input[name="universities"]');
    const selectedCountSpan = document.getElementById('selectedCount');
    const validationMessage = document.getElementById('validationMessage');

    function updateUniversityCount() {
        const checked = document.querySelectorAll('input[name="universities"]:checked');
        const count = checked.length;
        selectedCountSpan.textContent = count;

        if (count < 5) {
            validationMessage.style.display = 'inline';
        } else {
            validationMessage.style.display = 'none';
        }
    }

    if (universityCheckboxes.length > 0) {
        universityCheckboxes.forEach(cb => {
            cb.addEventListener('change', updateUniversityCount);
        });
        updateUniversityCount();
    }

    // ========== Показ/скрытие поля "Свой вариант" ==========
    function toggleOtherInput(select) {
        const questionId = select.dataset.questionId;
        const otherGroup = document.querySelector(`.other-input-group[data-for-question="${questionId}"]`);
        const otherInput = document.getElementById(`other_${questionId}`);

        if (!otherGroup || !otherInput) return;

        if (select.value === 'Свой вариант') {
            otherGroup.style.display = 'block';
            otherInput.required = true;
            otherInput.disabled = false;
        } else {
            otherGroup.style.display = 'none';
            otherInput.required = false;
            otherInput.disabled = true;
            otherInput.value = '';
        }
    }

    document.querySelectorAll('select[data-show-other="true"]').forEach(select => {
        select.addEventListener('change', function() {
            toggleOtherInput(this);
        });
        setTimeout(function() {
            toggleOtherInput(select);
        }, 100);
    });

    // ========== Обновление подписи для переключателей (boolean) ==========
    function updateSwitchLabel(cb) {
        const label = document.getElementById(`label_${cb.id}`);
        if (label) {
            label.textContent = cb.checked ? 'Да' : 'Нет';
            label.className = `badge bg-${cb.checked ? 'success' : 'secondary'}`;
        }
    }

    document.querySelectorAll('.form-switch input[type="checkbox"]').forEach(cb => {
        updateSwitchLabel(cb);

        cb.addEventListener('change', function() {
            updateSwitchLabel(this);
            // Триггерим обновление условных полей
            setTimeout(function() {
                toggleConditionalFields();
            }, 50);
        });
    });

    // ========== Условное отображение полей ==========
    function toggleConditionalFields() {
        document.querySelectorAll('.form-group[data-depends-on]').forEach(group => {
            const dependsOnId = group.dataset.dependsOn;
            const dependsValue = group.dataset.dependsValue;

            if (!dependsOnId) return;

            const questionId = dependsOnId.replace('q_', '');

            // Ищем поле по question-id (без префикса)
            const triggerField = document.querySelector(`.form-group[data-question-id="${questionId}"]`);
            if (!triggerField) return;

            // Ищем checkbox внутри triggerField
            const triggerInput = triggerField.querySelector('input[type="checkbox"]');
            if (!triggerInput) return;

            let shouldShow = false;

            const dependsValueLower = (dependsValue || '').toLowerCase();
            const isChecked = triggerInput.checked;

            if (dependsValueLower === 'true' || dependsValueLower === 'on' || dependsValueLower === '1') {
                shouldShow = isChecked === true;
            } else if (dependsValueLower === 'false' || dependsValueLower === 'off' || dependsValueLower === '0') {
                shouldShow = isChecked === false;
            } else {
                shouldShow = isChecked;
            }

            if (shouldShow) {
                group.style.display = 'block';
                setTimeout(function() {
                    group.classList.add('show');
                }, 10);
            } else {
                group.style.display = 'none';
                group.classList.remove('show');
            }

            group.querySelectorAll('input, select, textarea').forEach(function(el) {
                if (shouldShow) {
                    el.removeAttribute('disabled');
                    if (el.hasAttribute('data-required')) {
                        el.required = true;
                    }
                } else {
                    el.setAttribute('disabled', 'disabled');
                    el.required = false;
                }
            });
        });
    }

    // Навешиваем обработчики на все поля
    document.querySelectorAll('.form-group[data-question-id]').forEach(function(group) {
        const inputs = group.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('change', function() {
                setTimeout(function() {
                    toggleConditionalFields();
                }, 50);
            });
        });
    });

    // Запускаем при загрузке
    setTimeout(function() {
        toggleConditionalFields();
    }, 200);

    // ========== Валидация формы ==========
    const form = document.getElementById('requirementForm');

    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            document.querySelectorAll('.form-group[style*="display: block"], .form-group:not([style*="display: none"])').forEach(function(group) {
                if (group.dataset.dependsOn && group.style.display === 'none') return;

                const requiredInputs = group.querySelectorAll('[required]');
                requiredInputs.forEach(function(input) {
                    if (input.disabled) return;

                    if (!input.value || input.value.trim() === '') {
                        input.classList.add('is-invalid');
                        isValid = false;
                        const label = group.querySelector('label')?.textContent?.trim() || 'Вопрос';
                        errors.push('Поле "' + label + '" обязательно для заполнения');
                    } else {
                        input.classList.remove('is-invalid');
                    }
                });
            });

            document.querySelectorAll('.other-input-group[style*="display: block"] input').forEach(function(input) {
                if (!input.value || input.value.trim() === '') {
                    input.classList.add('is-invalid');
                    isValid = false;
                    errors.push('Пожалуйста, укажите свой вариант');
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            const selectedUniversities = document.querySelectorAll('input[name="universities"]:checked');
            if (selectedUniversities.length < 5) {
                isValid = false;
                errors.push('Выберите не менее 5 ВУЗов');
            }

            if (!isValid) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля:\n\n' + errors.join('\n'));
            }
        });
    }

    document.querySelectorAll('.is-invalid').forEach(function(el) {
        el.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
        el.addEventListener('change', function() {
            this.classList.remove('is-invalid');
        });
    });

    console.log('Technical Requirements form initialized');
});
