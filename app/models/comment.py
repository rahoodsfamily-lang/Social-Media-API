from neomodel import (
    StructuredNode, StringProperty, IntegerProperty,
    DateTimeProperty, BooleanProperty, ArrayProperty,
    RelationshipTo, RelationshipFrom, UniqueIdProperty
)
from datetime import datetime

class Comment(StructuredNode):
    # Basic comment information
    uid = UniqueIdProperty()
    content = StringProperty(required=True, max_length=1000)
    
    # Media attachments (for rich comments)
    image_url = StringProperty()
    gif_url = StringProperty()
    
    # Engagement metrics
    likes_count = IntegerProperty(default=0)
    replies_count = IntegerProperty(default=0)
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    # Comment settings
    is_edited = BooleanProperty(default=False)
    is_pinned = BooleanProperty(default=False)
    
    # Tags and mentions
    mentions = ArrayProperty(StringProperty(), default=[])
    
    # Relationships
    author = RelationshipFrom('app.models.user.User', 'COMMENTED')
    post = RelationshipFrom('app.models.post.Post', 'HAS_COMMENT')
    liked_by = RelationshipFrom('app.models.user.User', 'LIKED_COMMENT')
    
    # Nested comments (replies)
    parent_comment = RelationshipTo('app.models.comment.Comment', 'REPLY_TO')
    replies = RelationshipFrom('app.models.comment.Comment', 'REPLY_TO')
    
    def __str__(self):
        return f"Comment(uid={self.uid}, content={self.content[:30]}...)"
    
    def update_engagement_stats(self):
        """Update comment engagement statistics"""
        self.likes_count = len(self.liked_by.all())
        self.replies_count = len(self.replies.all())
        self.save()
    
    def add_mention(self, username: str):
        """Add a user mention to the comment"""
        if username not in self.mentions:
            self.mentions.append(username.lower())
            self.save()
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return bool(self.parent_comment.single())
