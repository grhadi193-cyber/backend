from typing import List

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from core.exceptions import NotFoundError

from .schemas import PostDetailOut, PostListOut
from .services import get_post_by_slug, get_published_posts

router = Router(tags=["Blog"])


@router.get("/posts", response=List[PostListOut], summary="لیست پست‌های منتشر شده")
def list_posts(request: HttpRequest):
    return get_published_posts()


@router.get("/posts/{slug}", response=PostDetailOut, summary="جزئیات پست")
def retrieve_post(request: HttpRequest, slug: str):
    try:
        return get_post_by_slug(slug)
    except NotFoundError as exc:
        raise HttpError(404, str(exc))
