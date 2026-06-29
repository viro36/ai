from django.views.generic import TemplateView
from apps.recommendations.utils import (
    is_ready_for_recommendations,
    has_completed_profile,
    has_completed_all_surveys,
)


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated and user.user_type == "employee":
            context["ready_for_recommendations"] = is_ready_for_recommendations(user)
            context["profile_completed"] = has_completed_profile(user)

            surveys_info = has_completed_all_surveys(user)
            context["surveys_completed"] = surveys_info["completed"]
            context["surveys_total"] = surveys_info["total"]
            context["all_surveys_completed"] = surveys_info["all_completed"]
            context["has_surveys"] = surveys_info["total"] > 0
        else:
            context["ready_for_recommendations"] = False
            context["profile_completed"] = False
            context["surveys_completed"] = 0
            context["surveys_total"] = 0
            context["all_surveys_completed"] = False
            context["has_surveys"] = False

        return context
