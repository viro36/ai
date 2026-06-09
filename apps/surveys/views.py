from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.surveys.services.survey_handlers import SurveyHandlerFactory
from .models import (
    SurveyCategory,
    SurveyBlock,
    SurveyQuestion,
    UserSurveyResponse,
    SurveySession,
    ScaleLabel,
)


@login_required
def survey_list(request):
    """Список доступных опросов"""
    categories = SurveyCategory.objects.filter(is_active=True)

    for category in categories:
        category.completed_sessions = SurveySession.objects.filter(
            user=request.user, category=category, status="completed"
        ).order_by("-attempt")

        category.has_completed = category.completed_sessions.exists()
        category.has_in_progress = SurveySession.objects.filter(
            user=request.user, category=category, status="in_progress"
        ).exists()
        category.attempts_count = category.completed_sessions.count()

    context = {
        "categories": categories,
    }
    return render(request, "surveys/survey_list.html", context)


@login_required
def survey_continue(request, category_id):
    """Продолжить незавершённый опрос"""
    category = get_object_or_404(SurveyCategory, id=category_id, is_active=True)

    # Находим незавершённую сессию
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

    # Если нет текущего вопроса - находим первый неотвеченный
    # Получаем все вопросы
    all_questions = []
    for block in category.blocks.filter(is_active=True).order_by("order"):
        for question in block.questions.filter(is_active=True).order_by("q_number"):
            all_questions.append({"block": block, "question": question})

    # Находим первый неотвеченный вопрос
    for item in all_questions:
        answered = UserSurveyResponse.objects.filter(
            user=request.user, question=item["question"]
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

    # Если все вопросы отвечены - завершаем опрос
    session.status = "completed"
    session.completed_at = timezone.now()
    session.save()
    messages.success(request, "Опрос уже завершён!")
    return redirect("surveys:survey_results", category_id=category_id)


@login_required
def survey_start(request, category_id):
    """Начало нового опроса"""
    category = get_object_or_404(SurveyCategory, id=category_id)

    # Проверка активности опроса
    if not category.is_active:
        messages.error(request, "Этот опрос в данный момент недоступен")
        return redirect("surveys:survey_list")

    # Проверяем, есть ли незавершённая сессия
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
    else:
        messages.error(request, "В опросе нет вопросов")
        return redirect("surveys:survey_list")


@login_required
def survey_question(request, category_id, block_id, question_id):
    """Отображение вопроса опроса"""
    category = get_object_or_404(SurveyCategory, id=category_id, is_active=True)
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

    # Получаем шкалу оценок
    scale_labels = ScaleLabel.objects.filter(category=category).order_by("scale_value")

    # Если для опроса нет своей шкалы, используем глобальную (без category)
    if not scale_labels.exists():
        scale_labels = ScaleLabel.objects.filter(category__isnull=True).order_by(
            "scale_value"
        )

    # Получаем сохранённый ответ пользователя для текущей сессии
    saved_response = UserSurveyResponse.objects.filter(
        user=request.user, question=question, session=session
    ).first()

    # Получаем все блоки и вопросы для навигации
    blocks = list(category.blocks.filter(is_active=True).order_by("order"))
    all_questions = []
    for b in blocks:
        for q in b.questions.filter(is_active=True).order_by("q_number"):
            all_questions.append({"block": b, "question": q})

    # Находим текущую позицию
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

    if request.method == "POST":
        score = request.POST.get("score")

        if not score:
            messages.error(request, "Пожалуйста, выберите вариант ответа")
        else:
            # Сохраняем ответ с привязкой к сессии
            UserSurveyResponse.objects.update_or_create(
                user=request.user,
                question=question,
                session=session,
                defaults={"score": int(score)},
            )

            # Обновляем текущий вопрос в сессии
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
            else:
                # Это последний вопрос
                # Обновляем текущий вопрос на последний перед завершением
                session.current_block = block
                session.current_question = question
                session.save()

                # Завершаем опрос
                session.status = "completed"
                session.completed_at = timezone.now()
                session.save()

                # Получаем обработчик и рассчитываем результаты
                handler = SurveyHandlerFactory.get_handler(category, session)
                user_responses = UserSurveyResponse.objects.filter(
                    user=request.user,
                    question__block__category=category,
                    session=session,
                )

                # Проверяем, нужно ли рассчитывать результаты (не для custom опросов)
                if handler.survey_config["type"] != "custom":
                    handler.calculate_results(user_responses)
                    messages.success(request, "Спасибо за прохождение опроса!")
                else:
                    messages.success(request, "Спасибо за прохождение опроса!")

                # Принудительно перенаправляем на результаты
                return redirect("surveys:survey_results", category_id=category_id)

    # Прогресс
    total = len(all_questions)
    answered = UserSurveyResponse.objects.filter(
        user=request.user, question__block__category=category, session=session
    ).count()

    # Ограничиваем прогресс 100%
    progress = round(answered / total * 100) if total > 0 else 0
    progress = min(progress, 100)

    # Номер вопроса в блоке
    block_questions = list(block.questions.filter(is_active=True).order_by("q_number"))
    question_in_block = (
        next((i for i, q in enumerate(block_questions) if q.id == question.id), 0) + 1
    )

    # Для уже отвеченного вопроса показываем сохранённую оценку
    selected_score = saved_response.score if saved_response else None

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
        "selected_score": selected_score,
        "blocks": blocks,
    }
    return render(request, "surveys/survey_question.html", context)


