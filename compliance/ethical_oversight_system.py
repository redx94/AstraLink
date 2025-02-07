# Ethical Oversight System for AstraLink

class EthicalOversight:
    def __init__(self, governance_protocols):
        self.governance_protocols = governance_protocols
        self.review = []

    def apply_protocols(self):
        for protocol in self.governance_protocols:
            if hasattr(protocol, 'check_compliance') and hasattr(protocol, 'name'):
                result = protocol.check_compliance()
                self.review.append({
                    "protocol": protocol.name,
                    "result": result
                })
            else:
                self.review.append({
                    "protocol": getattr(protocol, 'name', 'Unknown'),
                    "result": "Invalid protocol"
                })

    def get_report(self):
        return self.review

# Mock Protocol class for demonstration purposes
class Protocol:
    def __init__(self, name):
        self.name = name

    def check_compliance(self):
        # Placeholder for actual compliance check logic
        return "Compliant"

# Test instance
govprotocols = [Protocol("model diversity"), Protocol("privacy mandates")]
osystem = EthicalOversight(govprotocols)
osystem.apply_protocols()
print(osystem.get_report())
