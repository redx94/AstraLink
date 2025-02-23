from cellular.esim_manager import ESIMManager
from cellular.carrier_integration import CarrierIntegration
from ios.ios_integration import IOSIntegration
from payments.payment_processor import PaymentProcessor
from blockchain.nft_manager import NFTManager
import asyncio
import os

async def setup_cellular_data(payment_info: dict, user_address: str):
    # Initialize components
    esim = ESIMManager()
    carrier = CarrierIntegration()
    ios = IOSIntegration()
    payment_processor = PaymentProcessor(os.getenv('STRIPE_API_KEY'))
    nft_manager = NFTManager(
        os.getenv('NFT_CONTRACT_ADDRESS'),
        os.getenv('WEB3_PROVIDER')
    )

    try:
        # Process payment with revenue distribution
        payment_info['carrier_id'] = 'tmobile_connect'  # Add carrier ID for revenue sharing
        payment_result = await payment_processor.process_payment(
            amount=payment_info['amount'],
            currency=payment_info['currency'],
            payment_details=payment_info
        )

        # Verify revenue distribution
        if not payment_result.get('revenue_distribution', {}).get('success'):
            raise PaymentError("Revenue distribution failed")

        if not payment_result['success']:
            raise PaymentError("Payment failed")

        # Continue with eSIM setup
        device_info = ios.get_device_info()
        plans = await carrier.get_data_plans("t-mobile")
        
        # Purchase plan
        purchase_result = await carrier.purchase_plan(
            carrier="t-mobile",
            plan_id=payment_info['plan_id'],
            payment_info={'transaction_id': payment_result['transaction_id']}
        )

        # Download and activate eSIM profile
        profile = await esim.download_profile(
            purchase_result["iccid"],
            purchase_result["activation_code"]
        )

        # Activate the profile
        activation_result = await esim.activate_profile(profile["profile_id"])

        # Mint NFT for eSIM ownership
        nft_result = await nft_manager.mint_esim_nft(
            user_address,
            {
                'iccid': purchase_result['iccid'],
                'carrier': 't-mobile',
                'activation_date': activation_result['activation_date'],
                'plan_details': purchase_result['plan_details']
            }
        )

        return {
            'activation': activation_result,
            'payment': payment_result,
            'nft': nft_result,
            'revenue_distribution': payment_result['revenue_distribution']
        }

    except Exception as e:
        print(f"Error in setup process: {str(e)}")
        raise

async def get_platform_earnings(start_date: str, end_date: str) -> Dict:
    """Get platform earnings report"""
    payment_processor = PaymentProcessor(os.getenv('STRIPE_API_KEY'))
    return await payment_processor.get_earnings_report(start_date, end_date)

if __name__ == "__main__":
    payment_info = {
        'amount': 49.99,
        'currency': 'usd',
        'payment_method_id': 'pm_card_visa',
        'plan_id': 'UNLIMITED_5G'
    }
    user_eth_address = '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'
    asyncio.run(setup_cellular_data(payment_info, user_eth_address))