@login_required
def survey_results(request, category_id, attempt=None):
    """Результаты опроса (по умолчанию последняя попытка)"""
    category = get_object_or_404(SurveyCategory, id=category_id)

    # Если указана конкретная попытка, показываем её, иначе последнюю
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

    # Если нет завершённой сессии, но есть в процессе - продолжаем её
    if not session:
        in_progress = SurveySession.objects.filter(
            user=request.user, category=category, status="in_progress"
        ).first()

        if in_progress:
            return redirect("surveys:survey_continue", category_id=category_id)

        # Действительно нет никакой сессии
        messages.warning(request, "Вы ещё не прошли этот опрос")
        return redirect("surveys:survey_list")

    # Получаем обработчик для этого опроса
    handler = SurveyHandlerFactory.get_handler(category, session)

    # Получаем результаты
    results = None
    if hasattr(handler, "get_results"):
        results = handler.get_results()
    elif hasattr(handler, "calculate_results"):
        user_responses = UserSurveyResponse.objects.filter(
            user=request.user, question__block__category=category, session=session
        )
        results = handler.calculate_results(user_responses)

    # Получаем контекст от обработчика
    handler_context = handler.get_results_context(results) if results else {}

    # Группируем ответы по блокам (только для текущей сессии)
    blocks = category.blocks.filter(is_active=True).order_by("order")
    block_responses = []
    all_scores = []

    for block in blocks:
        questions = block.questions.filter(is_active=True).order_by("q_number")
        responses = []
        for question in questions:
            response = UserSurveyResponse.objects.filter(
                user=request.user, question=question, session=session
            ).first()
            if response:
                responses.append({"question": question, "score": response.score})
                all_scores.append(response.score)

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

    # Средний балл по опросу
    average_score = sum(all_scores) / len(all_scores) if all_scores else 0

    # Распределение ответов по шкале
    distribution = {i: 0 for i in range(1, 6)}
    for score in all_scores:
        distribution[score] += 1

    scale_labels = ScaleLabel.objects.filter(category=category).order_by("scale_value")
    if not scale_labels.exists():
        scale_labels = ScaleLabel.objects.filter(category__isnull=True).order_by(
            "scale_value"
        )
    scale_labels_dict = {sl.scale_value: sl.label for sl in scale_labels}

    # Получаем общее количество попыток
    total_attempts = SurveySession.objects.filter(
        user=request.user, category=category, status="completed"
    ).count()

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
    """Список всех попыток опроса"""
    category = get_object_or_404(SurveyCategory, id=category_id)

    sessions = SurveySession.objects.filter(
        user=request.user, category=category, status="completed"
    ).order_by("-attempt")

    context = {
        "category": category,
        "sessions": sessions,
    }
    return render(request, "surveys/survey_history.html", context)
