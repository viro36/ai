from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.surveys.services.survey_handlers import SurveyHandlerFactory
from .models import (
    SurveyCategory,
    SurveyBlock,
    SurveyQuestion,
    SurveyQuestionOption,
    UserSurveyResponse,
    SurveySession,
    ScaleLabel,
)

# ============================================================
# СПИСОК ОПРОСОВ
# ============================================================


@login_required
def survey_list(request):
    """Список доступных опросов (с учётом аудитории)."""
    all_categories = SurveyCategory.objects.filter(is_active=True).prefetch_related(
        "target_positions"
    )

    categories = [c for c in all_categories if c.is_available_for(request.user)]

    for category in categories:
        category.completed_sessions = SurveySession.objects.filter(
            user=request.user, category=category, status="completed"
        ).order_by("-attempt")

        category.has_completed = category.completed_sessions.exists()
        category.has_in_progress = SurveySession.objects.filter(
            user=request.user, category=category, status="in_progress"
        ).exists()
        category.attempts_count = category.completed_sessions.count()

    context = {"categories": categories}
    return render(request, "surveys/survey_list.html", context)


# ============================================================
# СТАРТ / ПРОДОЛЖЕНИЕ
# ============================================================


@login_required
def survey_continue(request, category_id):
    """Продолжить незавершённый опрос."""
    category = get_object_or_404(SurveyCategory, id=category_id, is_active=True)

    if not category.is_available_for(request.user):
        messages.error(request, "Этот опрос вам недоступен")
        return redirect("surveys:survey_list")

    session = SurveySession.objects.filter(
        user=request.user, category=category, status="in_progress"
    ).first()

    if not session:
        messages.warning(request, "Нет незавершённого опроса. Начните новый.")
        return redirect("surveys:survey_start", category_id=category_id)

    # Если есть текущий вопрос - продолжаем с него
    if session.current_question:
        return redirect(
            "surveys:survey_question",
            category_id=category_id,
            block_id=session.current_block.id,
            question_id=session.current_question.id,
        )

    # Ищем первый неотвеченный вопрос
    all_questions = []
    for block in category.blocks.filter(is_active=True).order_by("order"):
        for question in block.questions.filter(is_active=True).order_by("q_number"):
            all_questions.append({"block": block, "question": question})

    for item in all_questions:
        answered = UserSurveyResponse.objects.filter(
            user=request.user,
            question=item["question"],
            session=session,
        ).exists()
        if not answered:
            session.current_block = item["block"]
            session.current_question = item["question"]
            session.save()
            return redirect(
                "surveys:survey_question",
                category_id=category_id,
                block_id=item["block"].id,
                question_id=item["question"].id,
            )

    session.status = "completed"
    session.completed_at = timezone.now()
    session.save()
    messages.success(request, "Опрос уже завершён!")
    return redirect("surveys:survey_results", category_id=category_id)


@login_required
def survey_start(request, category_id):
    """Начало нового опроса."""
    category = get_object_or_404(SurveyCategory, id=category_id)

    # Проверка активности опроса
    if not category.is_active:
        messages.error(request, "Этот опрос в данный момент недоступен")
        return redirect("surveys:survey_list")

    if not category.is_available_for(request.user):
        messages.error(request, "Этот опрос вам недоступен")
        return redirect("surveys:survey_list")

    in_progress_session = SurveySession.objects.filter(
        user=request.user, category=category, status="in_progress"
    ).first()

    # Если есть незавершённая сессия - продолжаем её
    if in_progress_session:
        messages.info(request, "Продолжаем опрос с того места, где вы остановились")
        return redirect("surveys:survey_continue", category_id=category_id)

    # Определяем номер следующей попытки
    last_session = (
        SurveySession.objects.filter(
            user=request.user, category=category, status="completed"
        )
        .order_by("-attempt")
        .first()
    )

    next_attempt = (last_session.attempt + 1) if last_session else 1

    # Получаем первый блок и первый вопрос
    first_block = category.blocks.filter(is_active=True).order_by("order").first()
    first_question = None
    if first_block:
        first_question = (
            first_block.questions.filter(is_active=True).order_by("q_number").first()
        )

    # Создаём новую сессию
    session = SurveySession.objects.create(
        user=request.user,
        category=category,
        status="in_progress",
        attempt=next_attempt,
        current_block=first_block,
        current_question=first_question,
    )

    if session.current_question:
        return redirect(
            "surveys:survey_question",
            category_id=category_id,
            block_id=session.current_block.id,
            question_id=session.current_question.id,
        )

    messages.error(request, "В опросе нет вопросов")
    return redirect("surveys:survey_list")


