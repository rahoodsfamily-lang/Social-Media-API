from typing import List, Optional
from neomodel import db
from passlib.context import CryptContext
from app.models.user import User
from app.models.notification import Notification
from app.schemas.user_schemas import UserCreate, UserUpdate
from datetime import datetime

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCRUD:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_user(user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if username or email already exists
        try:
            existing_user = User.nodes.filter(
                username=user_data.username
            ).first()
            if existing_user:
                raise ValueError("Username already exists")
        except User.DoesNotExist:
            pass  # Username is available
        
        try:
            existing_email = User.nodes.filter(
                email=user_data.email
            ).first()
            if existing_email:
                raise ValueError("Email already exists")
        except User.DoesNotExist:
            pass  # Email is available
        
        # Hash password
        hashed_password = UserCRUD.hash_password(user_data.password)
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            bio=user_data.bio,
            location=user_data.location,
            website=user_data.website,
            phone_number=user_data.phone_number,
            is_private=user_data.is_private,
            interests=user_data.interests
        ).save()
        
        return user
    
    @staticmethod
    def get_user_by_uid(uid: str) -> Optional[User]:
        """Get user by UID"""
        try:
            return User.nodes.filter(uid=uid).first()
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return User.nodes.filter(username=username).first()
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return User.nodes.filter(email=email).first()
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_username_or_email(identifier: str) -> Optional[User]:
        """Get user by username or email"""
        try:
            user = User.nodes.filter(username=identifier).first()
            return user
        except User.DoesNotExist:
            try:
                user = User.nodes.filter(email=identifier).first()
                return user
            except User.DoesNotExist:
                return None
    
    @staticmethod
    def authenticate_user(username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password"""
        user = UserCRUD.get_user_by_username_or_email(username_or_email)
        if not user:
            return None
        if not UserCRUD.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.now()
        user.save()
        
        return user
    
    @staticmethod
    def update_user(user: User, user_data: UserUpdate) -> User:
        """Update user information"""
        update_data = user_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.now()
        user.save()
        return user
    
    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> bool:
        """Change user password"""
        if not UserCRUD.verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = UserCRUD.hash_password(new_password)
        user.updated_at = datetime.now()
        user.save()
        return True
    
    @staticmethod
    def follow_user(follower: User, following: User) -> bool:
        """Follow a user"""
        if follower.uid == following.uid:
            raise ValueError("Cannot follow yourself")
        
        if follower.following.is_connected(following):
            return False  # Already following
        
        follower.following.connect(following)
        
        # Update stats
        follower.update_stats()
        following.update_stats()
        
        # Create notification
        Notification.create_follow_notification(follower, following)
        
        return True
    
    @staticmethod
    def unfollow_user(follower: User, following: User) -> bool:
        """Unfollow a user"""
        if not follower.following.is_connected(following):
            return False  # Not following
        
        follower.following.disconnect(following)
        
        # Update stats
        follower.update_stats()
        following.update_stats()
        
        return True
    
    @staticmethod
    def is_following(follower: User, following: User) -> bool:
        """Check if user is following another user"""
        return follower.following.is_connected(following)
    
    @staticmethod
    def get_followers(user: User, skip: int = 0, limit: int = 20) -> List[User]:
        """Get user's followers"""
        query = """
        MATCH (follower:User)-[:FOLLOWS]->(user:User {uid: $uid})
        RETURN follower
        ORDER BY follower.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [User.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_following(user: User, skip: int = 0, limit: int = 20) -> List[User]:
        """Get users that the user is following"""
        query = """
        MATCH (user:User {uid: $uid})-[:FOLLOWS]->(following:User)
        RETURN following
        ORDER BY following.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [User.inflate(row[0]) for row in results]
    
    @staticmethod
    def search_users(query: str, skip: int = 0, limit: int = 20) -> List[User]:
        """Search users by username, first name, or last name"""
        cypher_query = """
        MATCH (u:User)
        WHERE u.username CONTAINS $query 
           OR u.first_name CONTAINS $query 
           OR u.last_name CONTAINS $query
        RETURN u
        ORDER BY u.username
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(cypher_query, {
            'query': query.lower(),
            'skip': skip,
            'limit': limit
        })
        
        return [User.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_user_suggestions(user: User, limit: int = 10) -> List[User]:
        """Get user suggestions based on mutual connections and interests"""
        query = """
        MATCH (user:User {uid: $uid})-[:FOLLOWS]->(following:User)-[:FOLLOWS]->(suggested:User)
        WHERE NOT (user)-[:FOLLOWS]->(suggested) 
          AND user.uid <> suggested.uid
        WITH suggested, COUNT(*) as mutual_connections
        ORDER BY mutual_connections DESC
        RETURN suggested
        LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'limit': limit
        })
        
        return [User.inflate(row[0]) for row in results]
    
    @staticmethod
    def deactivate_user(user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        user.updated_at = datetime.now()
        user.save()
        return user
    
    @staticmethod
    def activate_user(user: User) -> User:
        """Activate user account"""
        user.is_active = True
        user.updated_at = datetime.now()
        user.save()
        return user
