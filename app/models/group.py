from neomodel import (
    StructuredNode, StringProperty, IntegerProperty,
    DateTimeProperty, BooleanProperty, ArrayProperty,
    RelationshipTo, RelationshipFrom, UniqueIdProperty
)
from datetime import datetime

class Group(StructuredNode):
    # Basic group information
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True, required=True, max_length=100)
    description = StringProperty(max_length=1000)
    
    # Group settings
    group_type = StringProperty(choices={
        'public': 'Public',
        'private': 'Private',
        'secret': 'Secret'
    }, default='public')
    category = StringProperty(max_length=50)
    
    # Visual elements
    profile_picture_url = StringProperty()
    cover_photo_url = StringProperty()
    
    # Group rules and guidelines
    rules = ArrayProperty(StringProperty(), default=[])
    guidelines = StringProperty(max_length=2000)
    
    # Group statistics
    members_count = IntegerProperty(default=0)
    posts_count = IntegerProperty(default=0)
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    # Group settings
    allow_member_posts = BooleanProperty(default=True)
    require_approval = BooleanProperty(default=False)
    is_active = BooleanProperty(default=True)
    
    # Tags and topics
    tags = ArrayProperty(StringProperty(), default=[])
    location = StringProperty()
    
    # Relationships
    owner = RelationshipFrom('app.models.user.User', 'OWNS')
    admins = RelationshipFrom('app.models.user.User', 'ADMIN_OF')
    moderators = RelationshipFrom('app.models.user.User', 'MODERATOR_OF')
    members = RelationshipFrom('app.models.user.User', 'MEMBER_OF')
    
    # Group content
    posts = RelationshipFrom('app.models.post.Post', 'POSTED_IN')
    
    # Group interactions
    pending_requests = RelationshipFrom('app.models.user.User', 'REQUESTED_TO_JOIN')
    banned_users = RelationshipFrom('app.models.user.User', 'BANNED_FROM')
    
    def __str__(self):
        return f"Group(name={self.name}, type={self.group_type})"
    
    def update_stats(self):
        """Update group statistics"""
        self.members_count = len(self.members.all())
        self.posts_count = len(self.posts.all())
        self.save()
    
    def add_member(self, user):
        """Add a user to the group"""
        if not self.members.is_connected(user):
            self.members.connect(user)
            self.update_stats()
    
    def remove_member(self, user):
        """Remove a user from the group"""
        if self.members.is_connected(user):
            self.members.disconnect(user)
            self.update_stats()
    
    def is_member(self, user):
        """Check if user is a member of the group"""
        return self.members.is_connected(user)
    
    def is_admin(self, user):
        """Check if user is an admin of the group"""
        return self.admins.is_connected(user) or self.owner.is_connected(user)
    
    def add_rule(self, rule: str):
        """Add a rule to the group"""
        if rule not in self.rules:
            self.rules.append(rule)
            self.save()
