from neomodel import (
    StructuredNode, StringProperty, IntegerProperty, 
    DateTimeProperty, BooleanProperty, EmailProperty,
    RelationshipTo, RelationshipFrom, Relationship,
    UniqueIdProperty, ArrayProperty
)
from datetime import datetime
from typing import Optional

class User(StructuredNode):
    # Basic user information
    uid = UniqueIdProperty()
    username = StringProperty(unique_index=True, required=True, max_length=50)
    email = EmailProperty(unique_index=True, required=True)
    password_hash = StringProperty(required=True)
    
    # Profile information
    first_name = StringProperty(max_length=50)
    last_name = StringProperty(max_length=50)
    bio = StringProperty(max_length=500)
    profile_picture_url = StringProperty()
    cover_photo_url = StringProperty()
    
    # Account settings
    is_active = BooleanProperty(default=True)
    is_verified = BooleanProperty(default=False)
    is_private = BooleanProperty(default=False)
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    last_login = DateTimeProperty()
    
    # Location and contact
    location = StringProperty(max_length=100)
    website = StringProperty()
    phone_number = StringProperty()
    
    # Social stats (will be calculated dynamically)
    followers_count = IntegerProperty(default=0)
    following_count = IntegerProperty(default=0)
    posts_count = IntegerProperty(default=0)
    
    # Interests and tags
    interests = ArrayProperty(StringProperty(), default=[])
    
    # Relationships
    posts = RelationshipTo('app.models.post.Post', 'POSTED')
    liked_posts = RelationshipTo('app.models.post.Post', 'LIKED')
    commented_posts = RelationshipTo('app.models.post.Post', 'COMMENTED_ON')
    
    # User relationships
    following = RelationshipTo('app.models.user.User', 'FOLLOWS')
    followers = RelationshipFrom('app.models.user.User', 'FOLLOWS')
    blocked_users = RelationshipTo('app.models.user.User', 'BLOCKED')
    
    # Groups and communities
    joined_groups = RelationshipTo('app.models.group.Group', 'MEMBER_OF')
    owned_groups = RelationshipTo('app.models.group.Group', 'OWNS')
    
    def __str__(self):
        return f"User(username={self.username}, email={self.email})"
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def update_stats(self):
        """Update user statistics"""
        self.followers_count = len(self.followers.all())
        self.following_count = len(self.following.all())
        self.posts_count = len(self.posts.all())
        self.save()
