"""
Сбор данных для выгрузки.

Формирует «плоский» список строк, готовый к записи в Excel/CSV.
Выгружаются только пользователи с типом «Работник» (employee).
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from apps.surveys.models import (
    ProfessionalStandard,
    RiasacResult,
)
from apps.recommendations.models import CourseRecommendation, SelectedCourse


def _riasec_directions(user):
    """
    Возвращает dict:
        {
          "VO":  [{"code": "01.03.02", "name": "...", "ps_code": "01.001", "ps_name": "..."}],
          "SPO": [...],
        }

    Логика:
     1. Берём career_code пользователя из RiasacResult (например, "RIA").
     2. Находим ProfessionalStandard, у которых в riasec_codes есть этот код.
     3. Через ProfessionalStandardProgram находим связанные EducationProgram,
        разделяем по education_level (VO/SPO).
    """
    result = {"VO": [], "SPO": []}

    riasac = (
        RiasacResult.objects.filter(session__user=user).order_by("-created_at").first()
    )
    if not riasac or not riasac.career_code:
        return result

    career_code = riasac.career_code.strip().upper()
    if len(career_code) != 3:
        return result

    standards = (
        ProfessionalStandard.objects.filter(
            riasec_codes__code=career_code,
            is_active=True,
        )
        .distinct()
        .prefetch_related("program_links__education_program")
    )

    seen = {"VO": set(), "SPO": set()}

    for ps in standards:
        for link in ps.program_links.all():
            prog = link.education_program
            key = (prog.code, prog.education_level)
            if key in seen[prog.education_level]:
                continue
            seen[prog.education_level].add(key)
            result[prog.education_level].append(
                {
                    "code": prog.code,
                    "name": prog.name,
                    "ps_code": ps.code,
                    "ps_name": ps.name,
                }
            )

    return result


def _format_directions(items, limit=20):
    """Список направлений в одну строку: '01.03.02 Математика; ...'"""
    if not items:
        return ""
    items = items[:limit]
    return "; ".join(f"{i['code']} {i['name']}" for i in items)


def _format_recommendations(user, limit=50):
    """Строка рекомендаций: 'Курс 1 (75%); Курс 2 (60%)'"""
    qs = (
        CourseRecommendation.objects.filter(user=user)
        .select_related("course")
        .order_by("order", "-relevance_score")[:limit]
    )
    parts = []
    for rec in qs:
        percent = rec.get_relevance_percent()
        parts.append(f"{rec.course.title} ({percent}%)")
    return "; ".join(parts)


def _format_selected_courses(user, limit=50):
    """Строка выбранных курсов со статусом одобрения."""
    qs = (
        SelectedCourse.objects.filter(user=user)
        .select_related("course", "approval")
        .order_by("-created_at")[:limit]
    )
    parts = []
    for sc in qs:
        approval = getattr(sc, "approval", None)
        status = approval.get_status_display() if approval else "—"
        parts.append(f"{sc.course.title} [{status}]")
    return "; ".join(parts)


def collect_rows(filters=None):
    """
    Возвращает список dict-строк для выгрузки.

    Выборка всегда ограничена пользователями с user_type='employee'.

    Фильтры (опционально):
        - organization_id: int
        - only_with_riasec: bool
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    filters = filters or {}

    qs = (
        User.objects.filter(user_type="employee")
        .select_related("organization", "employee_profile")
        .prefetch_related("employee_profile__desired_organization_type")
        .order_by("id")
    )

    if filters.get("organization_id"):
        qs = qs.filter(organization_id=filters["organization_id"])

    rows = []
    for user in qs:
        employee_profile = getattr(user, "employee_profile", None)

        # --- RIASEC ---
        riasac = (
            RiasacResult.objects.filter(session__user=user)
            .order_by("-created_at")
            .first()
        )

        if filters.get("only_with_riasec") and not riasac:
            continue

        career_code = riasac.career_code if riasac else ""
        scores = riasac.get_scores_dict() if riasac else {}

        # --- Направления по RIASEC ---
        directions = _riasec_directions(user) if riasac else {"VO": [], "SPO": []}

        row = {
            # Пользователь
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "patronymic": user.patronymic,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "date_joined": (
                user.date_joined.strftime("%Y-%m-%d %H:%M") if user.date_joined else ""
            ),
            "birthday": user.birthday.strftime("%Y-%m-%d") if user.birthday else "",
            "snils": user.snils or "",
            # Организация
            "organization": user.organization.short_name if user.organization else "",
            "organization_inn": user.organization.inn if user.organization else "",
            # Профиль работника
            "position": employee_profile.position if employee_profile else "",
            "position_level": (
                employee_profile.get_position_level_display()
                if employee_profile and employee_profile.position_level
                else ""
            ),
            "gender": (
                employee_profile.get_gender_display()
                if employee_profile and employee_profile.gender
                else ""
            ),
            "citizenship": employee_profile.citizenship if employee_profile else "",
            "phone": employee_profile.phone if employee_profile else "",
            "municipality": employee_profile.municipality if employee_profile else "",
            "locality": employee_profile.locality if employee_profile else "",
            "employment_status": (
                employee_profile.get_employment_status_display()
                if employee_profile and employee_profile.employment_status
                else ""
            ),
            "work_experience_years": (
                employee_profile.work_experience_years if employee_profile else ""
            ),
            "is_unemployed": (
                employee_profile.is_unemployed if employee_profile else ""
            ),
            "is_svo_participant": (
                employee_profile.is_svo_participant if employee_profile else ""
            ),
            "education_level": (
                employee_profile.get_education_level_display()
                if employee_profile and employee_profile.education_level
                else ""
            ),
            "education_institution": (
                employee_profile.education_institution if employee_profile else ""
            ),
            "graduation_year": (
                employee_profile.graduation_year if employee_profile else ""
            ),
            "specialty": employee_profile.specialty if employee_profile else "",
            "desired_organization_type": (
                employee_profile.desired_organization_type.name
                if employee_profile and employee_profile.desired_organization_type
                else ""
            ),
            "desired_organization": (
                employee_profile.desired_organization if employee_profile else ""
            ),
            "desired_position": (
                employee_profile.desired_position if employee_profile else ""
            ),
            # RIASEC результат
            "riasec_career_code": career_code,
            "riasec_r": scores.get("R", ""),
            "riasec_i": scores.get("I", ""),
            "riasec_a": scores.get("A", ""),
            "riasec_s": scores.get("S", ""),
            "riasec_e": scores.get("E", ""),
            "riasec_c": scores.get("C", ""),
            "riasec_dominant": riasac.dominant_types if riasac else "",
            "riasec_created_at": (
                riasac.created_at.strftime("%Y-%m-%d %H:%M") if riasac else ""
            ),
            # Направления по RIASEC
            "directions_vo": _format_directions(directions["VO"]),
            "directions_spo": _format_directions(directions["SPO"]),
            "directions_vo_count": len(directions["VO"]),
            "directions_spo_count": len(directions["SPO"]),
            # Рекомендации курсов
            "recommendations": _format_recommendations(user),
            "recommendations_count": CourseRecommendation.objects.filter(
                user=user
            ).count(),
            # Выбранные курсы
            "selected_courses": _format_selected_courses(user),
            "selected_courses_count": SelectedCourse.objects.filter(user=user).count(),
        }
        rows.append(row)

    return rows


