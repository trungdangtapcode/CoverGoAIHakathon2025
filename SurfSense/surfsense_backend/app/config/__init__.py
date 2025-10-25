import os
import shutil
from pathlib import Path

# Heavy imports moved to lazy-loading properties to speed up module import during migrations
from dotenv import load_dotenv

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env_file = BASE_DIR / ".env"
load_dotenv(env_file)


def is_ffmpeg_installed():
    """
    Check if ffmpeg is installed on the current system.

    Returns:
        bool: True if ffmpeg is installed, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


class Config:
    # Check if ffmpeg is installed
    if not is_ffmpeg_installed():
        import static_ffmpeg

        # ffmpeg installed on first call to add_paths(), threadsafe.
        static_ffmpeg.add_paths()
        # check if ffmpeg is installed again
        if not is_ffmpeg_installed():
            raise ValueError(
                "FFmpeg is not installed on the system. Please install it to use the Surfsense Podcaster."
            )

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")

    NEXT_FRONTEND_URL = os.getenv("NEXT_FRONTEND_URL")

    # Auth
    AUTH_TYPE = os.getenv("AUTH_TYPE")
    REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "TRUE").upper() == "TRUE"

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    # Google Calendar redirect URI
    GOOGLE_CALENDAR_REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI")

    # Google Gmail redirect URI
    GOOGLE_GMAIL_REDIRECT_URI = os.getenv("GOOGLE_GMAIL_REDIRECT_URI")

    # Airtable OAuth
    AIRTABLE_CLIENT_ID = os.getenv("AIRTABLE_CLIENT_ID")
    AIRTABLE_CLIENT_SECRET = os.getenv("AIRTABLE_CLIENT_SECRET")
    AIRTABLE_REDIRECT_URI = os.getenv("AIRTABLE_REDIRECT_URI")

    # LLM instances are now managed per-user through the LLMConfig system
    # Legacy environment variables removed in favor of user-specific configurations

    # Chonkie Configuration | Edit this to your needs
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

    # Heavy ML models now lazy-loaded via properties to avoid loading during migrations
    _embedding_model_instance = None
    _chunker_instance = None
    _code_chunker_instance = None
    _reranker_instance = None

    # Reranker's Configuration | Pinecode, Cohere etc. Read more at https://github.com/AnswerDotAI/rerankers?tab=readme-ov-file#usage
    RERANKERS_MODEL_NAME = os.getenv("RERANKERS_MODEL_NAME")
    RERANKERS_MODEL_TYPE = os.getenv("RERANKERS_MODEL_TYPE")

    # OAuth JWT
    SECRET_KEY = os.getenv("SECRET_KEY")

    # ETL Service
    ETL_SERVICE = os.getenv("ETL_SERVICE")

    if ETL_SERVICE == "UNSTRUCTURED":
        # Unstructured API Key
        UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")

    elif ETL_SERVICE == "LLAMACLOUD":
        # LlamaCloud API Key
        LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

    # Firecrawl API Key
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", None)

    # Litellm TTS Configuration
    TTS_SERVICE = os.getenv("TTS_SERVICE")
    TTS_SERVICE_API_BASE = os.getenv("TTS_SERVICE_API_BASE")
    TTS_SERVICE_API_KEY = os.getenv("TTS_SERVICE_API_KEY")

    # STT Configuration
    STT_SERVICE = os.getenv("STT_SERVICE")
    STT_SERVICE_API_BASE = os.getenv("STT_SERVICE_API_BASE")
    STT_SERVICE_API_KEY = os.getenv("STT_SERVICE_API_KEY")

    # SMTP Email Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL")
    SMTP_SENDER_PASSWORD = os.getenv("SMTP_SENDER_PASSWORD")
    SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "SurfSense")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # Validation Checks moved to property accessors to avoid eager loading

    @classmethod
    def embedding_model_instance(cls):
        """Lazy-load embedding model only when needed."""
        if cls._embedding_model_instance is None:
            from chonkie import AutoEmbeddings
            cls._embedding_model_instance = AutoEmbeddings.get_embeddings(cls.EMBEDDING_MODEL)
            # Check embedding dimension
            if (
                hasattr(cls._embedding_model_instance, "dimension")
                and cls._embedding_model_instance.dimension > 2000
            ):
                raise ValueError(
                    f"Embedding dimension for Model: {cls.EMBEDDING_MODEL} "
                    f"has {cls._embedding_model_instance.dimension} dimensions, which "
                    f"exceeds the maximum of 2000 allowed by PGVector."
                )
        return cls._embedding_model_instance

    @classmethod
    def chunker_instance(cls):
        """Lazy-load chunker only when needed."""
        if cls._chunker_instance is None:
            from chonkie import RecursiveChunker
            embedding = cls.embedding_model_instance()
            cls._chunker_instance = RecursiveChunker(
                chunk_size=getattr(embedding, "max_seq_length", 512)
            )
        return cls._chunker_instance

    @classmethod
    def code_chunker_instance(cls):
        """Lazy-load code chunker only when needed."""
        if cls._code_chunker_instance is None:
            from chonkie import CodeChunker
            embedding = cls.embedding_model_instance()
            cls._code_chunker_instance = CodeChunker(
                chunk_size=getattr(embedding, "max_seq_length", 512)
            )
        return cls._code_chunker_instance

    @classmethod
    def reranker_instance(cls):
        """Lazy-load reranker only when needed."""
        if cls._reranker_instance is None:
            from rerankers import Reranker
            cls._reranker_instance = Reranker(
                model_name=cls.RERANKERS_MODEL_NAME,
                model_type=cls.RERANKERS_MODEL_TYPE,
            )
        return cls._reranker_instance

    @classmethod
    def get_settings(cls):
        """Get all settings as a dictionary."""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }


# Create a config instance
config = Config()
