import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class Judge0LanguageRegistry:
    """Lifespan cache that resolves standard language strings to Judge0 language IDs and versions."""

    # Fallback/canonical map in case Judge0 is offline during startup
    _cache: dict[str, int] = {
        "python": 71,       # Python (3.8.1)
        "cpp": 54,          # C++ (GCC 9.2.0)
        "java": 62,         # Java (OpenJDK 13.0.1)
        "javascript": 63,   # JavaScript (Node.js 12.14.0)
    }

    _versions: dict[str, str] = {
        "python": "3.8.1",
        "cpp": "GCC 9.2.0",
        "java": "OpenJDK 13.0.1",
        "javascript": "Node.js 12.14.0"
    }

    @classmethod
    async def initialize(cls) -> None:
        """Fetches dynamic language configurations from Judge0, caching names and version IDs."""
        url = f"{settings.JUDGE0_URL.rstrip('/')}/languages"
        headers = {}
        if settings.JUDGE0_API_KEY:
            headers["X-Auth-Token"] = settings.JUDGE0_API_KEY
            # Also support standard RapidAPI key header if user uses RapidAPI
            headers["X-RapidAPI-Key"] = settings.JUDGE0_API_KEY

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    languages = response.json()
                    new_cache = {}
                    new_versions = {}
                    for lang in languages:
                        name_lower = lang["name"].lower()
                        lang_id = lang["id"]

                        if "python" in name_lower and ("3." in name_lower or "python 3" in name_lower):
                            # Prioritize Python 3
                            new_cache["python"] = lang_id
                            new_versions["python"] = lang["name"]
                        elif "c++" in name_lower or "gcc" in name_lower or "cpp" in name_lower:
                            # Prioritize C++ compilers
                            new_cache["cpp"] = lang_id
                            new_versions["cpp"] = lang["name"]
                        elif "java" in name_lower and "javascript" not in name_lower:
                            new_cache["java"] = lang_id
                            new_versions["java"] = lang["name"]
                        elif "javascript" in name_lower or "node" in name_lower:
                            new_cache["javascript"] = lang_id
                            new_versions["javascript"] = lang["name"]

                    if new_cache:
                        cls._cache.update(new_cache)
                        cls._versions.update(new_versions)
                        logger.info(f"Initialized Judge0 Language Registry: {cls._cache}")
                else:
                    logger.warning(f"Judge0 returned status {response.status_code} during startup language initialization. Using fallback registry.")
        except Exception as e:
            logger.warning(f"Could not connect to Judge0 at {url} on startup ({e}). Running on offline fallback registry.")

    @classmethod
    def get_id(cls, language: str) -> int:
        lang_key = language.lower()
        if lang_key not in cls._cache:
            raise ValueError(f"Language '{language}' is not supported by the execution registry.")
        return cls._cache[lang_key]

    @classmethod
    def get_version(cls, language: str) -> str:
        lang_key = language.lower()
        return cls._versions.get(lang_key, "unknown")
