from neomodel import (
    StructuredNode, StringProperty, IntegerProperty,
    DateTimeProperty, BooleanProperty,
    RelationshipTo, RelationshipFrom, UniqueIdProperty
)
from datetime import datetime

class Hashtag(StructuredNode):
    # Basic hashtag information
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True, required=True, max_length=100)
    
    # Hashtag statistics
    usage_count = IntegerProperty(default=0)
    trending_score = IntegerProperty(default=0)
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    last_used = DateTimeProperty(default_now=True)
    
    # Hashtag metadata
    category = StringProperty(max_length=50)
    description = StringProperty(max_length=500)
    is_trending = BooleanProperty(default=False)
    is_banned = BooleanProperty(default=False)
    
    # Relationships
    posts = RelationshipFrom('app.models.post.Post', 'TAGGED_WITH')
    created_by = RelationshipFrom('app.models.user.User', 'CREATED_HASHTAG')
    
    def __str__(self):
        return f"Hashtag(name=#{self.name}, usage_count={self.usage_count})"
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used = datetime.now()
        self.save()
    
    def calculate_trending_score(self):
        """Calculate trending score based on recent usage"""
        # This would typically involve more complex logic
        # For now, simple calculation based on recent usage
        recent_posts = self.posts.filter(created_at__gte=datetime.now().replace(hour=0, minute=0, second=0))
        self.trending_score = len(recent_posts)
        self.is_trending = self.trending_score > 10  # Threshold for trending
        self.save()
