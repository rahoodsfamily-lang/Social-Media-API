from neomodel import (
    StructuredNode, StringProperty, IntegerProperty,
    DateTimeProperty, BooleanProperty, ArrayProperty,
    RelationshipTo, RelationshipFrom, UniqueIdProperty
)
from datetime import datetime

class Post(StructuredNode):
    # Basic post information
    uid = UniqueIdProperty()
    content = StringProperty(required=True, max_length=2000)
    title = StringProperty(max_length=200)
    
    # Media attachments
    image_urls = ArrayProperty(StringProperty(), default=[])
    video_urls = ArrayProperty(StringProperty(), default=[])
    
    # Post metadata
    post_type = StringProperty(choices={
        'text': 'Text',
        'image': 'Image', 
        'video': 'Video',
        'link': 'Link',
        'poll': 'Poll'
    }, default='text')
    visibility = StringProperty(choices={
        'public': 'Public',
        'friends': 'Friends',
        'private': 'Private'
    }, default='public')
    
    # Engagement metrics
    likes_count = IntegerProperty(default=0)
    comments_count = IntegerProperty(default=0)
    shares_count = IntegerProperty(default=0)
    views_count = IntegerProperty(default=0)
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    # Post settings
    allow_comments = BooleanProperty(default=True)
    is_pinned = BooleanProperty(default=False)
    is_archived = BooleanProperty(default=False)
    
    # Tags and mentions
    hashtags = ArrayProperty(StringProperty(), default=[])
    mentions = ArrayProperty(StringProperty(), default=[])
    
    # Location
    location = StringProperty()
    
    # Relationships
    author = RelationshipFrom('app.models.user.User', 'POSTED')
    liked_by = RelationshipFrom('app.models.user.User', 'LIKED')
    comments = RelationshipTo('app.models.comment.Comment', 'HAS_COMMENT')
    shared_by = RelationshipFrom('app.models.user.User', 'SHARED')
    
    # Original post for shares/reposts
    original_post = RelationshipTo('app.models.post.Post', 'SHARES')
    shared_from = RelationshipFrom('app.models.post.Post', 'SHARES')
    
    # Group association
    posted_in_group = RelationshipTo('app.models.group.Group', 'POSTED_IN')
    
    def __str__(self):
        return f"Post(uid={self.uid}, content={self.content[:50]}...)"
    
    def update_engagement_stats(self):
        """Update post engagement statistics"""
        self.likes_count = len(self.liked_by.all())
        self.comments_count = len(self.comments.all())
        self.shares_count = len(self.shared_by.all())
        self.save()
    
    def add_hashtag(self, hashtag: str):
        """Add a hashtag to the post"""
        if hashtag not in self.hashtags:
            self.hashtags.append(hashtag.lower())
            self.save()
    
    def add_mention(self, username: str):
        """Add a user mention to the post"""
        if username not in self.mentions:
            self.mentions.append(username.lower())
            self.save()
