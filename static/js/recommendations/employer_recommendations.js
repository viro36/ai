document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('categorySelect');
    const courseSelect = document.getElementById('courseSelect');
    const positionSelect = document.getElementById('positionSelect');
    const employeeSelect = document.getElementById('employeeSelect');
    const submitBtn = document.getElementById('submitBtn');
    const recommendationForm = document.getElementById('recommendationForm');

    // Загрузка курсов по категории
    categorySelect.addEventListener('change', function() {
        const categoryId = this.value;
        if (categoryId) {
            courseSelect.disabled = true;
            courseSelect.innerHTML = '<option value="">Загрузка...</option>';

            fetch(`/recommendations/employer/get-courses/?category_id=${categoryId}`)
                .then(response => response.json())
                .then(data => {
                    courseSelect.innerHTML = '<option value="">Выберите курс...</option>';
                    data.courses.forEach(course => {
                        const option = document.createElement('option');
                        option.value = course.id;
                        option.textContent = `${course.title} (${course.organization__short_name})`;
                        courseSelect.appendChild(option);
                    });
                    courseSelect.disabled = false;
                    checkFormValidity();
                })
                .catch(error => {
                    console.error('Ошибка загрузки курсов:', error);
                    courseSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                });
        } else {
            courseSelect.innerHTML = '<option value="">Сначала выберите категорию...</option>';
            courseSelect.disabled = true;
            checkFormValidity();
        }
    });

    // Загрузка сотрудников по должности
    positionSelect.addEventListener('change', function() {
        const position = this.value;
        if (position) {
            employeeSelect.disabled = true;
            employeeSelect.innerHTML = '<option value="">Загрузка...</option>';

            fetch(`/recommendations/employer/get-employees/?position=${encodeURIComponent(position)}`)
                .then(response => response.json())
                .then(data => {
                    employeeSelect.innerHTML = '<option value="">Выберите сотрудника...</option>';
                    data.employees.forEach(employee => {
                        const option = document.createElement('option');
                        option.value = employee.id;
                        const fullName = `${employee.last_name} ${employee.first_name} ${employee.patronymic || ''}`.trim();
                        option.textContent = fullName || employee.username;
                        employeeSelect.appendChild(option);
                    });
                    employeeSelect.disabled = false;
                    checkFormValidity();
                })
                .catch(error => {
                    console.error('Ошибка загрузки сотрудников:', error);
                    employeeSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                });
        } else {
            employeeSelect.innerHTML = '<option value="">Сначала выберите должность...</option>';
            employeeSelect.disabled = true;
            checkFormValidity();
        }
    });

    // Проверка валидности формы
    function checkFormValidity() {
        const isCategorySelected = categorySelect.value !== '';
        const isCourseSelected = courseSelect.value !== '';
        const isPositionSelected = positionSelect.value !== '';
        const isEmployeeSelected = employeeSelect.value !== '';

        submitBtn.disabled = !(isCategorySelected && isCourseSelected && isPositionSelected && isEmployeeSelected);
    }

    courseSelect.addEventListener('change', checkFormValidity);
    employeeSelect.addEventListener('change', checkFormValidity);

    // Валидация перед отправкой
    recommendationForm.addEventListener('submit', function(e) {
        if (!courseSelect.value || !employeeSelect.value) {
            e.preventDefault();
            alert('Пожалуйста, выберите курс и сотрудника');
        }
    });
});
