from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    year_today = datetime.now().year
    return {
        'year': year_today,
    }
