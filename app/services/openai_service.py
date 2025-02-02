from openai import AsyncOpenAI
from ..models.social_post import SocialPost
from ..config.settings import get_settings
from typing import List
import logging
import json

logger = logging.getLogger("uvicorn")

class OpenAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        
    async def filter_promotion_worthy(self, posts: List[SocialPost]) -> List[SocialPost]:
        """
        Acts as a final filter on matched posts, returning only those worth promoting to.
        """
        logger.info(f"Filtering {len(posts)} posts through OpenAI analysis")
        filtered_posts = []
        
        for post in posts:
            should_promote, _ = await self._evaluate_post(post)
            if should_promote:
                filtered_posts.append(post)
                
        logger.info(f"OpenAI filter: {len(filtered_posts)} posts passed out of {len(posts)}")
        return filtered_posts

    async def _evaluate_post(self, post: SocialPost) -> tuple[bool, str]:
        """
        Evaluate if a post is suitable for product promotion
        Returns: (should_promote: bool, reasoning: str)
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying potential business leads and networking opportunities."},
                    {"role": "user", "content": f"""Here's a post from {post.platform}:

Title: {post.title if post.title else 'N/A'}
Content: {post.content}
Author: {post.author}

Return true if ANY of these are true:
1. The post is asking people to share what they're working on
2. The author is seeking business/startup ideas
3. The author is looking for SaaS products or business tools
4. The post is about lead generation or finding customers"""}
                ],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "should_promote",
                        "description": "Return whether this post represents a lead opportunity",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "promote": {
                                    "type": "boolean",
                                    "description": "Whether this post represents a potential lead"
                                }
                            },
                            "required": ["promote"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "should_promote"}}
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            result = json.loads(tool_call.function.arguments)
            should_promote = result["promote"]
            
            logger.info(f"OpenAI evaluation complete - Should promote: {should_promote}")
            
            return should_promote, "AI evaluated post for lead potential"
            
        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {str(e)}")
            raise 