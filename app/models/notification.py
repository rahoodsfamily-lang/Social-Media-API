from neomodel import (
    StructuredNode, StringProperty, IntegerProperty,
    DateTimeProperty, BooleanProperty, JSONProperty,
    RelationshipTo, RelationshipFrom, UniqueIdProperty
)
from datetime import datetime

class Notification(StructuredNode):
    # Basic notification information
    uid = UniqueIdProperty()
    title = StringProperty(required=True, max_length=200)
    message = StringProperty(required=True, max_length=500)
    
    # Notification type and category
    notification_type = StringProperty(
        choices={
            'like': 'Like',
            'comment': 'Comment', 
            'follow': 'Follow',
            'mention': 'Mention',
            'share': 'Share',
            'group_invite': 'Group Invite',
            'group_request': 'Group Request',
            'post_approved': 'Post Approved',
            'friend_request': 'Friend Request',
            'birthday': 'Birthday',
            'system': 'System'
        },
        required=True
    )
    
    # Notification status
    is_read = BooleanProperty(default=False)
    is_seen = BooleanProperty(default=False)
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    read_at = DateTimeProperty()
    
    # Additional data (JSON for flexibility)
    metadata = JSONProperty(default={})
    
    # Action URL or deep link
    action_url = StringProperty()
    
    # Relationships
    recipient = RelationshipFrom('app.models.user.User', 'RECEIVED_NOTIFICATION')
    sender = RelationshipFrom('app.models.user.User', 'SENT_NOTIFICATION')
    
    # Related content
    related_post = RelationshipTo('app.models.post.Post', 'NOTIFICATION_FOR_POST')
    related_comment = RelationshipTo('app.models.comment.Comment', 'NOTIFICATION_FOR_COMMENT')
    related_group = RelationshipTo('app.models.group.Group', 'NOTIFICATION_FOR_GROUP')
    
    def __str__(self):
        return f"Notification(type={self.notification_type}, title={self.title})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now()
        self.save()
    
    def mark_as_seen(self):
        """Mark notification as seen"""
        self.is_seen = True
        self.save()
    
    @classmethod
    def create_like_notification(cls, sender, recipient, post):
        """Create a like notification"""
        notification = cls(
            title=f"{sender.username} liked your post",
            message=f"{sender.username} liked your post: {post.content[:50]}...",
            notification_type='like'
        ).save()
        
        notification.sender.connect(sender)
        notification.recipient.connect(recipient)
        notification.related_post.connect(post)
        
        return notification
    
    @classmethod
    def create_follow_notification(cls, sender, recipient):
        """Create a follow notification"""
        notification = cls(
            title=f"{sender.username} started following you",
            message=f"{sender.username} is now following you",
            notification_type='follow'
        ).save()
        
        notification.sender.connect(sender)
        notification.recipient.connect(recipient)
        
        return notification
    
    @classmethod
    def create_comment_notification(cls, sender, recipient, post, comment):
        """Create a comment notification"""
        notification = cls(
            title=f"{sender.username} commented on your post",
            message=f"{sender.username}: {comment.content[:100]}...",
            notification_type='comment'
        ).save()
        
        notification.sender.connect(sender)
        notification.recipient.connect(recipient)
        notification.related_post.connect(post)
        notification.related_comment.connect(comment)
        
        return notification
