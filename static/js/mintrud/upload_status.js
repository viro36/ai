/**
 * Опрос статуса Celery-задачи по загрузке кадровой потребности.
 *
 * Ожидает на странице:
 *   - #task-status        (обёртка, изначально display: none)
 *   - #task-status-alert  (блок alert)
 *   - #task-status-text   (текст внутри)
 *   - #task-spinner       (спиннер)
 *
 * task_id берётся из flash-сообщения "ID задачи: <uuid>".
 */
(function () {
    'use strict';

    function extractTaskId() {
        const text = document.body.innerText || '';
        const match = text.match(/ID задачи:\s*([a-f0-9-]{36})/i);
        return match ? match[1] : null;
    }

    function formatSuccess(r) {
        const processed = (r && r.processed_sheets != null) ? r.processed_sheets : '?';
        const total = (r && r.total_rows != null) ? r.total_rows : '?';
        const skipped = (r && Array.isArray(r.skipped_sheets))
            ? r.skipped_sheets.length
            : 0;

        let html =
            'Файл успешно обработан!<br>' +
            'Листов: <b>' + processed + '</b>, ' +
            'записей: <b>' + total + '</b>';

        if (skipped) {
            html += ', пропущено листов: <b>' + skipped + '</b>';
        }
        return html + '.';
    }

    function setSuccess(elements, r) {
        elements.alert.className = 'alert alert-success d-flex align-items-center';
        elements.spinner.outerHTML =
            '<i class="fa-solid fa-circle-check me-3" style="font-size: 1.5rem;"></i>';
        elements.text.innerHTML = formatSuccess(r);
    }

    function setFailure(elements, data) {
        const err = (data && data.error) ? data.error : 'неизвестная ошибка';
        elements.alert.className = 'alert alert-danger d-flex align-items-center';
        elements.spinner.outerHTML =
            '<i class="fa-solid fa-circle-xmark me-3" style="font-size: 1.5rem;"></i>';
        elements.text.innerHTML =
            'Ошибка при обработке файла:<br><code>' + err + '</code>';
    }

    function setRunning(elements, state) {
        const labels = {
            PENDING: 'Задача в очереди…',
            STARTED: 'Обработка файла… (задача выполняется)',
            RETRY:   'Повторная попытка…'
        };
        elements.text.textContent = labels[state] || ('Обработка… (' + state + ')');
    }

    document.addEventListener('DOMContentLoaded', function () {
        const taskId = extractTaskId();
        if (!taskId) {
            return;
        }

        const elements = {
            block:   document.getElementById('task-status'),
            alert:   document.getElementById('task-status-alert'),
            text:    document.getElementById('task-status-text'),
            spinner: document.getElementById('task-spinner'),
        };
        if (!elements.block || !elements.alert || !elements.text || !elements.spinner) {
            console.warn('[mintrud] task-status elements not found on page');
            return;
        }

        elements.block.style.display = 'block';

        const INTERVAL_MS = 3000;
        const MAX_ATTEMPTS = 400;   // ~20 минут
        let attempts = 0;

        const url = '/mintrud/task/' + encodeURIComponent(taskId) + '/status/';

        const poll = setInterval(function () {
            attempts++;

            fetch(url, { credentials: 'same-origin' })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('HTTP ' + response.status);
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data.state === 'SUCCESS') {
                        clearInterval(poll);
                        setSuccess(elements, data.result || {});
                    } else if (data.state === 'FAILURE') {
                        clearInterval(poll);
                        setFailure(elements, data);
                    } else {
                        setRunning(elements, data.state);
                    }

                    if (attempts >= MAX_ATTEMPTS) {
                        clearInterval(poll);
                        elements.alert.className = 'alert alert-warning';
                        elements.text.textContent =
                            'Долго нет ответа. Проверьте Flower: http://localhost:5557';
                    }
                })
                .catch(function (err) {
                    // Сеть/сервер отвалились — попробуем на следующем тике.
                    console.warn('[mintrud] status poll failed:', err);
                });
        }, INTERVAL_MS);
    });
})();