# ============================================================
# ВОПРОС
# ============================================================


@login_required
def survey_question(request, category_id, block_id, question_id):
    """Отображение вопроса опроса."""
    category = get_object_or_404(SurveyCategory, id=category_id, is_active=True)

    if not category.is_available_for(request.user):
        messages.error(request, "Этот опрос вам недоступен")
        return redirect("surveys:survey_list")

    block = get_object_or_404(
        SurveyBlock, id=block_id, category=category, is_active=True
    )
    question = get_object_or_404(
        SurveyQuestion, id=question_id, block=block, is_active=True
    )

    # Получаем сессию
    session = SurveySession.objects.filter(
        user=request.user, category=category, status="in_progress"
    ).first()

    if not session:
        return redirect("surveys:survey_start", category_id=category_id)

    # Шкала оценок (для обычных опросов)
    scale_labels = ScaleLabel.objects.filter(category=category).order_by("scale_value")
    if not scale_labels.exists():
        scale_labels = ScaleLabel.objects.filter(category__isnull=True).order_by(
            "scale_value"
        )

    # Есть ли у вопроса опции (диагностический комплект)
    question_groups = sorted(
        set(question.options.values_list("group", flat=True)) - {None, ""}
    )
    has_options = bool(question_groups)

    # Сохранённые ответы пользователя по текущей сессии
    saved_responses = UserSurveyResponse.objects.filter(
        user=request.user, question=question, session=session
    )
    saved_response = saved_responses.filter(group__isnull=True).first()
    selected_options = {
        r.group: r.selected_option_id
        for r in saved_responses.exclude(group__isnull=True)
        if r.group
    }

    # Навигация: все блоки и вопросы
    blocks = list(category.blocks.filter(is_active=True).order_by("order"))
    all_questions = []
    for b in blocks:
        for q in b.questions.filter(is_active=True).order_by("q_number"):
            all_questions.append({"block": b, "question": q})

    current_index = next(
        (
            i
            for i, item in enumerate(all_questions)
            if item["question"].id == question.id
        ),
        0,
    )

    prev_item = all_questions[current_index - 1] if current_index > 0 else None
    next_item = (
        all_questions[current_index + 1]
        if current_index + 1 < len(all_questions)
        else None
    )
    is_last = next_item is None

    # ============================================================
    # POST
    # ============================================================
    if request.method == "POST":
        if has_options:
            # ===== Опрос с опциями (диагностический комплект) =====
            answers = {}
            missing = []

            for letter in question_groups:
                option_id = request.POST.get(f"option_{letter}")
                if option_id:
                    answers[letter] = int(option_id)
                else:
                    missing.append(letter)

            if missing:
                messages.error(
                    request,
                    f"Выберите вариант в группе: {', '.join(missing)}",
                )
            else:
                for letter, option_id in answers.items():
                    UserSurveyResponse.objects.update_or_create(
                        user=request.user,
                        question=question,
                        session=session,
                        group=letter,
                        defaults={
                            "selected_option_id": option_id,
                            "score": 1,  # фиктивное значение, чтобы не нарушать NOT NULL
                        },
                    )

                if next_item:
                    session.current_block = next_item["block"]
                    session.current_question = next_item["question"]
                    session.save()
                    return redirect(
                        "surveys:survey_question",
                        category_id=category_id,
                        block_id=next_item["block"].id,
                        question_id=next_item["question"].id,
                    )

                # Последний вопрос — завершаем
                session.current_block = block
                session.current_question = question
                session.save()

                session.status = "completed"
                session.completed_at = timezone.now()
                session.save()

                handler = SurveyHandlerFactory.get_handler(category, session)
                responses = UserSurveyResponse.objects.filter(
                    user=request.user,
                    question__block__category=category,
                    session=session,
                )
                if handler.survey_config["type"] != "custom":
                    handler.calculate_results(responses)
                messages.success(request, "Спасибо за прохождение опроса!")
                return redirect("surveys:survey_results", category_id=category_id)

        else:
            # ===== Обычный опрос со шкалой 1–5 =====
            score = request.POST.get("score")

            if not score:
                messages.error(request, "Пожалуйста, выберите вариант ответа")
            else:
                UserSurveyResponse.objects.update_or_create(
                    user=request.user,
                    question=question,
                    session=session,
                    group=None,  # важно: явный None, чтобы не было дублей
                    defaults={"score": int(score)},
                )

                if next_item:
                    session.current_block = next_item["block"]
                    session.current_question = next_item["question"]
                    session.save()
                    return redirect(
                        "surveys:survey_question",
                        category_id=category_id,
                        block_id=next_item["block"].id,
                        question_id=next_item["question"].id,
                    )

                # Последний вопрос — завершаем
                session.current_block = block
                session.current_question = question
                session.save()

                session.status = "completed"
                session.completed_at = timezone.now()
                session.save()

                handler = SurveyHandlerFactory.get_handler(category, session)
                responses = UserSurveyResponse.objects.filter(
                    user=request.user,
                    question__block__category=category,
                    session=session,
                )
                if handler.survey_config["type"] != "custom":
                    handler.calculate_results(responses)
                messages.success(request, "Спасибо за прохождение опроса!")
                return redirect("surveys:survey_results", category_id=category_id)

    # ============================================================
    # Контекст для рендера
    # ============================================================
    total = len(all_questions)
    answered = (
        UserSurveyResponse.objects.filter(
            user=request.user,
            question__block__category=category,
            session=session,
        )
        .values("question")
        .distinct()
        .count()
    )
    progress = round(answered / total * 100) if total > 0 else 0
    progress = min(progress, 100)

    block_questions = list(block.questions.filter(is_active=True).order_by("q_number"))
    question_in_block = (
        next((i for i, q in enumerate(block_questions) if q.id == question.id), 0) + 1
    )

    context = {
        "category": category,
        "survey_block": block,
        "question": question,
        "scale_labels": scale_labels,
        "prev_question": prev_item["question"] if prev_item else None,
        "next_question": next_item["question"] if next_item else None,
        "prev_block": prev_item["block"] if prev_item else None,
        "next_block": next_item["block"] if next_item else None,
        "is_last": is_last,
        "progress": progress,
        "question_number": current_index + 1,
        "total_questions": total,
        "question_in_block": question_in_block,
        "total_in_block": len(block_questions),
        # для обычной шкалы 1–5
        "selected_score": saved_response.score if saved_response else None,
        # для опросов с опциями
        "has_options": has_options,
        "question_groups": question_groups,
        "selected_options": selected_options,
        "blocks": blocks,
    }
    return render(request, "surveys/survey_question.html", context)


