from django.urls import path
from . import views

app_name = "surveys"

urlpatterns = [
    path("", views.survey_list, name="survey_list"),
    path("start/<int:category_id>/", views.survey_start, name="survey_start"),
    path("continue/<int:category_id>/", views.survey_continue, name="survey_continue"),
    path(
        "question/<int:category_id>/<int:block_id>/<int:question_id>/",
        views.survey_question,
        name="survey_question",
    ),
    path("results/<int:category_id>/", views.survey_results, name="survey_results"),
    path(
        "results/<int:category_id>/attempt/<int:attempt>/",
        views.survey_results,
        name="survey_results_attempt",
    ),
    path(
        "history/<int:category_id>/",
        views.survey_results_history,
        name="survey_history",
    ),
]
