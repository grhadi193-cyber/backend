from typing import List

from core.exceptions import NotFoundError

from .models import Post


def get_published_posts() -> List[Post]:
    """Return all published posts ordered by published_at descending."""
    return list(Post.objects.filter(is_published=True))


def get_post_by_slug(slug: str) -> Post:
    """Return a single published post by slug, or raise NotFoundError."""
    try:
        return Post.objects.get(slug=slug, is_published=True)
    except Post.DoesNotExist:
        raise NotFoundError(f"Post with slug '{slug}' not found.")
