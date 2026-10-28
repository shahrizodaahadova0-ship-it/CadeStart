from .catalog import LESSONS, TASKS
from .models import LessonContent, TaskContent


def get_lessons():
    content = {row.slug: row for row in LessonContent.objects.all()}
    result = []
    for original in LESSONS:
        lesson = dict(original)
        row = content.get(lesson['slug'])
        if row:
            lesson.update(title=row.title, uz=row.title_uz, summary=row.summary,
                          uz_summary=row.summary_uz, text=row.text, uz_text=row.text_uz,
                          hint=row.hint, uz_hint=row.hint_uz, code=row.code,
                          minutes=row.minutes, content_id=row.pk)
        result.append(lesson)
    return result


def get_tasks():
    content = {row.slug: row for row in TaskContent.objects.all()}
    result = []
    for original in TASKS:
        task = {**original, 'revision': 1}
        row = content.get(task['slug'])
        if row:
            task.update(title=row.title, uz=row.title_uz, description=row.description,
                        uz_description=row.description_uz, requirements=row.requirements,
                        uz_requirements=row.requirements_uz, tag=row.tag, priority=row.priority,
                        revision=row.revision, content_id=row.pk)
        result.append(task)
    return result
