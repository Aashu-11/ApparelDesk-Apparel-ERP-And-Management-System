"""
RecommenderEngine: Loads and serves the pre-trained ALS recommendation model.
"""

import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Union
import numpy as np


class RecommenderEngine:
    """
    Production-ready recommendation engine that wraps the pre-trained ALS model.
    Handles all ID mappings and gracefully manages edge cases.
    """

    def __init__(self, model_path: str):
        """
        Initialize the engine by loading the pre-trained model.
        
        Args:
            model_path: Path to the .pkl file containing the trained model.
        """
        self.model = None
        self.user_id_to_idx = {}
        self.idx_to_user_id = {}
        self.item_id_to_idx = {}
        self.idx_to_item_id = {}
        self.config = {}
        self.metadata = {}
        self.is_loaded = False
        
        self._load_model(model_path)

    def _load_model(self, model_path: str) -> None:
        """Load the pickled model and its mappings."""
        path = Path(model_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        with open(path, "rb") as f:
            data = pickle.load(f)
        
        self.model = data["model"]
        self.user_id_to_idx = data["user_id_to_idx"]
        self.idx_to_user_id = data["idx_to_user_id"]
        self.item_id_to_idx = data["item_id_to_idx"]
        self.idx_to_item_id = data["idx_to_item_id"]
        self.config = data.get("config", {})
        self.metadata = data.get("metadata", {})
        self.is_loaded = True

    def _normalize_id(self, id_value: Union[int, str]) -> str:
        """Convert ID to string for lookup (model uses string keys)."""
        return str(id_value)

    def recommend_for_user(
        self, user_id: Union[int, str], limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get recommendations for a specific user.
        
        Args:
            user_id: External user ID (int or string).
            limit: Maximum number of recommendations to return.
        
        Returns:
            List of (item_id, score) tuples, sorted by score descending.
        """
        if not self.is_loaded:
            return []
        
        # Normalize ID to string for lookup
        user_id_str = self._normalize_id(user_id)
        
        # Check if user exists in mapping
        if user_id_str not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id_str]
        
        # Over-generate candidates to handle invalid indices
        n_candidates = min(limit * 3, len(self.idx_to_item_id))
        
        try:
            # ALS recommend() returns (item_indices, scores)
            # filter_already_liked_items=False because user_items matrix not available
            item_indices, scores = self.model.recommend(
                userid=user_idx,
                user_items=None,
                N=n_candidates,
                filter_already_liked_items=False
            )
        except Exception as e:
            print(f"Error in recommend: {e}")
            return []
        
        results = []
        for idx, score in zip(item_indices, scores):
            # Convert numpy types to Python native types
            idx_int = int(idx)
            score_float = float(score)
            
            # Safely handle indices that don't exist in mapping
            if idx_int not in self.idx_to_item_id:
                continue
            
            item_id = self.idx_to_item_id[idx_int]
            results.append((str(item_id), score_float))
            
            # Stop once we have enough valid results
            if len(results) >= limit:
                break
        
        return results

    def similar_items(
        self, item_id: Union[int, str], limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get items similar to a given item.
        
        Args:
            item_id: External item ID (int or string).
            limit: Maximum number of similar items to return.
        
        Returns:
            List of (item_id, score) tuples, sorted by similarity descending.
        """
        if not self.is_loaded:
            return []
        
        # Normalize ID to string for lookup
        item_id_str = self._normalize_id(item_id)
        
        # Check if item exists in mapping
        if item_id_str not in self.item_id_to_idx:
            return []
        
        item_idx = self.item_id_to_idx[item_id_str]
        
        # Over-generate candidates to handle invalid indices
        n_candidates = min(limit * 3, len(self.idx_to_item_id))
        
        try:
            # similar_items() also returns (item_indices, scores)
            item_indices, scores = self.model.similar_items(
                itemid=item_idx,
                N=n_candidates
            )
        except Exception as e:
            print(f"Error in similar_items: {e}")
            return []
        
        results = []
        for idx, score in zip(item_indices, scores):
            # Convert numpy types to Python native types
            idx_int = int(idx)
            score_float = float(score)
            
            # Safely handle indices that don't exist in mapping
            if idx_int not in self.idx_to_item_id:
                continue
            
            similar_item_id = self.idx_to_item_id[idx_int]
            
            # Skip the input item itself
            if str(similar_item_id) == item_id_str:
                continue
            
            results.append((str(similar_item_id), score_float))
            
            # Stop once we have enough valid results
            if len(results) >= limit:
                break
        
        return results

    def get_model_info(self) -> dict:
        """Return metadata about the loaded model."""
        return {
            "is_loaded": self.is_loaded,
            "num_users": len(self.user_id_to_idx),
            "num_items": len(self.item_id_to_idx),
            "config": self.config,
            "metadata": self.metadata
        }
    
    def get_sample_ids(self) -> dict:
        """Return sample user and item IDs for testing."""
        return {
            "sample_user_ids": list(self.user_id_to_idx.keys())[:10],
            "sample_item_ids": list(self.item_id_to_idx.keys())[:10]
        }
