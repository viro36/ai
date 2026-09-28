class ViewerRestrictedMixin:
    """
    Запрещает добавление, изменение, удаление и любые actions
    для пользователей из группы «Просмотрщик».

    Просмотр (list, detail) остаётся доступным.
    """

    def _is_viewer(self, request):
        return request.user.groups.filter(name="Просмотрщик").exists()

    def has_add_permission(self, request):
        if self._is_viewer(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        if self._is_viewer(request):
            return {}
        return super().get_actions(request)
