import stripe
import time
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.database import User

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self, settings):
        self.settings = settings
        stripe.api_key = settings.stripe_secret_key

        # In-memory credit cache with TTL (as per DESIGN.md)
        self.credit_cache = {}  # {user_id: (credits, expires_at)}
        self.cache_ttl = 300  # 5 minutes

    async def get_or_create_customer(self, user: User) -> str:
        """Get or create Stripe customer for user"""
        if user.stripe_customer_id:
            return user.stripe_customer_id

        try:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    'user_id': str(user.id),
                    'google_sub': user.google_sub,
                    'credits': '0',
                    'lifetime_spend': '0'
                }
            )

            # Update user record
            user.stripe_customer_id = customer.id
            # Note: Caller should commit this change

            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    async def get_user_credits(self, user_id: int, db: Session) -> int:
        """Get user credits with caching (as per DESIGN.md)"""
        # Check cache first
        if user_id in self.credit_cache:
            credits, expires = self.credit_cache[user_id]
            if time.time() < expires:
                return credits

        # Fetch from Stripe as source of truth
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            return 0

        try:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            credits = int(customer.metadata.get('credits', 0))

            # Cache for 5 minutes
            self.credit_cache[user_id] = (credits, time.time() + self.cache_ttl)
            return credits

        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch credits from Stripe: {e}")
            return 0

    async def get_lifetime_spend(self, user_id: int, db: Session) -> float:
        """Get user lifetime spend from Stripe metadata"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            return 0.0

        try:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            return float(customer.metadata.get('lifetime_spend', 0))

        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch lifetime spend from Stripe: {e}")
            return 0.0

    async def deduct_credits(self, user_id: int, amount: int, db: Session) -> bool:
        """Deduct credits from user account"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            return False

        try:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            current_credits = int(customer.metadata.get('credits', 0))

            if current_credits < amount:
                return False

            # Update Stripe metadata
            new_credits = current_credits - amount
            stripe.Customer.modify(
                user.stripe_customer_id,
                metadata={
                    **customer.metadata,
                    'credits': str(new_credits)
                }
            )

            # Clear cache
            if user_id in self.credit_cache:
                del self.credit_cache[user_id]

            logger.info(f"Deducted {amount} credits from user {user_id}, remaining: {new_credits}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to deduct credits: {e}")
            return False

    async def add_credits(self, user_id: int, amount: int, db: Session) -> bool:
        """Add credits to user account"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.stripe_customer_id:
            return False

        try:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            current_credits = int(customer.metadata.get('credits', 0))

            # Update Stripe metadata
            new_credits = current_credits + amount
            stripe.Customer.modify(
                user.stripe_customer_id,
                metadata={
                    **customer.metadata,
                    'credits': str(new_credits)
                }
            )

            # Clear cache
            if user_id in self.credit_cache:
                del self.credit_cache[user_id]

            logger.info(f"Added {amount} credits to user {user_id}, total: {new_credits}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to add credits: {e}")
            return False

    async def create_checkout_session(self,
                                    user_id: int,
                                    product_type: str,
                                    amount: Optional[int] = None) -> str:
        """Create Stripe checkout session"""
        try:
            # Define product configurations
            products = {
                'credits_100': {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 2500,  # $25.00
                        'product_data': {'name': '100 Credits'}
                    },
                    'quantity': 1,
                    'metadata': {'credits': '100'}
                },
                'credits_500': {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 10000,  # $100.00
                        'product_data': {'name': '500 Credits'}
                    },
                    'quantity': 1,
                    'metadata': {'credits': '500'}
                },
                'library': {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 5000,  # $50.00
                        'product_data': {'name': 'Full Library License'}
                    },
                    'quantity': 1,
                    'metadata': {'library_license': 'true'}
                }
            }

            if product_type not in products:
                raise ValueError(f"Unknown product type: {product_type}")

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[products[product_type]],
                mode='payment',
                success_url='http://localhost:8000/success',
                cancel_url='http://localhost:8000/cancel',
                metadata={
                    'user_id': str(user_id),
                    'product_type': product_type
                }
            )

            return session.url

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    async def create_billing_portal_session(self, customer_id: str) -> str:
        """Create Stripe billing portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url='http://localhost:8000/account'
            )
            return session.url

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise

    async def process_webhook_event(self, event: Dict[str, Any], db: Session) -> bool:
        """Process Stripe webhook event"""
        try:
            event_type = event['type']

            if event_type == 'checkout.session.completed':
                await self._handle_checkout_completed(event['data']['object'], db)

            elif event_type == 'customer.subscription.updated':
                await self._handle_subscription_updated(event['data']['object'], db)

            elif event_type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event['data']['object'], db)

            return True

        except Exception as e:
            logger.error(f"Failed to process webhook event: {e}")
            return False

    async def _handle_checkout_completed(self, session: Dict[str, Any], db: Session):
        """Handle completed checkout session"""
        user_id = int(session['metadata']['user_id'])
        product_type = session['metadata']['product_type']

        if 'credits' in product_type:
            # Extract credit amount from product metadata
            line_items = stripe.checkout.Session.list_line_items(session['id'])
            for item in line_items.data:
                metadata = item.price.metadata
                if 'credits' in metadata:
                    credits = int(metadata['credits'])
                    await self.add_credits(user_id, credits, db)
                    break

        elif product_type == 'library':
            # Grant library license
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.stripe_customer_id:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
                stripe.Customer.modify(
                    user.stripe_customer_id,
                    metadata={
                        **customer.metadata,
                        'library_license': 'true'
                    }
                )

    async def _handle_subscription_updated(self, subscription: Dict[str, Any], db: Session):
        """Handle subscription updates (for pro plans)"""
        # TODO: Implement pro plan logic if needed
        pass

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any], db: Session):
        """Handle subscription cancellation"""
        # TODO: Implement pro plan logic if needed
        pass