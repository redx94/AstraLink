# Ethical Oversight System for AstraLink

class EthicalOversight:
    def __init__(self, governance_protocols):
        self.governance_protocols = governance_protocols
        self.review = []

    def apply_protocols(self):
        for protocol in self.governance_protocols:
            result = protocol.check_compliance()
            self.review.append({
                "protocol": protocol.name,
                "result": result})

    def get_report(self):
        return self.review

# Test instance
govprotocols = ["model diversity", "privacy mandates"]
osystem = EthicalOversight(govprotocols)
osystem.apply_protocols()
print(osystem.get_report())