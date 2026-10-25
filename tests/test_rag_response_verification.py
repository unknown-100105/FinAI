from llm.model_gateway import ModelGateway
from llm.response_service import ResponseService


class FixedAdapter:
    def __init__(self, response):
        self.response = response

    def generate(self, **kwargs):
        return {
            "status": "GENERATED",
            "model_id": "gemini-cloud",
            "source": kwargs["source"],
            "language": kwargs["language"],
            "persona": kwargs["persona"],
            "response": self.response,
            "metrics": {},
        }


def make_service(response):
    gateway = ModelGateway(default_model="gemini-cloud")
    gateway.register(
        "gemini-cloud",
        FixedAdapter(response),
        capabilities=["response_generation"],
    )
    return ResponseService(gateway=gateway)


def evidence():
    return {
        "query": "What documents are required for KYC?",
        "evidence_count": 1,
        "documents": [
            {
                "document_id": 1,
                "title": "KYC requirements",
                "source": "test",
                "date": "2025-01-01",
                "text": (
                    "KYC may require PAN card, address proof, photograph, "
                    "cancelled cheque, and signatures."
                ),
            }
        ],
    }


def test_response_service_applies_rag_evidence_verification(monkeypatch):
    # This test uses a fixed adapter; a dummy credential satisfies the router's
    # provider-configuration check without making a real API request.
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-not-a-real-key")
    service = make_service(
        (
            "KYC may require a PAN card and address proof. "
            "A photograph and cancelled cheque may also be required."
        )
    )

    result = service.generate(
        user_text="What documents are required for KYC?",
        intent="KYC_DOCUMENTS",
        verified_result=evidence(),
        source="retrieval_evidence",
        model_id="gemini-cloud",
    )

    assert result["status"] == "GENERATED_VERIFIED"
    assert result["verification"]["applicable"] is True
    assert result["verification"]["mode"] == "EVIDENCE_SUPPORT"
    assert result["verification"]["passed"] is True
    assert len(result["verification"]["supported_claims"]) == 2


def test_response_service_rejects_unsupported_rag_claim():
    service = make_service(
        (
            "KYC may require a PAN card. "
            "KYC guarantees approval of every loan application."
        )
    )

    result = service._verify_response(
        response=(
            "KYC may require a PAN card. "
            "KYC guarantees approval of every loan application."
        ),
        intent="KYC_DOCUMENTS",
        verified_result=evidence(),
        source="retrieval_evidence",
    )

    assert result["applicable"] is True
    assert result["mode"] == "EVIDENCE_SUPPORT"
    assert result["passed"] is False
    assert result["unsupported_claims"]


def test_deterministic_emi_verification_remains_separate():
    service = make_service("irrelevant")

    result = service._verify_response(
        response=(
            "Your monthly EMI is ₹8,678.23. "
            "Total payment is ₹2,082,775.76. "
            "Total interest is ₹1,082,775.76."
        ),
        intent="EMI_QUERY",
        verified_result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
    )

    assert result["applicable"] is True
    assert result["passed"] is True
