from django.views.generic import TemplateView
from apps.recommendations.utils import is_ready_for_recommendations


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated and user.user_type == "employee":
            context["ready_for_recommendations"] = is_ready_for_recommendations(user)
        else:
            context["ready_for_recommendations"] = False

        return context