COLUMNS = [
    ("user_id", "ID пользователя"),
    ("username", "Логин"),
    ("email", "Email"),
    ("last_name", "Фамилия"),
    ("first_name", "Имя"),
    ("patronymic", "Отчество"),
    ("full_name", "ФИО"),
    ("is_active", "Активен"),
    ("date_joined", "Дата регистрации"),
    ("birthday", "Дата рождения"),
    ("snils", "СНИЛС"),
    ("organization", "Организация"),
    ("organization_inn", "ИНН организации"),
    ("position", "Должность"),
    ("position_level", "Категория должности"),
    ("gender", "Пол"),
    ("citizenship", "Гражданство"),
    ("phone", "Телефон"),
    ("municipality", "Муниципалитет"),
    ("locality", "Населённый пункт"),
    ("employment_status", "Статус занятости"),
    ("work_experience_years", "Стаж (лет)"),
    ("is_unemployed", "Безработный"),
    ("is_svo_participant", "Участник СВО"),
    ("education_level", "Уровень образования"),
    ("education_institution", "Учебное заведение"),
    ("graduation_year", "Год окончания"),
    ("specialty", "Специальность"),
    ("desired_organization_type", "Желаемая сфера"),
    ("desired_organization", "Желаемая организация"),
    ("desired_position", "Желаемая должность"),
    ("riasec_career_code", "RIASEC код"),
    ("riasec_r", "R"),
    ("riasec_i", "I"),
    ("riasec_a", "A"),
    ("riasec_s", "S"),
    ("riasec_e", "E"),
    ("riasec_c", "C"),
    ("riasec_dominant", "Доминирующие типы"),
    ("riasec_created_at", "RIASEC рассчитан"),
    ("directions_vo", "Направления ВО по RIASEC"),
    ("directions_spo", "Направления СПО по RIASEC"),
    ("directions_vo_count", "Кол-во ВО"),
    ("directions_spo_count", "Кол-во СПО"),
    ("recommendations", "Рекомендованные курсы"),
    ("recommendations_count", "Кол-во рекомендаций"),
    ("selected_courses", "Выбранные курсы"),
    ("selected_courses_count", "Кол-во выбранных курсов"),
]


def write_xlsx(rows, path):
    """Записывает строки в Excel-файл."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Работники"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F46E5")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Заголовки
    for col_idx, (_, title) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    # Данные
    for row_idx, row in enumerate(rows, start=2):
        for col_idx, (key, _) in enumerate(COLUMNS, start=1):
            ws.cell(row=row_idx, column=col_idx, value=row.get(key, ""))

    # Ширина колонок
    for col_idx, (key, title) in enumerate(COLUMNS, start=1):
        max_len = len(str(title))
        for row in rows[:200]:
            val = str(row.get(key, "") or "")
            max_len = max(max_len, min(len(val), 60))
        ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 2

    # Автофильтр + закрепление первой строки
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    wb.save(path)
    return path
