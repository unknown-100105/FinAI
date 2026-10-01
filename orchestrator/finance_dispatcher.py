from finance_engine.emi_service import EMIService
from finance_engine.sip_service import SIPService
from finance_engine.interest_service import InterestService


class FinanceDispatcher:

    def __init__(self):

        self.emi_service = EMIService()
        self.sip_service = SIPService()
        self.interest_service = InterestService()

    def dispatch(
        self,
        intent: str,
        user_text: str,
    ):

        # ---------------------------------------------------------
        # EMI
        # ---------------------------------------------------------

        if intent == "EMI_QUERY":

            return {
                "handled": True,
                "operation": "EMI_CALCULATION",
                "result": self.emi_service.process(
                    user_text
                ),
            }

        # ---------------------------------------------------------
        # Compound interest
        #
        # INTEREST_QUERY is currently the available trained
        # intent in the 50-intent taxonomy for this path.
        # ---------------------------------------------------------

        if intent == "INTEREST_QUERY":

            return {
                "handled": True,
                "operation": "COMPOUND_INTEREST_CALCULATION",
                "result": self.interest_service.process(
                    user_text
                ),
            }

        # ---------------------------------------------------------
        # SIP service exists, but SIP_QUERY is not currently one
        # of the trained 50 router intents.
        # ---------------------------------------------------------

        return {
            "handled": False,
            "operation": None,
            "result": None,
        }


if __name__ == "__main__":

    dispatcher = FinanceDispatcher()

    tests = [
        (
            "EMI_QUERY",
            "Calculate EMI for ₹10 lakh at 8.5% for 20 years",
        ),
        (
            "INTEREST_QUERY",
            "Calculate compound interest on ₹1 lakh at 8% for 5 years monthly",
        ),
        (
            "INTEREST_QUERY",
            "Calculate compound interest",
        ),
        (
            "ACCOUNT_BALANCE",
            "How much is my account balance?",
        ),
    ]

    print("=" * 80)
    print("FinAI FINANCE DISPATCHER TEST")
    print("=" * 80)

    for intent, text in tests:

        print()
        print("INTENT:", intent)
        print("USER:", text)

        result = dispatcher.dispatch(
            intent=intent,
            user_text=text,
        )

        print("HANDLED:", result["handled"])
        print("OPERATION:", result["operation"])
        print("RESULT:", result["result"])
