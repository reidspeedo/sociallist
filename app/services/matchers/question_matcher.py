from typing import Tuple, Dict, Any
import re
import logging

logger = logging.getLogger("uvicorn")

class QuestionMatcher:
    @staticmethod
    def match(text: str, keywords: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Matches posts that are asking questions or seeking advice
        """
        question_patterns = [
            # Project/Building related
            r"(?i)what (are you|'?re you|have you been) (working on|building|developing|coding|creating)",
            r"(?i)share what you'?ve (been working on|built|developed|created)",
            r"(?i)show (off|us) your (project|side project|latest project|build)",
            r"(?i)what side project(s)? (are you|is everyone) working on",
            
            # Pain points/Problems
            r"(?i)(what('s| is) your|biggest|main) (pain point|struggle|roadblock|bottleneck)",
            r"(?i)(what('s| is)|biggest|main) (problem|issue|challenge|frustration) (you'?re facing|with your business|with your startup)?",
            r"(?i)what('s| is) holding you back",
            r"(?i)why did your (startup|project|idea) fail",
            r"(?i)what('s| is) stopping you from launching",
            
            # SaaS/Ideas related
            r"(?i)looking for (saas )?(ideas|opportunities|niches|markets)",
            r"(?i)need (an )?(idea|inspiration|side hustle idea)",
            r"(?i)need a (business|startup) idea",
            r"(?i)what('s| is) a good (saas|startup|side project) idea",
            r"(?i)brainstorm (saas|startup|app|product) ideas",
            r"(?i)help me come up with (an|a new) idea",
            r"(?i)anyone have (saas|startup|business) ideas",
            
            # Self-promotion/Showcase
            r"(?i)time for self[\-]promotion",
            r"(?i)showcase your (project|business|startup|side hustle)",
            r"(?i)post your (product|app|website|startup|SaaS)",
            r"(?i)plug your (work|project|startup|product|service)",
            r"(?i)promote your (business|startup|side hustle|SaaS|app)",
            r"(?i)tell me about your (startup|project|business|product)",
            r"(?i)what have you launched",
            
            # Startup Growth/Marketing
            r"(?i)how do I get users for my (startup|SaaS|MVP|side project)",
            r"(?i)how to market my (startup|business|SaaS|product)",
            r"(?i)best way to validate a (startup|SaaS|business) idea",
            r"(?i)how did you get your first (10|100|1000) users",
            r"(?i)how do you validate a (business|SaaS|startup) idea",
        ]

        
        for pattern in question_patterns:
            if re.search(pattern, text):
                logger.debug(f"Found question pattern: {pattern}")
                return True, f"question:{pattern}"
        
        return False, "" 