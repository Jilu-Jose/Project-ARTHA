"""
ARTHA LLM Integration — NVIDIA NIM + Kimi K2.6
================================================
Direct calls to NVIDIA NIM's OpenAI-compatible API using the Kimi K2.6
long-context model (256K tokens).

Architecture choice:
- Uses the `openai` Python SDK pointed at NVIDIA's base URL
- NO LangChain, NO LangGraph — direct SDK calls only
- This demonstrates understanding of retrieval mechanics rather
  than framework fluency
- Streaming support for real-time chat UX
- Retry logic with exponential backoff for production resilience

The system prompt enforces:
- Answer ONLY from provided context (no hallucinated provisions)
- Cite every claim as [Section X, Act Name]
- Explicit acknowledgment when context is insufficient
- Legal disclaimer appended to every response
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are ARTHA (Advisory for Regulatory and Tax-related Holistic Advisories), a legal intelligence assistant for Indian startup founders.

## Your Role
You help first-time founders, early-stage startups, and indie hackers navigate Indian regulatory and compliance requirements. You provide clear, accurate, and well-cited answers grounded exclusively in the legal document excerpts provided to you.

## Rules (STRICTLY FOLLOW)
1. **Answer ONLY from the provided legal document excerpts.** Do NOT use general knowledge or training data for legal claims.
2. **Cite every legal claim** using the format [Section X, Act Name]. Example: [Section 22, CGST Act, 2017].
3. **If the provided context does not contain sufficient information** to answer the question, say so explicitly: "The provided legal excerpts do not contain sufficient information to fully answer this question. Please consult a qualified legal professional."
4. **Never invent, extrapolate, or assume statutory provisions** that are not explicitly stated in the provided context.
5. **Use plain language** that a non-lawyer founder can understand, while maintaining legal accuracy.
6. **Clean Formatting:** Structure your answers with clear headings and standard numbered lists (e.g., 1., 2., 3.). Do NOT use asterisks (*) for bullet points or excessive Markdown bolding (**), as it makes the output look chaotic. Keep the text clean.
7. **When comparing options** (e.g., Pvt Ltd vs LLP), create a clear comparison highlighting the key differences without using excessive special characters.
8. **Always append this disclaimer** at the end of every response:

---
⚖️ *Disclaimer: This is legal information derived from statutory sources, not legal advice. For decisions specific to your situation, please consult a qualified Company Secretary (CS), Chartered Accountant (CA), or lawyer.*
"""


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------

class ARTHALLMClient:
    """
    Async LLM client for NVIDIA NIM + Kimi K2.6.

    Uses the OpenAI-compatible SDK pointed at NVIDIA's API endpoint.
    Supports both streaming and non-streaming completions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.base_url = base_url or settings.NVIDIA_BASE_URL
        self.model = model or settings.NVIDIA_MODEL

        if not self.api_key:
            logger.warning(
                "NVIDIA_API_KEY not set. LLM calls will fail. "
                "Get your key at https://build.nvidia.com/settings/api-keys"
            )

        # Initialize AsyncOpenAI client pointed at NVIDIA NIM
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        logger.info(
            f"ARTHA LLM client initialized: model={self.model}, "
            f"base_url={self.base_url}"
        )

    async def generate(
        self,
        query: str,
        context: str,
        conversation_history: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a non-streaming response.

        Args:
            query: User's question
            context: Retrieved legal context from BM25
            conversation_history: Optional previous conversation
            temperature: Override LLM temperature
            max_tokens: Override max output tokens

        Returns:
            Complete response string
        """
        messages = self._build_messages(query, context, conversation_history)

        response = await self._call_with_retry(
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.MAX_OUTPUT_TOKENS,
            stream=False,
        )

        return response.choices[0].message.content

    async def generate_stream(
        self,
        query: str,
        context: str,
        conversation_history: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response for real-time chat UX.

        Yields content chunks as they arrive from NVIDIA NIM.

        Args:
            query: User's question
            context: Retrieved legal context from BM25
            conversation_history: Optional previous conversation
            temperature: Override LLM temperature
            max_tokens: Override max output tokens

        Yields:
            Content string chunks
        """
        messages = self._build_messages(query, context, conversation_history)

        stream = await self._call_with_retry(
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.MAX_OUTPUT_TOKENS,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _build_messages(
        self,
        query: str,
        context: str,
        conversation_history: Optional[str] = None,
    ) -> list:
        """Build the message list for the LLM call."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        # Include conversation history if available
        if conversation_history:
            messages.append({
                "role": "user",
                "content": f"Previous conversation for context:\n{conversation_history}",
            })
            messages.append({
                "role": "assistant",
                "content": "I understand the conversation context. I'll consider it when answering your next question.",
            })

        # Main query with retrieved context
        user_message = (
            f"Context from Indian legal documents:\n\n"
            f"{context}\n\n"
            f"---\n\n"
            f"Founder's question: {query}"
        )
        messages.append({"role": "user", "content": user_message})

        return messages

    async def _call_with_retry(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        stream: bool,
        max_retries: int = 3,
    ):
        """
        Call the NVIDIA NIM API with exponential backoff retry logic.

        Retries on transient errors (rate limiting, server errors).
        Does NOT retry on authentication errors (wrong API key).
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
                return response

            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Don't retry on auth errors
                if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
                    logger.error(f"Authentication error (not retrying): {e}")
                    raise

                # Exponential backoff for transient errors
                wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s
                logger.warning(
                    f"LLM call attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

        logger.error(f"LLM call failed after {max_retries} retries: {last_exception}")
        raise last_exception

    async def health_check(self) -> bool:
        """Check if the NVIDIA NIM API is reachable."""
        try:
            # Make a minimal call to verify connectivity
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                stream=False,
            )
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False


# ---------------------------------------------------------------------------
# Module-level client (lazy initialization)
# ---------------------------------------------------------------------------
_llm_client: Optional[ARTHALLMClient] = None


def get_llm_client() -> ARTHALLMClient:
    """Get or create the singleton LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = ARTHALLMClient()
    return _llm_client
