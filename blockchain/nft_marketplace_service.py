"""
AstraLink - NFT Marketplace Service
================================

Handles secure trading of eSIM NFTs with quantum verification
and benefits transfer.
"""

from typing import Dict, Any, List, Optional
from web3 import Web3
from quantum.quantum_interface import QuantumSystem
from logging_config import get_logger
import asyncio
import time
from decimal import Decimal

logger = get_logger(__name__)

class NFTMarketplaceService:
    def __init__(self, contract_manager, quantum_system):
        self.contract_manager = contract_manager
        self.quantum_system = quantum_system
        self.web3 = Web3()
        self.active_listings = {}
        self.market_analytics = {}

    async def list_esim_for_sale(
        self,
        token_id: int,
        price: int,
        seller_address: str,
        listing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List an eSIM NFT for sale with quantum verification"""
        try:
            # Verify ownership and active status
            await self._verify_ownership(token_id, seller_address)
            
            # Generate quantum listing proof
            listing_proof = await self._generate_listing_proof(
                token_id,
                price,
                seller_address
            )
            
            # Create listing with smart contract
            tx = await self.contract_manager.create_listing(
                token_id=token_id,
                price=price,
                seller=seller_address,
                quantum_proof=listing_proof['signature'],
                config=listing_config
            )
            
            # Add to active listings
            self.active_listings[token_id] = {
                'price': price,
                'seller': seller_address,
                'timestamp': int(time.time()),
                'quantum_proof': listing_proof,
                'transaction_hash': tx['hash']
            }
            
            # Update market analytics
            await self._update_market_analytics(token_id, price, 'list')
            
            return {
                'listing_id': token_id,
                'status': 'active',
                'transaction_hash': tx['hash'],
                'quantum_verification': listing_proof['verification']
            }

        except Exception as e:
            logger.error(f"Failed to list eSIM: {str(e)}")
            raise

    async def purchase_esim(
        self,
        token_id: int,
        buyer_address: str,
        payment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Purchase a listed eSIM NFT with secure benefit transfer"""
        try:
            # Verify listing exists and is active
            listing = await self._verify_listing(token_id)
            
            # Verify buyer has sufficient funds
            await self._verify_funds(buyer_address, listing['price'])
            
            # Generate quantum purchase proof
            purchase_proof = await self._generate_purchase_proof(
                token_id,
                buyer_address,
                payment_info
            )
            
            # Process payment with quantum security
            payment_result = await self._process_secure_payment(
                listing,
                buyer_address,
                purchase_proof,
                payment_info
            )
            
            # Transfer NFT and benefits
            transfer_result = await self._transfer_esim_with_benefits(
                token_id,
                listing['seller'],
                buyer_address,
                purchase_proof
            )
            
            # Update market analytics
            await self._update_market_analytics(token_id, listing['price'], 'purchase')
            
            # Remove from active listings
            del self.active_listings[token_id]
            
            return {
                'status': 'completed',
                'transaction_hash': transfer_result['hash'],
                'payment_confirmation': payment_result['confirmation'],
                'quantum_verification': purchase_proof['verification']
            }

        except Exception as e:
            logger.error(f"Failed to purchase eSIM: {str(e)}")
            raise

    async def update_listing_price(
        self,
        token_id: int,
        new_price: int,
        seller_address: str
    ) -> Dict[str, Any]:
        """Update price of listed eSIM with quantum verification"""
        try:
            # Verify listing ownership
            listing = await self._verify_listing_ownership(token_id, seller_address)
            
            # Generate price update proof
            update_proof = await self._generate_price_update_proof(
                token_id,
                new_price,
                seller_address
            )
            
            # Update price in smart contract
            tx = await self.contract_manager.update_listing_price(
                token_id=token_id,
                new_price=new_price,
                quantum_proof=update_proof['signature']
            )
            
            # Update active listing
            self.active_listings[token_id]['price'] = new_price
            self.active_listings[token_id]['update_proof'] = update_proof
            
            # Update market analytics
            await self._update_market_analytics(token_id, new_price, 'update')
            
            return {
                'status': 'updated',
                'transaction_hash': tx['hash'],
                'quantum_verification': update_proof['verification']
            }

        except Exception as e:
            logger.error(f"Failed to update listing price: {str(e)}")
            raise

    async def cancel_listing(
        self,
        token_id: int,
        seller_address: str
    ) -> Dict[str, Any]:
        """Cancel eSIM listing with quantum verification"""
        try:
            # Verify listing ownership
            listing = await self._verify_listing_ownership(token_id, seller_address)
            
            # Generate cancellation proof
            cancel_proof = await self._generate_cancellation_proof(
                token_id,
                seller_address
            )
            
            # Cancel listing in smart contract
            tx = await self.contract_manager.cancel_listing(
                token_id=token_id,
                quantum_proof=cancel_proof['signature']
            )
            
            # Remove from active listings
            del self.active_listings[token_id]
            
            # Update market analytics
            await self._update_market_analytics(token_id, listing['price'], 'cancel')
            
            return {
                'status': 'cancelled',
                'transaction_hash': tx['hash'],
                'quantum_verification': cancel_proof['verification']
            }

        except Exception as e:
            logger.error(f"Failed to cancel listing: {str(e)}")
            raise

    async def get_market_analytics(
        self,
        token_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get market analytics with quantum-verified data"""
        try:
            if token_id:
                return await self._get_token_analytics(token_id)
            
            # Get global market analytics
            analytics = {
                'total_volume': sum(m['volume'] for m in self.market_analytics.values()),
                'active_listings': len(self.active_listings),
                'avg_price': self._calculate_average_price(),
                'price_history': await self._get_price_history(),
                'trading_velocity': self._calculate_trading_velocity(),
                'market_health': await self._calculate_market_health()
            }
            
            # Add quantum verification
            analytics['verification'] = await self._generate_analytics_proof(analytics)
            
            return analytics

        except Exception as e:
            logger.error(f"Failed to get market analytics: {str(e)}")
            raise

    async def _generate_listing_proof(
        self,
        token_id: int,
        price: int,
        seller_address: str
    ) -> Dict[str, Any]:
        """Generate quantum-secure proof for listing"""
        try:
            # Create listing data
            listing_data = {
                'token_id': token_id,
                'price': price,
                'seller': seller_address,
                'timestamp': int(time.time())
            }
            
            # Generate quantum signature
            signature = await self.quantum_system.sign_data(listing_data)
            
            # Generate verification data
            verification = await self.quantum_system.generate_verification_data(
                signature,
                listing_data
            )
            
            return {
                'signature': signature,
                'verification': verification,
                'timestamp': listing_data['timestamp']
            }

        except Exception as e:
            logger.error(f"Failed to generate listing proof: {str(e)}")
            raise

    async def _process_secure_payment(
        self,
        listing: Dict[str, Any],
        buyer_address: str,
        purchase_proof: Dict[str, Any],
        payment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment with quantum security"""
        try:
            # Create quantum-secure payment channel
            payment_channel = await self._create_payment_channel(
                listing['seller'],
                buyer_address,
                purchase_proof
            )
            
            # Calculate fees
            marketplace_fee = self._calculate_marketplace_fee(listing['price'])
            
            # Process payment with quantum verification
            payment_result = await self.contract_manager.process_payment(
                token_id=listing['token_id'],
                amount=listing['price'],
                buyer=buyer_address,
                seller=listing['seller'],
                marketplace_fee=marketplace_fee,
                quantum_proof=purchase_proof['signature'],
                payment_channel=payment_channel
            )
            
            return {
                'status': 'completed',
                'confirmation': payment_result['confirmation'],
                'quantum_verification': payment_result['verification']
            }

        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            raise

    async def _transfer_esim_with_benefits(
        self,
        token_id: int,
        seller_address: str,
        buyer_address: str,
        purchase_proof: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transfer eSIM NFT and associated benefits"""
        try:
            # Get current benefits
            benefits = await self.contract_manager.get_token_benefits(token_id)
            
            # Create quantum-secure transfer
            transfer = await self.contract_manager.transfer_token_with_benefits(
                token_id=token_id,
                from_address=seller_address,
                to_address=buyer_address,
                benefits=benefits,
                quantum_proof=purchase_proof['signature']
            )
            
            # Verify transfer success
            if not await self._verify_transfer_success(transfer['hash']):
                raise TransferError("Transfer verification failed")
            
            return transfer

        except Exception as e:
            logger.error(f"Benefits transfer failed: {str(e)}")
            raise

    def _calculate_marketplace_fee(self, price: int) -> int:
        """Calculate marketplace fee (2.5%)"""
        return int(Decimal(price) * Decimal('0.025'))