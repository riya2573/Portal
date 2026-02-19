import requests
import json
from typing import List
from config import OLLAMA_API_URL, OLLAMA_MODEL, SYSTEM_PROMPT, IMAGE_SEARCH_PROMPT, OLLAMA_TIMEOUT


class LLMService:
    def __init__(self):
        """Initialize LLM service"""
        self.api_url = OLLAMA_API_URL
        self.model = OLLAMA_MODEL
        self._verify_connection()

    def _verify_connection(self):
        """Verify Ollama is running"""
        try:
            response = requests.get(f"{self.api_url}/api/tags")
            if response.status_code == 200:
                print(f"[OK] Connected to Ollama at {self.api_url}")
                return True
            else:
                print(f"[ERROR] Ollama connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Cannot connect to Ollama: {str(e)}")
            print(f"  Make sure Ollama is running: ollama serve")
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

        return self._call_ollama(prompt)

    def detect_image_intent(self, question: str) -> bool:
        """
        Detect if user is asking for images

        Args:
            question: User question

        Returns:
            True if asking for images, False otherwise
        """
        prompt = IMAGE_SEARCH_PROMPT.format(question=question)

        response = self._call_ollama(prompt)
        return "SHOW_IMAGE" in response.upper()

    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API without streaming

        Args:
            prompt: Prompt to send

        Returns:
            Generated response
        """
        try:
            url = f"{self.api_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            }

            response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model may be slow or Ollama may be unresponsive."
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure it's running with 'ollama serve'"
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_answer_stream(self, context: str, question: str):
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
            url = f"{self.api_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "temperature": 0.7,
            }

            with requests.post(url, json=payload, stream=True, timeout=OLLAMA_TIMEOUT) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            yield "Error: Request timed out."
        except requests.exceptions.ConnectionError:
            yield "Error: Cannot connect to Ollama."
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

        return self._call_ollama(prompt)


# Global instance
llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
