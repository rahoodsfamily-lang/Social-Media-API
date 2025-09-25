from typing import List, Optional
from neomodel import db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.notification import Notification
from app.schemas.comment_schemas import CommentCreate, CommentUpdate
from datetime import datetime

class CommentCRUD:
    
    @staticmethod
    def create_comment(author: User, comment_data: CommentCreate) -> Comment:
        """Create a new comment"""
        # Get the post
        try:
            post = Post.nodes.filter(uid=comment_data.post_uid).first()
        except Post.DoesNotExist:
            raise ValueError("Post not found")
        
        # Create comment
        comment = Comment(
            content=comment_data.content,
            mentions=comment_data.mentions,
            image_url=comment_data.image_url,
            gif_url=comment_data.gif_url
        ).save()
        
        # Connect relationships
        comment.author.connect(author)
        comment.post.connect(post)
        
        # Handle parent comment (for replies)
        if comment_data.parent_comment_uid:
            try:
                parent_comment = Comment.nodes.filter(uid=comment_data.parent_comment_uid).first()
                comment.parent_comment.connect(parent_comment)
            except Comment.DoesNotExist:
                pass  # Parent comment not found, skip connecting
        
        # Update post stats
        post.update_engagement_stats()
        
        # Create notification for post author
        post_author = post.author.single()
        if post_author and post_author.uid != author.uid:
            Notification.create_comment_notification(author, post_author, post, comment)
        
        # Create notifications for mentions
        for username in comment_data.mentions:
            try:
                mentioned_user = User.nodes.filter(username=username).first()
                if mentioned_user and mentioned_user.uid != author.uid:
                    Notification(
                        title=f"{author.username} mentioned you in a comment",
                        message=f"{author.username} mentioned you: {comment.content[:100]}...",
                        notification_type='mention'
                    ).save()
            except User.DoesNotExist:
                pass  # User not found, skip notification
        
        return comment
    
    @staticmethod
    def get_comment_by_uid(uid: str) -> Optional[Comment]:
        """Get comment by UID"""
        try:
            return Comment.nodes.filter(uid=uid).first()
        except Comment.DoesNotExist:
            return None
    
    @staticmethod
    def update_comment(comment: Comment, comment_data: CommentUpdate) -> Comment:
        """Update comment information"""
        update_data = comment_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(comment, field):
                setattr(comment, field, value)
        
        comment.updated_at = datetime.now()
        comment.is_edited = True
        comment.save()
        return comment
    
    @staticmethod
    def delete_comment(comment: Comment) -> bool:
        """Delete a comment"""
        post = comment.post.single()
        comment.delete()
        
        # Update post stats
        if post:
            post.update_engagement_stats()
        
        return True
    
    @staticmethod
    def like_comment(user: User, comment: Comment) -> bool:
        """Like a comment"""
        if user in comment.liked_by.all():
            return False  # Already liked
        
        comment.liked_by.connect(user)
        comment.update_engagement_stats()
        
        # Create notification for comment author
        author = comment.author.single()
        if author and author.uid != user.uid:
            Notification(
                title=f"{user.username} liked your comment",
                message=f"{user.username} liked your comment: {comment.content[:50]}...",
                notification_type='like'
            ).save()
        
        return True
    
    @staticmethod
    def unlike_comment(user: User, comment: Comment) -> bool:
        """Unlike a comment"""
        if user not in comment.liked_by.all():
            return False  # Not liked
        
        comment.liked_by.disconnect(user)
        comment.update_engagement_stats()
        
        return True
    
    @staticmethod
    def is_comment_liked_by_user(user: User, comment: Comment) -> bool:
        """Check if comment is liked by user"""
        return user in comment.liked_by.all()
    
    @staticmethod
    def get_post_comments(post: Post, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get comments for a specific post (top-level comments only)"""
        query = """
        MATCH (post:Post {uid: $post_uid})-[:HAS_COMMENT]->(comment:Comment)
        WHERE NOT EXISTS((comment)-[:REPLY_TO]->(:Comment))
        RETURN comment
        ORDER BY comment.created_at ASC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'post_uid': post.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Comment.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_comment_replies(comment: Comment, skip: int = 0, limit: int = 10) -> List[Comment]:
        """Get replies to a specific comment"""
        query = """
        MATCH (parent:Comment {uid: $comment_uid})<-[:REPLY_TO]-(reply:Comment)
        RETURN reply
        ORDER BY reply.created_at ASC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'comment_uid': comment.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Comment.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_user_comments(user: User, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get comments by a specific user"""
        query = """
        MATCH (user:User {uid: $uid})-[:COMMENTED]->(comment:Comment)
        RETURN comment
        ORDER BY comment.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Comment.inflate(row[0]) for row in results]
    
    @staticmethod
    def pin_comment(comment: Comment) -> Comment:
        """Pin a comment"""
        comment.is_pinned = True
        comment.save()
        return comment
    
    @staticmethod
    def unpin_comment(comment: Comment) -> Comment:
        """Unpin a comment"""
        comment.is_pinned = False
        comment.save()
        return comment
    
    @staticmethod
    def get_comment_thread(comment: Comment) -> List[Comment]:
        """Get the full thread of a comment (parent and all replies)"""
        # Get the root comment
        root_comment = comment
        parent = comment.parent_comment.single()
        while parent:
            root_comment = parent
            parent = root_comment.parent_comment.single()
        
        # Get all replies in the thread
        query = """
        MATCH path = (root:Comment {uid: $root_uid})<-[:REPLY_TO*0..]-(comment:Comment)
        RETURN comment
        ORDER BY comment.created_at ASC
        """
        results, _ = db.cypher_query(query, {
            'root_uid': root_comment.uid
        })
        
        return [Comment.inflate(row[0]) for row in results]
