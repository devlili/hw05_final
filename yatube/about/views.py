from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Страница об авторе сайта."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Страница об используемых технологиях."""
    template_name = 'about/tech.html'
