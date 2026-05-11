"""Infrastructure layer - AI implementations.
Concrete implementations of AI-related ports.
"""
from backend.src.domain.ports import AISummarizerPort
from backend.src.domain.exceptions import TranscriptionError
import os


try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiAISummarizer(AISummarizerPort):
    """Gemini-based AI summarizer implementation."""

    def __init__(self, model_name: str = "gemini"):
        self.model_name = model_name
        self._agent_cache = {}
        self._init_gemini()

    def _init_gemini(self):
        """Initialize Gemini client if available."""
        if not GEMINI_AVAILABLE:
            return
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
        except Exception:
            pass

    def _load_agent(self, mode: str):
        """Load agent implementation for mode."""
        prompts = {
            "default": "Eres un asistente experto. Resume el siguiente texto.",
            "tecnico": "Eres un analista técnico. Resume en aspectos técnicos.",
            "refinamiento": "Eres un analista de ingeniería. Extrae decisiones.",
            "ejecutivo": "Eres un ejecutivo. Extrae puntos clave de negocio.",
            "bullet": "Resume en viñetas concisas los puntos importantes.",
        }
        return prompts.get(mode, prompts["default"])

    def summarize(self, text: str, mode: str) -> str:
        """Summarize text using Gemini."""
        try:
            system_prompt = self._load_agent(mode)

            if GEMINI_AVAILABLE:
                try:
                    model = genai.GenerativeModel(self.model_name)
                    response = model.generate_content(f"{system_prompt}\n\nTexto:\n{text}")
                    return response.text
                except Exception:
                    pass

            # Fallback: simple extraction
            words = text.split()
            if len(words) > 100:
                return " ".join(words[:100]) + "..."
            return text
        except Exception as e:
            raise TranscriptionError(f"AI summarization failed: {str(e)}")

    def get_agent(self, mode: str):
        """Get a mock agent for the mode."""
        class MockAgent:
            def __init__(self, summarizer, mode):
                self.summarizer = summarizer
                self.mode = mode

            def run(self, message, stream=False):
                result = self.summarizer.summarize(message, self.mode)
                if stream:
                    for chunk in result.split(". "):
                        if chunk:
                            yield chunk + ". "
                return result

        if mode not in self._agent_cache:
            self._agent_cache[mode] = MockAgent(self, mode)
        return self._agent_cache[mode]


class GeminiModelAISummarizer(AISummarizerPort):
    """Direct Gemini model AI summarizer."""

    def __init__(self):
        self._agent_cache = {}
        self._init_gemini()

    def _init_gemini(self):
        if not GEMINI_AVAILABLE:
            self.agents = {}
            return
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("gemini")
            else:
                self.model = None
        except Exception:
            self.model = None

    def _get_agents(self):
        if not self._agent_cache:
            for mode in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
                self._agent_cache[mode] = GeminiAISummarizer().get_agent(mode)
            self._agent_cache["default"] = self._agent_cache["default"]
        return self._agent_cache

    def summarize(self, text: str, mode: str) -> str:
        try:
            agents = self._get_agents()
            agent = agents.get(mode, agents["default"])
            result = agent.run(message=text, stream=False)
            if hasattr(result, "text"):
                return result.text
            return str(result)
        except Exception as e:
            raise TranscriptionError(f"Gemini summarization failed: {str(e)}")

    def get_agent(self, mode: str):
        agents = self._get_agents()
        return agents.get(mode, agents["default"])