# ============================================================
# РЕЗУЛЬТАТЫ
# ============================================================


@login_required
def survey_results(request, category_id, attempt=None):
    """Результаты опроса (по умолчанию последняя попытка)."""
    category = get_object_or_404(SurveyCategory, id=category_id)

    if not category.is_available_for(request.user):
        messages.error(request, "Этот опрос вам недоступен")
        return redirect("surveys:survey_list")

    # ---------- Определяем сессию ----------
    if attempt:
        session = get_object_or_404(
            SurveySession,
            user=request.user,
            category=category,
            attempt=attempt,
            status="completed",
        )
    else:
        session = (
            SurveySession.objects.filter(
                user=request.user, category=category, status="completed"
            )
            .order_by("-attempt")
            .first()
        )

    if not session:
        in_progress = SurveySession.objects.filter(
            user=request.user, category=category, status="in_progress"
        ).first()
        if in_progress:
            return redirect("surveys:survey_continue", category_id=category_id)
        messages.warning(request, "Вы ещё не прошли этот опрос")
        return redirect("surveys:survey_list")

    # ---------- Получаем обработчик ----------
    handler = SurveyHandlerFactory.get_handler(category, session)

    # ---------- Пытаемся получить готовый результат, иначе считаем ----------
    results = None
    if hasattr(handler, "get_results"):
        results = handler.get_results()

    if results is None and hasattr(handler, "calculate_results"):
        user_responses_qs = UserSurveyResponse.objects.filter(
            user=request.user,
            question__block__category=category,
            session=session,
        )
        results = handler.calculate_results(user_responses_qs)

    # ---------- Контекст от обработчика ----------
    handler_context = {}
    if hasattr(handler, "get_results_context"):
        handler_context = handler.get_results_context(results) or {}

    # ---------- Группировка ответов по блокам ----------
    blocks = category.blocks.filter(is_active=True).order_by("order")
    block_responses = []
    all_scores = []

    for block in blocks:
        questions = block.questions.filter(is_active=True).order_by("q_number")
        responses = []

        for question in questions:
            user_responses = list(
                UserSurveyResponse.objects.filter(
                    user=request.user,
                    question=question,
                    session=session,
                ).order_by("group")
            )
            if not user_responses:
                continue

            # Детали выбранных вариантов (для опросов с опциями)
            details = []
            for r in user_responses:
                option_text = ""
                is_correct = None
                if r.selected_option_id:
                    try:
                        option = SurveyQuestionOption.objects.get(
                            id=r.selected_option_id
                        )
                        option_text = option.text
                        is_correct = option.is_correct
                    except SurveyQuestionOption.DoesNotExist:
                        pass

                details.append(
                    {
                        "group": r.group,
                        "option_text": option_text,
                        "is_correct": is_correct,
                        "score": r.score,
                    }
                )

            # Основной балл для агрегатов:
            # для опросов с опциями — score первой записи,
            # для шкалы 1–5 — score единственной записи.
            main_score = user_responses[0].score or 0

            responses.append(
                {
                    "question": question,
                    "score": main_score,
                    "details": details,
                }
            )
            all_scores.append(main_score)

        if responses:
            block_responses.append(
                {
                    "block": block,
                    "responses": responses,
                    "avg_score": (
                        sum(r["score"] for r in responses) / len(responses)
                        if responses
                        else 0
                    ),
                }
            )

    # ---------- Средний балл и распределение ----------
    average_score = sum(all_scores) / len(all_scores) if all_scores else 0

    distribution = {i: 0 for i in range(1, 6)}
    for score in all_scores:
        if score in distribution:
            distribution[score] += 1

    scale_labels = ScaleLabel.objects.filter(category=category).order_by("scale_value")
    if not scale_labels.exists():
        scale_labels = ScaleLabel.objects.filter(category__isnull=True).order_by(
            "scale_value"
        )
    scale_labels_dict = {sl.scale_value: sl.label for sl in scale_labels}

    # ---------- Общее число попыток ----------
    total_attempts = SurveySession.objects.filter(
        user=request.user, category=category, status="completed"
    ).count()

    # ---------- Контекст ----------
    context = {
        "category": category,
        "session": session,
        "current_attempt": session.attempt,
        "total_attempts": total_attempts,
        "sessions_list": list(range(1, total_attempts + 1)),
        "block_responses": block_responses,
        "average_score": round(average_score, 2),
        "distribution": distribution,
        "scale_labels": scale_labels_dict,
        "completed_at": session.completed_at,
        "total_responses": len(all_scores),
        **handler_context,
    }

    template = handler.get_results_template()
    return render(request, template, context)


@login_required
def survey_results_history(request, category_id):
    """Список всех попыток опроса."""
    category = get_object_or_404(SurveyCategory, id=category_id)

    if not category.is_available_for(request.user):
        messages.error(request, "Этот опрос вам недоступен")
        return redirect("surveys:survey_list")

    sessions = SurveySession.objects.filter(
        user=request.user, category=category, status="completed"
    ).order_by("-attempt")

    context = {"category": category, "sessions": sessions}
    return render(request, "surveys/survey_history.html", context)
