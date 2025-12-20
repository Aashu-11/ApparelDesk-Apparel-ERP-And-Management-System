"""
Model Analysis Script - Analyzes the trained recommendation model.
Works without implicit library installed.
"""

import pickle
import sys
from pathlib import Path

def analyze_model(model_path: str):
    """Analyze the pickled recommendation model."""
    
    print("=" * 60)
    print("RECOMMENDATION MODEL ANALYSIS")
    print("=" * 60)
    
    # Load model
    path = Path(model_path)
    if not path.exists():
        print(f"Error: Model file not found at {model_path}")
        return
    
    file_size_mb = path.stat().st_size / (1024 * 1024)
    print(f"\nFile: {model_path}")
    print(f"Size: {file_size_mb:.2f} MB")
    
    # Try to load - may fail if implicit not installed
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
    except ModuleNotFoundError as e:
        print(f"\n[!] Cannot fully load model: {e}")
        print("    Install implicit library to analyze model internals.")
        print("\n    On Windows, try one of these options:")
        print("    1. Install Visual Studio Build Tools first:")
        print("       https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("       Then: pip install implicit")
        print("\n    2. Use Anaconda/Miniconda:")
        print("       conda install -c conda-forge implicit")
        print("\n    3. Run in WSL (Windows Subsystem for Linux)")
        return
    
    print(f"\nKeys in pickle file:")
    for key in data.keys():
        print(f"   - {key}")
    
    # Analyze mappings
    print("\n" + "-" * 60)
    print("DATA STATISTICS")
    print("-" * 60)
    
    user_id_to_idx = data.get("user_id_to_idx", {})
    idx_to_user_id = data.get("idx_to_user_id", {})
    item_id_to_idx = data.get("item_id_to_idx", {})
    idx_to_item_id = data.get("idx_to_item_id", {})
    
    print(f"\nUsers:")
    print(f"   Total unique users: {len(user_id_to_idx):,}")
    if user_id_to_idx:
        user_ids = list(user_id_to_idx.keys())[:10]
        print(f"   Sample user IDs: {user_ids}")
    
    print(f"\nItems:")
    print(f"   Total unique items: {len(item_id_to_idx):,}")
    if item_id_to_idx:
        item_ids = list(item_id_to_idx.keys())[:10]
        print(f"   Sample item IDs: {item_ids}")
    
    # Analyze ALS model
    print("\n" + "-" * 60)
    print("ALS MODEL DETAILS")
    print("-" * 60)
    
    model = data.get("model")
    if model:
        print(f"\n   Model type: {type(model).__name__}")
        
        # Common ALS attributes
        if hasattr(model, 'factors'):
            print(f"   Latent factors: {model.factors}")
        if hasattr(model, 'regularization'):
            print(f"   Regularization: {model.regularization}")
        if hasattr(model, 'iterations'):
            print(f"   Iterations: {model.iterations}")
        if hasattr(model, 'user_factors'):
            uf = model.user_factors
            print(f"   User factors shape: {uf.shape}")
        if hasattr(model, 'item_factors'):
            itf = model.item_factors
            print(f"   Item factors shape: {itf.shape}")
    
    # Config & Metadata
    config = data.get("config", {})
    metadata = data.get("metadata", {})
    
    if config:
        print("\n" + "-" * 60)
        print("CONFIG")
        print("-" * 60)
        for k, v in config.items():
            print(f"   {k}: {v}")
    
    if metadata:
        print("\n" + "-" * 60)
        print("METADATA")
        print("-" * 60)
        for k, v in metadata.items():
            print(f"   {k}: {v}")
    
    print("\n" + "=" * 60)
    print("SAMPLE IDs FOR TESTING")
    print("=" * 60)
    print(f"\nUse these IDs to test the API:")
    print(f"   User IDs: {list(user_id_to_idx.keys())[:5]}")
    print(f"   Item IDs: {list(item_id_to_idx.keys())[:5]}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    model_path = "models/recommender_v1.pkl"
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    
    analyze_model(model_path)
