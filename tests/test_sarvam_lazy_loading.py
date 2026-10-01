from llm.response_service import ResponseService


def test_sarvam_is_not_registered_in_production_gateway():

    service = ResponseService()

    try:
        service.gateway.get_adapter("sarvam-1")
    except ValueError:
        return

    raise AssertionError(
        "Sarvam must remain disabled in the production response path."
    )
