def year(request):
    """Добавляет переменную с текущим годом."""
    from datetime import datetime
    return {
        'year': datetime.now().year
    }
