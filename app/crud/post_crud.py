from typing import List, Optional
from neomodel import db
from app.models.user import User
from app.models.post import Post
from app.models.hashtag import Hashtag
from app.models.notification import Notification
from app.schemas.post_schemas import PostCreate, PostUpdate
from datetime import datetime

class PostCRUD:
    
    @staticmethod
    def create_post(author: User, post_data: PostCreate) -> Post:
        """Create a new post"""
        post = Post(
            content=post_data.content,
            title=post_data.title,
            post_type=post_data.post_type.value,  # Extract enum value
            visibility=post_data.visibility.value,  # Extract enum value
            location=post_data.location,
            allow_comments=post_data.allow_comments,
            image_urls=post_data.image_urls,
            video_urls=post_data.video_urls,
            hashtags=post_data.hashtags,
            mentions=post_data.mentions
        ).save()
        
        # Connect to author
        post.author.connect(author)
        
        # Process hashtags
        for hashtag_name in post_data.hashtags:
            try:
                hashtag = Hashtag.nodes.filter(name=hashtag_name).first()
            except Hashtag.DoesNotExist:
                hashtag = None
            
            if not hashtag:
                hashtag = Hashtag(name=hashtag_name).save()
                hashtag.created_by.connect(author)
            hashtag.increment_usage()
        
        # Process mentions - create notifications
        for username in post_data.mentions:
            try:
                mentioned_user = User.nodes.filter(username=username).first()
            except User.DoesNotExist:
                mentioned_user = None
                
            if mentioned_user and mentioned_user.uid != author.uid:
                Notification(
                    title=f"{author.username} mentioned you in a post",
                    message=f"{author.username} mentioned you: {post.content[:100]}...",
                    notification_type='mention'
                ).save()
        
        # Update author's post count
        author.update_stats()
        
        return post
    
    @staticmethod
    def get_post_by_uid(uid: str) -> Optional[Post]:
        """Get post by UID"""
        try:
            return Post.nodes.filter(uid=uid).first()
        except Post.DoesNotExist:
            return None
    
    @staticmethod
    def update_post(post: Post, post_data: PostUpdate) -> Post:
        """Update post information"""
        update_data = post_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(post, field):
                # Handle enum values
                if field in ['post_type', 'visibility'] and hasattr(value, 'value'):
                    setattr(post, field, value.value)
                else:
                    setattr(post, field, value)
        
        post.updated_at = datetime.now()
        post.save()
        return post
    
    @staticmethod
    def delete_post(post: Post) -> bool:
        """Delete a post"""
        author = post.author.single()
        post.delete()
        
        # Update author's stats
        if author:
            author.update_stats()
        
        return True
    
    @staticmethod
    def like_post(user: User, post: Post) -> bool:
        """Like a post"""
        if user.liked_posts.is_connected(post):
            return False  # Already liked
        
        user.liked_posts.connect(post)
        post.update_engagement_stats()
        
        # Create notification for post author
        author = post.author.single()
        if author and author.uid != user.uid:
            Notification.create_like_notification(user, author, post)
        
        return True
    
    @staticmethod
    def unlike_post(user: User, post: Post) -> bool:
        """Unlike a post"""
        if not user.liked_posts.is_connected(post):
            return False  # Not liked
        
        user.liked_posts.disconnect(post)
        post.update_engagement_stats()
        
        return True
    
    @staticmethod
    def is_post_liked_by_user(user: User, post: Post) -> bool:
        """Check if post is liked by user"""
        return user.liked_posts.is_connected(post)
    
    @staticmethod
    def share_post(user: User, original_post: Post, content: Optional[str] = None) -> Post:
        """Share/repost a post"""
        share_post = Post(
            content=content or f"Shared from @{original_post.author.single().username}",
            post_type='text',
            visibility='public'
        ).save()
        
        # Connect relationships
        share_post.author.connect(user)
        share_post.original_post.connect(original_post)
        
        # Update stats
        original_post.update_engagement_stats()
        user.update_stats()
        
        return share_post
    
    @staticmethod
    def get_user_posts(user: User, skip: int = 0, limit: int = 20) -> List[Post]:
        """Get posts by a specific user"""
        query = """
        MATCH (user:User {uid: $uid})-[:POSTED]->(post:Post)
        WHERE post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_feed_posts(user: User, skip: int = 0, limit: int = 20) -> List[Post]:
        """Get feed posts for a user (posts from followed users)"""
        query = """
        MATCH (user:User {uid: $uid})-[:FOLLOWS]->(followed:User)-[:POSTED]->(post:Post)
        WHERE post.visibility IN ['public', 'friends'] 
          AND post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_public_posts(skip: int = 0, limit: int = 20) -> List[Post]:
        """Get public posts for explore/discover"""
        query = """
        MATCH (post:Post)
        WHERE post.visibility = 'public' 
          AND post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_trending_posts(skip: int = 0, limit: int = 20) -> List[Post]:
        """Get trending posts based on engagement"""
        query = """
        MATCH (post:Post)
        WHERE post.visibility = 'public' 
          AND post.is_archived = false
          AND post.created_at > datetime() - duration('P7D')
        RETURN post
        ORDER BY (post.likes_count + post.comments_count + post.shares_count) DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def search_posts(query: str, skip: int = 0, limit: int = 20) -> List[Post]:
        """Search posts by content"""
        cypher_query = """
        MATCH (post:Post)
        WHERE post.content CONTAINS $query 
          AND post.visibility = 'public'
          AND post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(cypher_query, {
            'query': query.lower(),
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_posts_by_hashtag(hashtag: str, skip: int = 0, limit: int = 20) -> List[Post]:
        """Get posts by hashtag"""
        query = """
        MATCH (post:Post)
        WHERE $hashtag IN post.hashtags
          AND post.visibility = 'public'
          AND post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'hashtag': hashtag.lower(),
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_liked_posts(user: User, skip: int = 0, limit: int = 20) -> List[Post]:
        """Get posts liked by user"""
        query = """
        MATCH (user:User {uid: $uid})-[:LIKED]->(post:Post)
        WHERE post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def pin_post(post: Post) -> Post:
        """Pin a post"""
        post.is_pinned = True
        post.save()
        return post
    
    @staticmethod
    def unpin_post(post: Post) -> Post:
        """Unpin a post"""
        post.is_pinned = False
        post.save()
        return post
    
    @staticmethod
    def archive_post(post: Post) -> Post:
        """Archive a post"""
        post.is_archived = True
        post.save()
        return post
    
    @staticmethod
    def unarchive_post(post: Post) -> Post:
        """Unarchive a post"""
        post.is_archived = False
        post.save()
        return post
