from typing import Tuple, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticMatcher:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def match(self, text: str, keywords: Dict[str, Any], threshold: float = 0.8) -> Tuple[bool, str]:
        keyword_embeddings = self.model.encode(keywords["keywords"])
        text_embedding = self.model.encode(text)
        
        similarities = np.dot(keyword_embeddings, text_embedding)
        
        if np.max(similarities) > threshold:
            most_similar_idx = np.argmax(similarities)
            return True, f"semantic:{keywords['keywords'][most_similar_idx]}"
            
        return False, "" 