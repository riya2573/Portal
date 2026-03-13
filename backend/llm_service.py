import os
from pathlib import Path
from typing import List, Generator
from llama_cpp import Llama
from config import (
    LLAMA_MODEL_PATH,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_CONTEXT_SIZE,
    LLM_GPU_LAYERS,
    SYSTEM_PROMPT,
    IMAGE_SEARCH_PROMPT,
)

# Model download settings
LLAMA_REPO_ID = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
LLAMA_FILENAME = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"


class LLMService:
    def __init__(self):
        """Initialize LLM service with direct llama-cpp-python execution"""
        self.model_path = Path(LLAMA_MODEL_PATH)
        self.temperature = LLM_TEMPERATURE
        self.max_tokens = LLM_MAX_TOKENS
        self._model = None  # Lazy-loaded

    def _download_model(self):
        """Download the GGUF model from HuggingFace if not present"""
        if self.model_path.exists():
            return

        print(f"[INFO] Model not found: {self.model_path}")
        print(f"[INFO] Downloading from HuggingFace ({LLAMA_REPO_ID})...")
        print(f"       This will download ~4.6GB. Please wait...")

        try:
            from huggingface_hub import hf_hub_download

            # Ensure models directory exists
            self.model_path.parent.mkdir(parents=True, exist_ok=True)

            # Download model
            hf_hub_download(
                repo_id=LLAMA_REPO_ID,
                filename=LLAMA_FILENAME,
                local_dir=str(self.model_path.parent),
            )
            print(f"[OK] Model downloaded successfully")

        except Exception as e:
            print(f"[ERROR] Failed to download model: {e}")
            print(f"")
            print(f"Please download manually:")
            print(f"  python -c \"")
            print(f"  from huggingface_hub import hf_hub_download")
            print(f"  hf_hub_download(")
            print(f"      repo_id='{LLAMA_REPO_ID}',")
            print(f"      filename='{LLAMA_FILENAME}',")
            print(f"      local_dir='./models'")
            print(f"  )\"")
            raise

    def _load_model(self) -> Llama:
        """Lazy-load the LLM model (downloads if missing)"""
        if self._model is None:
            # Auto-download if missing
            self._download_model()

            print(f"[INFO] Loading LLM model: {self.model_path}")
            print(f"       This may take a minute...")

            try:
                self._model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=LLM_CONTEXT_SIZE,
                    n_gpu_layers=LLM_GPU_LAYERS,
                    verbose=False,
                )
                print(f"[OK] LLM model loaded successfully")
            except Exception as e:
                print(f"[ERROR] Failed to load LLM model: {e}")
                raise

        return self._model

    def _verify_connection(self) -> bool:
        """Check if model can be loaded (for health check compatibility)"""
        try:
            self._load_model()
            return True
        except Exception:
            return False

    def generate_answer(self, context: str, question: str) -> str:
        """
        Generate answer using LLM with retrieved context

        Args:
            context: Retrieved document context
            question: User question

        Returns:
            Generated answer
        """
        prompt = SYSTEM_PROMPT.format(context=context, question=question)
        return self._call_llm(prompt)

    def detect_image_intent(self, question: str) -> bool:
        """
        Detect if user is asking for images

        Args:
            question: User question

        Returns:
            True if asking for images, False otherwise
        """
        prompt = IMAGE_SEARCH_PROMPT.format(question=question)
        response = self._call_llm(prompt)
        return "SHOW_IMAGE" in response.upper()

    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM directly using llama-cpp-python

        Args:
            prompt: Prompt to send

        Returns:
            Generated response
        """
        try:
            model = self._load_model()

            response = model.create_chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "").strip()
            return ""

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_answer_stream(self, context: str, question: str) -> Generator[str, None, None]:
        """
        Generate answer using LLM with streaming response

        Args:
            context: Retrieved document context
            question: User question

        Yields:
            Token strings as they are generated
        """
        prompt = SYSTEM_PROMPT.format(context=context, question=question)

        try:
            model = self._load_model()

            stream = model.create_chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

            for chunk in stream:
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content

                    finish_reason = choices[0].get("finish_reason")
                    if finish_reason:
                        break

        except Exception as e:
            yield f"Error: {str(e)}"

    def summarize_documents(self, documents: List[str], topic: str) -> str:
        """
        Summarize multiple documents on a topic

        Args:
            documents: List of document texts
            topic: Topic to summarize

        Returns:
            Summary
        """
        combined = "\n\n".join([f"Document: {doc}" for doc in documents])
        prompt = f"""Summarize the following documents about {topic} in a clear, concise way:

{combined}

Summary:"""

        return self._call_llm(prompt)


# Global instance
llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
