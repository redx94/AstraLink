# Bandwidth Marketplace module for AstraLink

class BandwidthMarketplace:
    def __init__(self):
        self.registered_users = {}
        self.offers = []
        self.transactions = []

    def register_user(self, user_id, capacity):
        "" Add a user to the marketplace ""
        self.registered_users[user_id] = capacity
        return {"status": "available"}

    def list_offers(self):
        """ List current offers """
        return self.offers

    def make_offer(self, user_id, amount, capacity):
        """ Create a new bandwidth offer """
        offer = {
            "user_id": user_id,
            "amount": amount,
            "capacity": capacity,
            "status": "active"
        }
        self.offers.append(offer)
        return offer

    def complete_transaction(self, user_id, offer_id):
        """ Complete a bandwidth transaction """
        transaction = {
            "user_id": user_id,
            "offer_id": offer_id,
            "status": "completed"
        }
        self.transactions.append(transaction)
        return {"status": "success"}

marketplace = BandwidthMarketplace()
marketplace.register_user("user_123", 2500)
offer = marketplace.make_offer("user_123", 100, "msg")
print(offer)
transaction = marketplace.complete_transaction("user_123", offer["user_id"])
print(transaction)
