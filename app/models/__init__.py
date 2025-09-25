from .user import User
from .post import Post
from .comment import Comment
from .group import Group
from .hashtag import Hashtag
from .notification import Notification
from .person import Person  # Keep existing model

__all__ = [
    'User',
    'Post', 
    'Comment',
    'Group',
    'Hashtag',
    'Notification',
    'Person'
]
