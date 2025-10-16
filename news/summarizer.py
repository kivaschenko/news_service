import logging
from typing import Dict, Optional, Any
import torch

logger = logging.getLogger(__name__)

# Try to import transformers
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, summarization will be disabled")


class OpenSourceSummarizer:
    """Open-source text summarization using Hugging Face models"""

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initialize the summarizer with a specific model

        Args:
            model_name: HuggingFace model name for summarization
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.summarizer = None
        self._initialized = False

        if TRANSFORMERS_AVAILABLE:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize the model and tokenizer"""
        try:
            logger.info(f"Loading summarization model: {self.model_name}")

            # Use pipeline for easier handling
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
                torch_dtype=torch.float16
                if torch.cuda.is_available()
                else torch.float32,
            )

            self._initialized = True
            logger.info(f"Successfully loaded model: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            # Fallback to a smaller model
            try:
                logger.info(
                    "Falling back to smaller model: sshleifer/distilbart-cnn-12-6"
                )
                self.summarizer = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6",
                    device=-1,  # Use CPU for smaller model
                )
                self._initialized = True
                logger.info("Successfully loaded fallback model")
            except Exception as fallback_error:
                logger.error(f"Failed to load fallback model: {fallback_error}")
                self._initialized = False

    def summarize_text(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 50,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Summarize the given text

        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            language: Language of the text (for potential translation)

        Returns:
            Dictionary with summary and metadata
        """
        if not TRANSFORMERS_AVAILABLE or not self._initialized:
            return {
                "summary": "Summarization not available (model not loaded)",
                "status": "error",
                "model_used": "none",
            }

        try:
            # Prepare text for summarization
            # Limit input length to avoid token limits
            max_input_length = 1024  # Most models support this
            if len(text.split()) > max_input_length:
                # Take first and last parts to preserve context
                words = text.split()
                half_length = max_input_length // 2
                text = " ".join(words[:half_length] + ["..."] + words[-half_length:])

            # Generate summary
            logger.debug(f"Summarizing text of {len(text.split())} words")

            summary_result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True,
            )  # type: ignore

            summary = summary_result[0]["summary_text"]

            # If language is not English, we might want to add a note
            language_note = ""
            if language not in ["en", "unknown"]:
                language_note = f" (Оригінальна мова: {language})"

            return {
                "summary": summary + language_note,
                "status": "success",
                "model_used": self.model_name,
                "input_length": len(text.split()),
                "summary_length": len(summary.split()),
            }

        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            return {
                "summary": f"Помилка при створенні стислого опису: {str(e)}",
                "status": "error",
                "model_used": self.model_name,
            }

    def translate_and_summarize(
        self, text: str, source_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Translate text to Ukrainian and then summarize

        Args:
            text: Text to translate and summarize
            source_lang: Source language (auto-detect if 'auto')

        Returns:
            Dictionary with translated summary and metadata
        """
        try:
            # For now, we'll just summarize in the original language
            # and add a note about translation
            result = self.summarize_text(text, language=source_lang)

            if source_lang not in ["uk", "unknown"] and result["status"] == "success":
                # Add a note that this needs translation
                result["summary"] = f"[Потребує перекладу з {source_lang}] " + str(
                    result["summary"]
                )
                result["needs_translation"] = True
            else:
                result["needs_translation"] = False

            return result

        except Exception as e:
            logger.error(f"Error during translation and summarization: {e}")
            return {
                "summary": f"Помилка при перекладі та створенні стислого опису: {str(e)}",
                "status": "error",
                "model_used": self.model_name,
                "needs_translation": False,
            }


# Global summarizer instance
_global_summarizer = None


def get_summarizer() -> OpenSourceSummarizer:
    """Get or create global summarizer instance"""
    global _global_summarizer
    if _global_summarizer is None:
        _global_summarizer = OpenSourceSummarizer()
    return _global_summarizer


def summarize_article(text: str, language: str = "unknown") -> str:
    """
    Convenient function to summarize article text

    Args:
        text: Article text to summarize
        language: Language of the text

    Returns:
        Summary text
    """
    summarizer = get_summarizer()
    result = summarizer.summarize_text(text, language=language)

    if result["status"] == "success":
        return result["summary"]
    else:
        return "Не вдалося створити стислий опис статті"


def summarize_with_translation(text: str, source_lang: str = "auto") -> str:
    """
    Convenient function to translate and summarize article text

    Args:
        text: Article text to translate and summarize
        source_lang: Source language

    Returns:
        Translated summary text
    """
    summarizer = get_summarizer()
    result = summarizer.translate_and_summarize(text, source_lang)

    if result["status"] == "success":
        return result["summary"]
    else:
        return "Не вдалося створити стислий опис статті"
