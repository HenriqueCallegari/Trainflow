"""URLs do módulo de treino."""
from django.urls import path

from . import views

app_name = "training"

urlpatterns = [
    # Planos
    path("planos/", views.TrainingPlanListView.as_view(), name="plan_list"),
    path("planos/novo/", views.TrainingPlanCreateView.as_view(), name="plan_create"),
    path("planos/<int:pk>/", views.TrainingPlanDetailView.as_view(), name="plan_detail"),
    path("planos/<int:pk>/editar/", views.TrainingPlanUpdateView.as_view(), name="plan_update"),
    path("planos/<int:pk>/excluir/", views.TrainingPlanDeleteView.as_view(), name="plan_delete"),

    # Semanas inline
    path("planos/<int:pk>/semanas/adicionar/", views.plan_add_week, name="plan_add_week"),
    path("planos/<int:pk>/semanas/<int:week_number>/remover/",
         views.plan_remove_week, name="plan_remove_week"),

    # Sessões
    path("sessoes/<int:pk>/", views.TrainingSessionDetailView.as_view(), name="session_detail"),
    path("sessoes/<int:pk>/editar/", views.TrainingSessionUpdateView.as_view(), name="session_update"),
    path("sessoes/<int:pk>/concluir/", views.session_toggle_complete, name="session_toggle"),
    path("sessoes/<int:pk>/excluir/", views.session_delete_inline, name="session_delete"),
    path("planos/<int:plan_pk>/semanas/<int:week_number>/sessoes/adicionar/",
         views.session_add, name="session_add"),

    # Exercícios
    path("sessoes/<int:pk>/adicionar-exercicio/",
         views.session_add_exercise, name="session_add_exercise"),
    path("sessoes/<int:pk>/criar-exercicio/",
         views.session_create_exercise_inline, name="session_create_exercise"),
    path("exercicio-sessao/<int:pk>/editar/",
         views.SessionExerciseUpdateView.as_view(), name="session_exercise_update"),
    path("exercicio-sessao/<int:pk>/excluir/",
         views.session_exercise_delete, name="session_exercise_delete"),

    # Feedback
    path("sessoes/<int:pk>/feedback/",
         views.session_submit_feedback, name="session_feedback_submit"),
    path("feedback/<int:pk>/responder/",
         views.session_feedback_respond, name="session_feedback_respond"),

    # Mover exercício na ordem (↑ / ↓)
    path("exercicio-sessao/<int:pk>/mover/<str:direction>/",
         views.session_exercise_move, name="session_exercise_move"),

    # Reps pré-salvas
    path("reps/", views.RepSchemeListView.as_view(), name="repscheme_list"),
    path("reps/novo/", views.RepSchemeCreateView.as_view(), name="repscheme_create"),
    path("reps/<int:pk>/editar/", views.RepSchemeUpdateView.as_view(), name="repscheme_update"),
    path("reps/<int:pk>/excluir/", views.RepSchemeDeleteView.as_view(), name="repscheme_delete"),

    # Biblioteca
    path("exercicios/", views.ExerciseLibraryListView.as_view(), name="exercise_list"),
    path("exercicios/novo/", views.ExerciseLibraryCreateView.as_view(), name="exercise_create"),
    path("exercicios/<int:pk>/editar/", views.ExerciseLibraryUpdateView.as_view(), name="exercise_update"),
    path("exercicios/<int:pk>/excluir/", views.ExerciseLibraryDeleteView.as_view(), name="exercise_delete"),

    # Templates
    path("templates/", views.AccessoryTemplateListView.as_view(), name="template_list"),
    path("templates/novo/", views.AccessoryTemplateCreateView.as_view(), name="template_create"),
    path("templates/<int:pk>/editar/", views.AccessoryTemplateUpdateView.as_view(), name="template_update"),
    path("templates/<int:pk>/excluir/", views.AccessoryTemplateDeleteView.as_view(), name="template_delete"),

    # Anamnese
    path("anamnese/", views.AthleteAnamnesisListView.as_view(), name="anamnesis_list"),
    path("anamnese/nova/", views.AthleteAnamnesisCreateView.as_view(), name="anamnesis_create"),
    path("anamnese/<int:pk>/editar/", views.AthleteAnamnesisUpdateView.as_view(), name="anamnesis_update"),

    # PRs
    path("prs/", views.PersonalRecordListView.as_view(), name="pr_list"),
    path("prs/novo/", views.PersonalRecordCreateView.as_view(), name="pr_create"),
    path("prs/<int:pk>/editar/", views.PersonalRecordUpdateView.as_view(), name="pr_update"),
    path("prs/<int:pk>/excluir/", views.PersonalRecordDeleteView.as_view(), name="pr_delete"),
]
