"""
FastAPI backend for the recommendation system.
Stateless, read-only inference endpoints.
"""

import os
from pathlib import Path
from typing import List, Optional, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.recommender_engine import RecommenderEngine


# Response models
class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    num_users: Optional[int] = None
    num_items: Optional[int] = None
    sample_user_ids: Optional[List[str]] = None
    sample_item_ids: Optional[List[str]] = None


class RecommendationItem(BaseModel):
    item_id: str
    score: float


class UserRecommendationsResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendationItem]
    count: int
    message: Optional[str] = None


class SimilarProductsResponse(BaseModel):
    item_id: str
    similar_products: List[RecommendationItem]
    count: int
    message: Optional[str] = None


class OutfitItem(BaseModel):
    item_id: str
    score: float
    category: str


class OutfitMatchResponse(BaseModel):
    base_item_id: str
    base_category: Optional[str] = None
    outfit_items: List[OutfitItem]
    count: int
    message: Optional[str] = None


# Global engine reference
engine: Optional[RecommenderEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the recommendation engine at startup."""
    global engine
    
    # Model path relative to project root
    model_path = Path(__file__).parent.parent / "models" / "recommender_v1.pkl"
    
    try:
        engine = RecommenderEngine(str(model_path))
        model_info = engine.get_model_info()
        sample_ids = engine.get_sample_ids()
        
        print("\n" + "=" * 60)
        print("API SERVER READY")
        print("=" * 60)
        print(f"  Model: {model_path}")
        print(f"  Users: {model_info['num_users']}, Items: {model_info['num_items']}")
        print(f"  Data Source: {engine.data_source.upper()}")
        if engine.data_source == "mysql":
            print(f"  MySQL Host: {engine.mysql_host}")
        elif engine.data_source == "csv":
            print(f"  Using CSV fallback")
        print(f"  Sample User IDs: {sample_ids['sample_user_ids'][:5]}")
        print(f"  Sample Item IDs: {sample_ids['sample_item_ids'][:5]}")
        print("=" * 60 + "\n")
        
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("  API will start but recommendations will not be available.")
        engine = None
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()
        engine = None
    
    yield
    
    # Cleanup
    engine = None


app = FastAPI(
    title="E-Commerce Recommendation API",
    description="Netflix-style recommendation system using ALS collaborative filtering",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access (including file:// origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],  # 'null' is for file:// protocol
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    if engine is None or not engine.is_loaded:
        return HealthResponse(
            status="degraded",
            model_loaded=False
        )
    
    model_info = engine.get_model_info()
    sample_ids = engine.get_sample_ids()
    return HealthResponse(
        status="healthy",
        model_loaded=True,
        num_users=model_info["num_users"],
        num_items=model_info["num_items"],
        sample_user_ids=sample_ids["sample_user_ids"][:5],
        sample_item_ids=sample_ids["sample_item_ids"][:5]
    )


@app.get("/recommendations/user/{user_id}", response_model=UserRecommendationsResponse)
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of recommendations")
):
    """
    Get personalized recommendations for a user.
    
    - **user_id**: The external user ID (string or number)
    - **limit**: Maximum number of recommendations (1-100)
    """
    if engine is None or not engine.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Recommendation model not loaded"
        )
    
    recommendations = engine.recommend_for_user(user_id, limit=limit)
    
    if not recommendations:
        return UserRecommendationsResponse(
            user_id=user_id,
            recommendations=[],
            count=0,
            message=f"No recommendations found. User '{user_id}' may not exist in the training data."
        )
    
    return UserRecommendationsResponse(
        user_id=user_id,
        recommendations=[
            RecommendationItem(item_id=item_id, score=round(score, 4))
            for item_id, score in recommendations
        ],
        count=len(recommendations)
    )


@app.get("/recommendations/product/{item_id}", response_model=SimilarProductsResponse)
async def get_similar_products(
    item_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of similar products")
):
    """
    Get products similar to a given product.
    
    - **item_id**: The external product/item ID (string or number)
    - **limit**: Maximum number of similar products (1-100)
    """
    if engine is None or not engine.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Recommendation model not loaded"
        )
    
    similar = engine.similar_items(item_id, limit=limit)
    
    if not similar:
        return SimilarProductsResponse(
            item_id=item_id,
            similar_products=[],
            count=0,
            message=f"No similar products found. Item '{item_id}' may not exist in the training data."
        )
    
    return SimilarProductsResponse(
        item_id=item_id,
        similar_products=[
            RecommendationItem(item_id=sim_id, score=round(score, 4))
            for sim_id, score in similar
        ],
        count=len(similar)
    )


@app.get("/recommendations/outfit/{item_id}", response_model=OutfitMatchResponse)
async def get_outfit_matches(
    item_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Number of recommendations to consider"),
    limit_per_type: int = Query(default=1, ge=1, le=10, description="Max items per category")
):
    """
    Get complementary outfit items for a product.
    
    When viewing jeans, this returns complementary items like shirts, shoes, jackets.
    NOT items of the same type.
    
    - **item_id**: The base product ID (e.g., jeans)
    - **limit**: How many similar items to consider (higher = more variety)
    - **limit_per_type**: Maximum items per category type (default: 1)
    """
    if engine is None or not engine.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Recommendation model not loaded"
        )
    
    # Get base item's category for display
    base_category = engine.item_descriptions.get(str(item_id))
    
    # First get similar items from the recommender
    similar = engine.similar_items(item_id, limit=limit)
    
    if not similar:
        return OutfitMatchResponse(
            base_item_id=item_id,
            base_category=base_category,
            outfit_items=[],
            count=0,
            message=f"No outfit matches found. Item '{item_id}' may not exist in the training data."
        )
    
    # Filter to complementary items only
    outfit_matches = engine.get_outfit_matches(
        base_item_id=item_id,
        recommended_items=similar,
        limit_per_type=limit_per_type
    )
    
    if not outfit_matches:
        return OutfitMatchResponse(
            base_item_id=item_id,
            base_category=base_category,
            outfit_items=[],
            count=0,
            message=f"No complementary items found. Item '{item_id}' may not have category data."
        )
    
    return OutfitMatchResponse(
        base_item_id=item_id,
        base_category=base_category,
        outfit_items=[
            OutfitItem(item_id=oid, score=round(score, 4), category=cat)
            for oid, score, cat in outfit_matches
        ],
        count=len(outfit_matches)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
