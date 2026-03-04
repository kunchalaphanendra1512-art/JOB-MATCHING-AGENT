import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# runtime flags and client cache
_key_valid = True
_genai_client = None


def _ensure_client() -> Optional[object]:
    """Lazily import and configure the Gemini client. Returns None if unavailable.
    This avoids importing heavy/remote clients at module import time which can
    slow startup or raise when keys are missing.
    """
    global _genai_client, _key_valid
    if _genai_client is not None or not _key_valid:
        return _genai_client

    if not GEMINI_API_KEY:
        print("⚠ GEMINI_API_KEY missing; embedding service disabled.")
        _key_valid = False
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _genai_client = genai
        return _genai_client
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
        _key_valid = False
        return None


class EmbeddingService:
    @staticmethod
    def get_embedding(text: str, model: str = "models/embedding-001"):
        """Return an embedding vector for `text` or a zero-vector fallback.

        The function avoids network calls when keys are missing or previously
        marked invalid. It also lazy-loads the heavy Gemini client to speed
        up application startup.
        """
        global _key_valid
        if not text or not text.strip():
            return []

        if not _key_valid:
            print("Skipping embedding call: API key previously marked invalid")
            return [0.0] * 768

        client = _ensure_client()
        if client is None:
            return [0.0] * 768

        try:
            # note: newer versions of the Gemini client no longer accept a
            # `timeout` keyword on embed_content, so we call with the minimal
            # arguments supported.
            result = client.embed_content(
                model=model,
                content=text,
                task_type="retrieval_document",
            )
            return result.get("embedding", [])
        except Exception as e:
            msg = str(e)
            print(f"Gemini Embedding Error: {e}")
            if "API key not valid" in msg or "API_KEY_INVALID" in msg:
                _key_valid = False
                print("Disabling further embedding requests due to invalid API key")
            import traceback
            traceback.print_exc()
            return [0.0] * 768
