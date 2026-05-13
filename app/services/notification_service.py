from app.extensions import db
from app.models.admin.notification import Notification

class NotificationService:
    @staticmethod
    def create_notification(user_id, organization_id, title, message, link=None, type='INFO'):
        """Create a notification for a specific user."""
        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            message=message,
            link=link,
            type=type
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def create_org_notification(organization_id, title, message, link=None, type='INFO'):
        """Create a notification for all users in an organization."""
        from app.models.admin.organization import OrganizationMembership
        
        memberships = OrganizationMembership.query.filter_by(organization_id=organization_id, is_active=True).all()
        
        for membership in memberships:
            notification = Notification(
                user_id=membership.user_id,
                organization_id=organization_id,
                title=title,
                message=message,
                link=link,
                type=type
            )
            db.session.add(notification)
            
        db.session.commit()
