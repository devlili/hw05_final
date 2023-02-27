from django.core.paginator import Paginator

from yatube.settings import POSTS_PER_PAGE


def paginate(request, posts, pagesize=POSTS_PER_PAGE):
    """Паджинатор - разбивка на страницы."""
    paginator = Paginator(posts, pagesize)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
