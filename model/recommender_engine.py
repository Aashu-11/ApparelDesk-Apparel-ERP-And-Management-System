"""
RecommenderEngine: Sklearn-based recommendation model with MySQL support.
Uses TruncatedSVD for matrix factorization - no C++ compilation needed!
Loads item descriptions from MySQL database.
"""

import csv
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Union, Dict
import numpy as np


class RecommenderEngine:
    """
    Production-ready recommendation engine using sklearn.
    Works on Windows without any C++ build tools!
    
    Features:
    - User recommendations
    - Similar items
    - Outfit matching (complementary items)
    - MySQL database support for item descriptions
    """

    def __init__(
        self, 
        model_path: str, 
        item_descriptions_path: Optional[str] = None,
        use_mysql: bool = True
    ):
        """
        Initialize the engine by loading the pre-trained model.
        
        Args:
            model_path: Path to the pickled model file
            item_descriptions_path: Path to CSV file (fallback if MySQL fails)
            use_mysql: Whether to try loading from MySQL first
        """
        self.model = None
        self.user_factors = None
        self.item_factors = None
        self.user_id_to_idx = {}
        self.idx_to_user_id = {}
        self.item_id_to_idx = {}
        self.idx_to_item_id = {}
        self.config = {}
        self.metadata = {}
        self.is_loaded = False
        
        # Item descriptions for outfit matching
        self.item_descriptions: Dict[str, str] = {}
        
        self._load_model(model_path)
        self._load_item_descriptions(item_descriptions_path, use_mysql)

    def _load_model(self, model_path: str) -> None:
        """Load the pickled model and its mappings."""
        path = Path(model_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        with open(path, "rb") as f:
            data = pickle.load(f)
        
        # Check if it's the new sklearn format or old implicit format
        if "user_factors" in data:
            # New sklearn format - just numpy arrays
            self.user_factors = data["user_factors"]
            self.item_factors = data["item_factors"]
        elif "model" in data:
            # Old implicit format - extract factors from model
            model = data["model"]
            if hasattr(model, 'user_factors'):
                self.user_factors = np.array(model.user_factors)
                self.item_factors = np.array(model.item_factors)
            else:
                raise ValueError("Model format not recognized")
        else:
            raise ValueError("Model format not recognized")
        
        self.user_id_to_idx = data["user_id_to_idx"]
        self.idx_to_user_id = data["idx_to_user_id"]
        self.item_id_to_idx = data["item_id_to_idx"]
        self.idx_to_item_id = data["idx_to_item_id"]
        self.config = data.get("config", {})
        self.metadata = data.get("metadata", {})
        self.is_loaded = True

    def _load_item_descriptions(
        self, 
        item_descriptions_path: Optional[str] = None,
        use_mysql: bool = True
    ) -> None:
        """
        Load item descriptions from MySQL database or CSV file.
        
        Priority:
        1. MySQL database (if use_mysql=True and connection works)
        2. CSV file (fallback)
        """
        # Try MySQL first
        if use_mysql:
            try:
                from data.mysql_loader import MySQLDataLoader
                loader = MySQLDataLoader()
                
                if loader.connection:
                    self.item_descriptions = loader.get_product_descriptions()
                    loader.close()
                    
                    if self.item_descriptions:
                        print(f"[OUTFIT MATCHING] Loaded {len(self.item_descriptions)} descriptions from MySQL")
                        return
            except ImportError:
                print("[OUTFIT MATCHING] MySQL loader not available, using CSV")
            except Exception as e:
                print(f"[OUTFIT MATCHING] MySQL error: {e}, falling back to CSV")
        
        # Fallback to CSV
        if item_descriptions_path is None:
            base_path = Path(__file__).parent.parent / "data" / "item_descriptions.csv"
            item_descriptions_path = str(base_path)
        
        path = Path(item_descriptions_path)
        
        if not path.exists():
            print(f"[OUTFIT MATCHING] Warning: item_descriptions.csv not found at {path}")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item_id = str(row["item_id"]).strip()
                    description = row["description"].strip().lower()
                    self.item_descriptions[item_id] = description
            
            print(f"[OUTFIT MATCHING] Loaded {len(self.item_descriptions)} descriptions from CSV")
        except Exception as e:
            print(f"[OUTFIT MATCHING] Error loading CSV: {e}")
            self.item_descriptions = {}

    def reload_descriptions_from_mysql(self) -> bool:
        """
        Reload item descriptions from MySQL database.
        Useful for refreshing data without restarting the server.
        
        Returns:
            True if reload was successful
        """
        try:
            from data.mysql_loader import MySQLDataLoader
            loader = MySQLDataLoader()
            
            if loader.connection:
                new_descriptions = loader.get_product_descriptions()
                loader.close()
                
                if new_descriptions:
                    self.item_descriptions = new_descriptions
                    print(f"[OUTFIT MATCHING] Reloaded {len(self.item_descriptions)} descriptions from MySQL")
                    return True
            
            return False
        except Exception as e:
            print(f"[OUTFIT MATCHING] Reload failed: {e}")
            return False

    def get_outfit_matches(
        self,
        base_item_id: Union[int, str],
        recommended_items: List[Tuple[str, float]],
        limit_per_type: int = 1
    ) -> List[Tuple[str, float, str]]:
        """
        Get complementary outfit items from recommendations.
        
        Args:
            base_item_id: The base item (e.g., jeans)
            recommended_items: List of (item_id, score) recommendations
            limit_per_type: Max items per category
            
        Returns:
            List of (item_id, score, category) tuples for complementary items
        """
        base_item_id_str = self._normalize_id(base_item_id)
        
        if not self.item_descriptions:
            return []
        
        base_description = self.item_descriptions.get(base_item_id_str)
        if base_description is None:
            return []
        
        category_counts: Dict[str, int] = {}
        outfit_items: List[Tuple[str, float, str]] = []
        
        for item_id, score in recommended_items:
            item_id_str = self._normalize_id(item_id)
            item_description = self.item_descriptions.get(item_id_str)
            
            if item_description is None:
                continue
            
            # Skip items of the same type as base
            if item_description == base_description:
                continue
            
            current_count = category_counts.get(item_description, 0)
            if current_count >= limit_per_type:
                continue
            
            outfit_items.append((item_id_str, score, item_description))
            category_counts[item_description] = current_count + 1
        
        return outfit_items

    def _normalize_id(self, id_value: Union[int, str]) -> str:
        """Convert ID to string for lookup."""
        return str(id_value)

    def recommend_for_user(
        self, user_id: Union[int, str], limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Get recommendations for a specific user."""
        if not self.is_loaded:
            return []
        
        user_id_str = self._normalize_id(user_id)
        
        if user_id_str not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id_str]
        
        # Compute scores: user_factor dot product with all item_factors
        user_vector = self.user_factors[user_idx]
        scores = np.dot(self.item_factors, user_vector)
        
        # Get top indices
        top_indices = np.argsort(scores)[::-1][:limit * 2]
        
        results = []
        for idx in top_indices:
            idx_int = int(idx)
            if idx_int not in self.idx_to_item_id:
                continue
            
            item_id = self.idx_to_item_id[idx_int]
            score = float(scores[idx])
            results.append((str(item_id), score))
            
            if len(results) >= limit:
                break
        
        return results

    def similar_items(
        self, item_id: Union[int, str], limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Get items similar to a given item."""
        if not self.is_loaded:
            return []
        
        item_id_str = self._normalize_id(item_id)
        
        if item_id_str not in self.item_id_to_idx:
            return []
        
        item_idx = self.item_id_to_idx[item_id_str]
        
        # Compute cosine similarity with all items
        item_vector = self.item_factors[item_idx]
        
        # Normalize for cosine similarity
        item_norm = np.linalg.norm(item_vector)
        if item_norm == 0:
            return []
        
        item_vector_normalized = item_vector / item_norm
        
        # Compute similarities
        norms = np.linalg.norm(self.item_factors, axis=1)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized_factors = self.item_factors / norms[:, np.newaxis]
        
        similarities = np.dot(normalized_factors, item_vector_normalized)
        
        # Get top indices
        top_indices = np.argsort(similarities)[::-1][:limit * 2]
        
        results = []
        for idx in top_indices:
            idx_int = int(idx)
            if idx_int not in self.idx_to_item_id:
                continue
            
            similar_item_id = self.idx_to_item_id[idx_int]
            
            # Skip the input item itself
            if str(similar_item_id) == item_id_str:
                continue
            
            score = float(similarities[idx])
            results.append((str(similar_item_id), score))
            
            if len(results) >= limit:
                break
        
        return results

    def get_model_info(self) -> dict:
        """Return metadata about the loaded model."""
        return {
            "is_loaded": self.is_loaded,
            "num_users": len(self.user_id_to_idx),
            "num_items": len(self.item_id_to_idx),
            "num_descriptions": len(self.item_descriptions),
            "config": self.config,
            "metadata": self.metadata
        }
    
    def get_sample_ids(self) -> dict:
        """Return sample user and item IDs for testing."""
        return {
            "sample_user_ids": list(self.user_id_to_idx.keys())[:10],
            "sample_item_ids": list(self.item_id_to_idx.keys())[:10]
        }
