import pytest
from backend.app.services.llm_provider import (
    get_llm_provider,
    GroqProvider,
    GeminiProvider,
    OpenAIProvider,
    MockLLMProvider,
)


@pytest.mark.asyncio
async def test_mock_llm_provider():
    provider = MockLLMProvider()
    response = await provider.generate_text("Draft an outreach cold email for Software Engineer")
    assert "FastAPI" in response or "Python" in response


@pytest.mark.asyncio
async def test_groq_provider_fallback_when_unconfigured():
    provider = GroqProvider(api_key="", model="llama-3.3-70b-versatile")
    response = await provider.generate_text("Draft an outreach cold email for AI Engineer")
    assert len(response) > 0
    assert "Python" in response or "FastAPI" in response


@pytest.mark.asyncio
async def test_get_llm_provider_factory():
    # Factory with groq
    groq_inst = get_llm_provider("groq")
    assert isinstance(groq_inst, GroqProvider)
    assert groq_inst.model == "llama-3.3-70b-versatile"

    # Factory with mock
    mock_inst = get_llm_provider("mock")
    assert isinstance(mock_inst, MockLLMProvider)

