import os
from typing import List, Dict

class KnowledgeService:
    def __init__(self, knowledge_base_path: str = "data/knowledge_base"):
        self.kb_path = knowledge_base_path
        self._cache: Dict[str, str] = {}
        self._load_cache()
        
    def _load_cache(self):
        """Pre-load all knowledge files into memory."""
        if not os.path.exists(self.kb_path):
            return

        for filename in os.listdir(self.kb_path):
            if filename.endswith(".md"):
                file_path = os.path.join(self.kb_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._cache[filename] = f.read()
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def get_relevant_context(self, tags: List[str] = None) -> str:
        """
        Retrieves relevant knowledge based on tags (abnormal items) or defaults.
        Optimization Strategy:
        1. Always include 'Safety' and 'Guidelines' (Mandatory).
        2. Filter 'Interactions' or specific topic files based on tag keywords.
        """
        context_str = ""
        
        # 1. Mandatory Knowledge (Start with these)
        mandatory_files = ["general_guidelines.md", "supplement_safety.md"]
        for fname in mandatory_files:
            if fname in self._cache:
                context_str += f"\n\n### 📖 知識庫來源: {fname}\n{self._cache[fname]}"

        # 2. Contextual Knowledge (Filter by Tags)
        # If no tags, include everything (safe fallback)
        other_files = [f for f in self._cache.keys() if f not in mandatory_files]
        
        for fname in other_files:
            content = self._cache[fname]
            include = False
            
            if not tags:
                include = True
            else:
                # Naive Keyword Matching: If tag appears in file content
                for tag in tags:
                    # Basic normalization
                    clean_tag = tag.lower().replace("high", "").replace("low", "").strip() 
                    if clean_tag and (clean_tag in content.lower()):
                        include = True
                        break
            
            if include:
                 context_str += f"\n\n### 📖 知識庫來源: {fname}\n{content}"
            
        return context_str

knowledge_service = KnowledgeService()
