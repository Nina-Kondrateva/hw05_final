from django.conf import settings
from django.core.paginator import Paginator


def get_page(posts, request):
    paginator = Paginator(posts, settings.POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {'paginator': paginator, 'page_number': page_number,
            'page_obj': page_obj}
