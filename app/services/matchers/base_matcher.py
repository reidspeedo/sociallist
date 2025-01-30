from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger("uvicorn")

class BaseMatcher:
    @staticmethod
    def match(text: str, keywords: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Basic keyword matching implementation that all services can use
        """
        text = text.lower()
        
        # Check excluded keywords first
        for excl in keywords.get("exclude_keywords", []):
            if excl.lower() in text:
                logger.debug(f"Text excluded due to keyword: {excl}")
                return False, ""

        # Check included keywords
        for keyword in keywords["keywords"]:
            if keyword.lower() in text:
                logger.debug(f"Found matching keyword: {keyword}")
                return True, keyword

        return False, "" 