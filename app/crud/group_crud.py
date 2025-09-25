from typing import List, Optional
from neomodel import db
from app.models.user import User
from app.models.group import Group
from app.models.post import Post
from app.schemas.group_schemas import GroupCreate, GroupUpdate
from datetime import datetime

class GroupCRUD:
    
    @staticmethod
    def create_group(owner: User, group_data: GroupCreate) -> Group:
        """Create a new group"""
        # Check if group name already exists
        try:
            existing_group = Group.nodes.filter(name=group_data.name).first()
            if existing_group:
                raise ValueError("Group name already exists")
        except Group.DoesNotExist:
            # Group doesn't exist, which is what we want
            pass
        
        # Create group
        group = Group(
            name=group_data.name,
            description=group_data.description,
            group_type=group_data.group_type.value,  # Extract enum value
            category=group_data.category,
            location=group_data.location,
            allow_member_posts=group_data.allow_member_posts,
            require_approval=group_data.require_approval,
            tags=group_data.tags,
            rules=group_data.rules,
            guidelines=group_data.guidelines
        ).save()
        
        # Connect owner
        group.owner.connect(owner)
        group.members.connect(owner)  # Owner is also a member
        
        # Update stats
        group.update_stats()
        
        return group
    
    @staticmethod
    def get_group_by_uid(uid: str) -> Optional[Group]:
        """Get group by UID"""
        try:
            return Group.nodes.filter(uid=uid).first()
        except Group.DoesNotExist:
            return None
    
    @staticmethod
    def get_group_by_name(name: str) -> Optional[Group]:
        """Get group by name"""
        try:
            return Group.nodes.filter(name=name).first()
        except Group.DoesNotExist:
            return None
    
    @staticmethod
    def update_group(group: Group, group_data: GroupUpdate) -> Group:
        """Update group information"""
        update_data = group_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(group, field):
                setattr(group, field, value)
        
        group.updated_at = datetime.now()
        group.save()
        return group
    
    @staticmethod
    def delete_group(group: Group) -> bool:
        """Delete a group"""
        group.delete()
        return True
    
    @staticmethod
    def join_group(user: User, group: Group) -> bool:
        """Join a group"""
        if group.is_member(user):
            return False  # Already a member
        
        if group.require_approval:
            # Add to pending requests
            group.pending_requests.connect(user)
            return False  # Pending approval
        else:
            # Join immediately
            group.add_member(user)
            return True
    
    @staticmethod
    def leave_group(user: User, group: Group) -> bool:
        """Leave a group"""
        if not group.is_member(user):
            return False  # Not a member
        
        # Check if user is the owner
        if group.owner.is_connected(user):
            raise ValueError("Owner cannot leave the group. Transfer ownership first.")
        
        group.remove_member(user)
        
        # Remove from admin/moderator roles if applicable
        if group.admins.is_connected(user):
            group.admins.disconnect(user)
        if group.moderators.is_connected(user):
            group.moderators.disconnect(user)
        
        return True
    
    @staticmethod
    def approve_join_request(group: Group, user: User, approver: User) -> bool:
        """Approve a join request"""
        if not group.is_admin(approver):
            raise ValueError("Only admins can approve join requests")
        
        if not group.pending_requests.is_connected(user):
            return False  # No pending request
        
        group.pending_requests.disconnect(user)
        group.add_member(user)
        
        return True
    
    @staticmethod
    def reject_join_request(group: Group, user: User, approver: User) -> bool:
        """Reject a join request"""
        if not group.is_admin(approver):
            raise ValueError("Only admins can reject join requests")
        
        if not group.pending_requests.is_connected(user):
            return False  # No pending request
        
        group.pending_requests.disconnect(user)
        return True
    
    @staticmethod
    def promote_member(group: Group, user: User, role: str, promoter: User) -> bool:
        """Promote a member to admin or moderator"""
        if not group.owner.is_connected(promoter):
            raise ValueError("Only the owner can promote members")
        
        if not group.is_member(user):
            raise ValueError("User is not a member of the group")
        
        if role == "admin":
            if not group.admins.is_connected(user):
                group.admins.connect(user)
        elif role == "moderator":
            if not group.moderators.is_connected(user):
                group.moderators.connect(user)
        else:
            raise ValueError("Invalid role")
        
        return True
    
    @staticmethod
    def demote_member(group: Group, user: User, demoter: User) -> bool:
        """Demote a member from admin or moderator"""
        if not group.owner.is_connected(demoter):
            raise ValueError("Only the owner can demote members")
        
        if group.admins.is_connected(user):
            group.admins.disconnect(user)
        if group.moderators.is_connected(user):
            group.moderators.disconnect(user)
        
        return True
    
    @staticmethod
    def remove_member(group: Group, user: User, remover: User) -> bool:
        """Remove a member from the group"""
        if not group.is_admin(remover):
            raise ValueError("Only admins can remove members")
        
        if group.owner.is_connected(user):
            raise ValueError("Cannot remove the owner")
        
        group.remove_member(user)
        
        # Remove from admin/moderator roles if applicable
        if group.admins.is_connected(user):
            group.admins.disconnect(user)
        if group.moderators.is_connected(user):
            group.moderators.disconnect(user)
        
        return True
    
    @staticmethod
    def get_user_groups(user: User, skip: int = 0, limit: int = 20) -> List[Group]:
        """Get groups that user is a member of"""
        query = """
        MATCH (user:User {uid: $uid})-[:MEMBER_OF]->(group:Group)
        WHERE group.is_active = true
        RETURN group
        ORDER BY group.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Group.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_owned_groups(user: User, skip: int = 0, limit: int = 20) -> List[Group]:
        """Get groups owned by user"""
        query = """
        MATCH (user:User {uid: $uid})-[:OWNS]->(group:Group)
        WHERE group.is_active = true
        RETURN group
        ORDER BY group.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': user.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Group.inflate(row[0]) for row in results]
    
    @staticmethod
    def search_groups(query: str, skip: int = 0, limit: int = 20) -> List[Group]:
        """Search groups by name or description"""
        cypher_query = """
        MATCH (g:Group)
        WHERE (g.name CONTAINS $query OR g.description CONTAINS $query)
          AND g.group_type IN ['public', 'private']
          AND g.is_active = true
        RETURN g
        ORDER BY g.members_count DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(cypher_query, {
            'query': query.lower(),
            'skip': skip,
            'limit': limit
        })
        
        return [Group.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_public_groups(skip: int = 0, limit: int = 20) -> List[Group]:
        """Get public groups"""
        query = """
        MATCH (g:Group)
        WHERE g.group_type = 'public' AND g.is_active = true
        RETURN g
        ORDER BY g.members_count DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'skip': skip,
            'limit': limit
        })
        
        return [Group.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_group_members(group: Group, skip: int = 0, limit: int = 50) -> List[User]:
        """Get group members"""
        query = """
        MATCH (group:Group {uid: $uid})<-[:MEMBER_OF]-(user:User)
        RETURN user
        ORDER BY user.username
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': group.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [User.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_group_posts(group: Group, skip: int = 0, limit: int = 20) -> List[Post]:
        """Get posts in a group"""
        query = """
        MATCH (group:Group {uid: $uid})<-[:POSTED_IN]-(post:Post)
        WHERE post.is_archived = false
        RETURN post
        ORDER BY post.created_at DESC
        SKIP $skip LIMIT $limit
        """
        results, _ = db.cypher_query(query, {
            'uid': group.uid,
            'skip': skip,
            'limit': limit
        })
        
        return [Post.inflate(row[0]) for row in results]
    
    @staticmethod
    def get_pending_requests(group: Group) -> List[User]:
        """Get pending join requests for a group"""
        query = """
        MATCH (group:Group {uid: $uid})<-[:REQUESTED_TO_JOIN]-(user:User)
        RETURN user
        ORDER BY user.username
        """
        results, _ = db.cypher_query(query, {
            'uid': group.uid
        })
        
        return [User.inflate(row[0]) for row in results]
    
    @staticmethod
    def transfer_ownership(group: Group, new_owner: User, current_owner: User) -> bool:
        """Transfer group ownership"""
        if not group.owner.is_connected(current_owner):
            raise ValueError("Only the current owner can transfer ownership")
        
        if not group.is_member(new_owner):
            raise ValueError("New owner must be a member of the group")
        
        # Disconnect current owner
        group.owner.disconnect(current_owner)
        
        # Connect new owner
        group.owner.connect(new_owner)
        
        # Make new owner an admin if not already
        if not group.admins.is_connected(new_owner):
            group.admins.connect(new_owner)
        
        return True
