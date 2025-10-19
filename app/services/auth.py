from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..models.database import User

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, settings):
        self.settings = settings
        self.google_client_id = settings.google_client_id

    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token against Google's servers
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.google_client_id
            )

            # Additional validation
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # Return user info
            return {
                'google_sub': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', '')
            }
        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
            raise ValueError(f"Invalid token: {e}")

    def get_or_create_user(self, db: Session, user_info: Dict[str, Any]) -> User:
        """Get existing user or create new one"""
        # Try to find existing user
        user = db.query(User).filter(User.google_sub == user_info['google_sub']).first()

        if user:
            # Update email in case it changed
            user.email = user_info['email']
            db.commit()
            db.refresh(user)
            return user

        # Create new user
        user = User(
            google_sub=user_info['google_sub'],
            email=user_info['email']
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Created new user: {user.email}")
        return user

    def create_session_data(self, user: User) -> Dict[str, Any]:
        """Create session data for user"""
        return {
            'user_id': user.id,
            'google_sub': user.google_sub,
            'email': user.email
        }

    def get_user_from_session(self, db: Session, session_data: Dict[str, Any]) -> User:
        """Get user from session data"""
        if not session_data or 'user_id' not in session_data:
            return None

        return db.query(User).filter(User.id == session_data['user_id']).first()