function saveSelectedOrganization() {
    const orgSelect = document.getElementById('modal-organization-select');
    const selectedOption = orgSelect?.options[orgSelect.selectedIndex];

    if (!selectedOption || !selectedOption.value) return;

    const orgId = selectedOption.value;
    const orgName = selectedOption.textContent;
    const orgInn = selectedOption.getAttribute('data-inn') || '';

    // Обновляем скрытые поля в основной форме
    const orgIdInput = document.getElementById('organization-id');
    const orgNameSpan = document.getElementById('organization-name');
    const orgInnSpan = document.getElementById('organization-inn');

    if (orgIdInput) orgIdInput.value = orgId;
    if (orgNameSpan) orgNameSpan.textContent = orgName;
    if (orgInnSpan) orgInnSpan.textContent = orgInn;

    // Закрываем модалку
    const modal = bootstrap.Modal.getInstance(document.getElementById('orgModal'));
    if (modal) modal.hide();
}
