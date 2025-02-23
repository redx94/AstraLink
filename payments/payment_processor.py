import stripe
from typing import Dict
import asyncio
from datetime import datetime
from payments.revenue_manager import RevenueManager
from decimal import Decimal

class PaymentProcessor:
    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.supported_methods = ['card', 'apple_pay', 'google_pay']
        self.revenue_manager = RevenueManager(api_key)

    async def process_payment(self, amount: float, currency: str, payment_details: Dict) -> Dict:
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                payment_method_types=self.supported_methods,
                metadata={
                    'service': 'esim_activation',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            # Confirm payment
            confirmation = stripe.PaymentIntent.confirm(
                intent.id,
                payment_method=payment_details['payment_method_id']
            )

            # Process revenue distribution
            distribution = await self.revenue_manager.process_revenue_distribution(
                payment_amount=Decimal(str(amount)),
                carrier_id=payment_details.get('carrier_id'),
                transaction_id=confirmation.id
            )

            return {
                'success': True,
                'transaction_id': confirmation.id,
                'amount': amount,
                'currency': currency,
                'status': confirmation.status,
                'revenue_distribution': distribution
            }

        except stripe.error.StripeError as e:
            raise PaymentError(f"Payment failed: {str(e)}")

    async def create_subscription(self, customer_id: str, plan_id: str) -> Dict:
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': plan_id}],
                payment_behavior='default_incomplete'
            )
            
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end
            }
        except stripe.error.StripeError as e:
            raise PaymentError(f"Subscription creation failed: {str(e)}")

    async def get_earnings_report(self, start_date: str, end_date: str) -> Dict:
        """Get earnings report for technology usage"""
        return await self.revenue_manager.get_revenue_report(start_date, end_date)
