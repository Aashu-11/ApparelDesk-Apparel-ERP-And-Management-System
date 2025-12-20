# 🎯 ALS Recommendation System - Complete Technical Guide

> **Author:** Recommendation System Team  
> **Last Updated:** December 20, 2025  
> **Purpose:** Mentor Presentation & Code Documentation

---

## 📋 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [System Overview](#-system-overview)
3. [Architecture Flowchart](#-architecture-flowchart)
4. [Core Components Deep Dive](#-core-components-deep-dive)
5. [Code Walkthrough](#-code-walkthrough)
6. [Data Flow Diagram](#-data-flow-diagram)
7. [Key Concepts Explained](#-key-concepts-explained)
8. [Common Questions & Answers](#-common-questions--answers)

---

## 🎯 Executive Summary

This recommendation system uses **Alternating Least Squares (ALS)**, a collaborative filtering algorithm, to provide:

| Feature | Description |
|---------|-------------|
| **User Recommendations** | Personalized product suggestions based on user behavior |
| **Similar Items** | Products similar to a given item based on user interaction patterns |

### Why ALS?

- ✅ **Scalable** - Handles millions of users and items
- ✅ **Implicit Feedback** - Works with views, clicks, purchases (not just ratings)
- ✅ **Fast Inference** - Pre-computed embeddings enable real-time recommendations
- ✅ **Industry Standard** - Used by Spotify, Netflix, Amazon

---

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RECOMMENDATION SYSTEM ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────┐    │
│   │   Raw Data  │───▶│  Training Phase │───▶│  Trained Model (.pkl)   │    │
│   │ (CSV/DB)    │    │  (ALS Algorithm)│    │  + ID Mappings          │    │
│   └─────────────┘    └─────────────────┘    └───────────┬─────────────┘    │
│                                                         │                   │
│                              ┌──────────────────────────┘                   │
│                              ▼                                              │
│                    ┌─────────────────────┐                                  │
│                    │   Inference Phase   │                                  │
│                    │  (This Script!)     │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│              ┌────────────────┼────────────────┐                            │
│              ▼                ▼                ▼                            │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│    │    User      │  │   Similar    │  │   Similar    │                    │
│    │Recommendations│  │    Items     │  │    Users     │                    │
│    └──────────────┘  └──────────────┘  └──────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Architecture Flowchart

### Main Inference Flow

```
                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Load recommender_    │
                    │  artifacts.pkl        │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Extract Components:  │
                    │  • model              │
                    │  • user_id_to_idx     │
                    │  • idx_to_item_id     │
                    │  • item_id_to_idx     │
                    └───────────┬───────────┘
                                │
           ┌────────────────────┴────────────────────┐
           ▼                                         ▼
┌─────────────────────┐                   ┌─────────────────────┐
│ USER RECOMMENDATIONS│                   │   SIMILAR ITEMS     │
└──────────┬──────────┘                   └──────────┬──────────┘
           │                                         │
           ▼                                         ▼
┌─────────────────────┐                   ┌─────────────────────┐
│ Get user_id from    │                   │ Get item_id from    │
│ available users     │                   │ available items     │
└──────────┬──────────┘                   └──────────┬──────────┘
           │                                         │
           ▼                                         ▼
┌─────────────────────┐                   ┌─────────────────────┐
│ Convert to user_idx │                   │ Convert to item_idx │
│ (internal index)    │                   │ (internal index)    │
└──────────┬──────────┘                   └──────────┬──────────┘
           │                                         │
           ▼                                         ▼
┌─────────────────────┐                   ┌─────────────────────┐
│ model.recommend()   │                   │ model.similar_items │
│ Returns: indices,   │                   │ Returns: indices,   │
│          scores     │                   │          scores     │
└──────────┬──────────┘                   └──────────┬──────────┘
           │                                         │
           ▼                                         ▼
┌─────────────────────┐                   ┌─────────────────────┐
│ 🔒 SAFETY CHECK:    │                   │ 🔒 SAFETY CHECK:    │
│ Is item_idx in      │                   │ Is sim_idx in       │
│ idx_to_item_id?     │                   │ idx_to_item_id?     │
└──────────┬──────────┘                   └──────────┬──────────┘
           │                                         │
     ┌─────┴─────┐                           ┌─────┴─────┐
     ▼           ▼                           ▼           ▼
   [YES]       [NO]                        [YES]       [NO]
     │           │                           │           │
     ▼           ▼                           ▼           ▼
┌─────────┐ ┌─────────┐                ┌─────────┐ ┌─────────┐
│ Convert │ │  Skip   │                │ Convert │ │  Skip   │
│ to real │ │  this   │                │ to real │ │  this   │
│ item_id │ │  item   │                │ item_id │ │  item   │
└────┬────┘ └─────────┘                └────┬────┘ └─────────┘
     │                                      │
     ▼                                      ▼
┌─────────────────────┐                ┌─────────────────────┐
│ Display Product ID  │                │ Display Similar     │
│ with Score          │                │ Product with Score  │
└──────────┬──────────┘                └──────────┬──────────┘
           │                                      │
           └──────────────┬───────────────────────┘
                          ▼
                        END
```

---

## 🔧 Core Components Deep Dive

### 1. The Pickle File Structure

```python
artifacts = {
    "model":           <AlternatingLeastSquares>,  # Trained ALS model
    "user_id_to_idx":  {"user123": 0, "user456": 1, ...},  # User ID → Index
    "idx_to_user_id":  {0: "user123", 1: "user456", ...},  # Index → User ID
    "item_id_to_idx":  {"prod_A": 0, "prod_B": 1, ...},    # Item ID → Index
    "idx_to_item_id":  {0: "prod_A", 1: "prod_B", ...}     # Index → Item ID
}
```

### 2. Why Do We Need ID Mappings?

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ID MAPPING EXPLAINED                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  YOUR DATA (External IDs)          MODEL INTERNALS (Matrix Indices)  │
│  ─────────────────────────         ──────────────────────────────── │
│                                                                      │
│  user_id: "USR_12345"     ──────▶  user_idx: 0                      │
│  user_id: "USR_67890"     ──────▶  user_idx: 1                      │
│  user_id: "USR_11111"     ──────▶  user_idx: 2                      │
│                                                                      │
│  item_id: "PROD_ABC"      ──────▶  item_idx: 0                      │
│  item_id: "PROD_XYZ"      ──────▶  item_idx: 1                      │
│  item_id: "PROD_123"      ──────▶  item_idx: 2                      │
│                                                                      │
│  WHY? The ALS model uses MATRICES internally:                       │
│                                                                      │
│       User Factors Matrix          Item Factors Matrix              │
│       ┌─────────────────┐          ┌─────────────────┐              │
│       │ [0.2, 0.5, 0.1] │ idx=0    │ [0.3, 0.8, 0.2] │ idx=0        │
│       │ [0.8, 0.3, 0.6] │ idx=1    │ [0.1, 0.4, 0.9] │ idx=1        │
│       │ [0.4, 0.7, 0.2] │ idx=2    │ [0.7, 0.2, 0.5] │ idx=2        │
│       └─────────────────┘          └─────────────────┘              │
│                                                                      │
│  Recommendation = User Vector · Item Vector (dot product)           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3. The ALS Model Object

```python
model.user_factors  # Shape: (num_users, num_factors) - User embeddings
model.item_factors  # Shape: (num_items, num_factors) - Item embeddings

# Key methods:
model.recommend(userid, user_items, N)  # Get N recommendations for user
model.similar_items(itemid, N)          # Get N similar items
```

---

## 📝 Code Walkthrough

### Section 1: Loading Artifacts

```python
with open("recommender_artifacts.pkl", "rb") as f:
    artifacts = pickle.load(f)

model = artifacts["model"]
user_id_to_idx = artifacts["user_id_to_idx"]
idx_to_item_id = artifacts["idx_to_item_id"]
item_id_to_idx = artifacts["item_id_to_idx"]
```

**What's Happening:**
1. Open the pickle file in binary read mode (`"rb"`)
2. Deserialize the Python objects stored inside
3. Extract each component into its own variable

**Memory Layout:**
```
┌────────────────────────────────────────┐
│        recommender_artifacts.pkl       │
│  ┌──────────────────────────────────┐  │
│  │  model: ALS trained weights      │──┼──▶ model
│  ├──────────────────────────────────┤  │
│  │  user_id_to_idx: {str: int}      │──┼──▶ user_id_to_idx
│  ├──────────────────────────────────┤  │
│  │  idx_to_item_id: {int: str}      │──┼──▶ idx_to_item_id
│  ├──────────────────────────────────┤  │
│  │  item_id_to_idx: {str: int}      │──┼──▶ item_id_to_idx
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

---

### Section 2: Debug Check

```python
print("ALS item factors:", model.item_factors.shape[0])
print("Mapped items:", len(idx_to_item_id))
```

**Why This Matters:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                    POTENTIAL MISMATCH CHECK                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  model.item_factors.shape[0] = 1000  (Model knows 1000 items)       │
│  len(idx_to_item_id) = 950           (Mapping has 950 items)        │
│                                                                     │
│  ⚠️ MISMATCH! 50 item indices have no mapping!                      │
│                                                                     │
│  This can happen when:                                              │
│  • Training data had items that were later removed                  │
│  • Sparse matrix indices don't match item catalog                   │
│  • Data cleaning removed some items after training                  │
│                                                                     │
│  SOLUTION: Safety checks in the inference code (see below)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Section 3: User Recommendations

```python
# Step 1: Get a valid user ID
user_id = list(user_id_to_idx.keys())[0]  # e.g., "USR_12345"

# Step 2: Convert to internal index
user_idx = user_id_to_idx[user_id]        # e.g., 0

# Step 3: Get recommendations from model
item_indices, scores = model.recommend(
    userid=user_idx,
    user_items=None,                      # No filtering
    N=10,                                 # Get 10 candidates
    filter_already_liked_items=False      # Include previously seen items
)

# Step 4: Convert back to real IDs with safety check
for item_idx, score in zip(item_indices, scores):
    if int(item_idx) not in idx_to_item_id:
        continue  # 🔒 SKIP invalid indices
    
    print(f"Product {idx_to_item_id[int(item_idx)]} → score: {score:.4f}")
```

**Visual Flow:**
```
"USR_12345"                    [0.2, 0.5, 0.8, 0.1]
     │                                   │
     ▼                                   ▼
user_id_to_idx["USR_12345"]    model.user_factors[0]
     │                                   │
     ▼                                   │
   idx = 0 ─────────────────────────────┘
                                         │
                            ┌────────────┴────────────┐
                            ▼                         ▼
                    Compute dot product      Sort by score
                    with all item vectors    descending
                            │                         │
                            └────────────┬────────────┘
                                         ▼
                              item_indices = [42, 17, 88, ...]
                              scores = [0.95, 0.87, 0.82, ...]
                                         │
                                         ▼
                              idx_to_item_id[42] = "PROD_XYZ"
                                         │
                                         ▼
                              OUTPUT: "PROD_XYZ → 0.9500"
```

---

### Section 4: Similar Items

```python
# Step 1: Get a valid item ID
item_id = list(item_id_to_idx.keys())[0]  # e.g., "PROD_ABC"

# Step 2: Convert to internal index
item_idx = item_id_to_idx[item_id]         # e.g., 5

# Step 3: Find similar items
similar_indices, similar_scores = model.similar_items(item_idx, N=10)

# Step 4: Convert back with safety check
for sim_idx, score in zip(similar_indices, similar_scores):
    if int(sim_idx) not in idx_to_item_id:
        continue  # 🔒 SKIP invalid indices
    
    print(f"Product {idx_to_item_id[int(sim_idx)]} → similarity: {score:.4f}")
```

**How Similar Items Works:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                    SIMILAR ITEMS ALGORITHM                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Item Factors Matrix (each row = item embedding)                    │
│  ┌──────────────────────────────────────────┐                       │
│  │ idx=0: [0.2, 0.8, 0.1, 0.5]  ─── PROD_A  │                       │
│  │ idx=1: [0.3, 0.7, 0.2, 0.4]  ─── PROD_B  │ ← Similar to PROD_A!  │
│  │ idx=2: [0.9, 0.1, 0.8, 0.2]  ─── PROD_C  │                       │
│  │ idx=3: [0.25, 0.75, 0.15, 0.45] ─ PROD_D │ ← Also similar!       │
│  │ idx=4: [0.8, 0.2, 0.7, 0.3]  ─── PROD_E  │                       │
│  └──────────────────────────────────────────┘                       │
│                                                                     │
│  For item idx=0 (PROD_A), compute cosine similarity with all:       │
│                                                                     │
│  similarity(0, 1) = 0.95  ⭐ HIGH                                   │
│  similarity(0, 2) = 0.23                                            │
│  similarity(0, 3) = 0.97  ⭐ HIGHEST                                │
│  similarity(0, 4) = 0.31                                            │
│                                                                     │
│  Result: [idx=3, idx=1, idx=4, idx=2] sorted by similarity          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE DATA FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                           │
│  │   RAW DATA   │                                                           │
│  │              │                                                           │
│  │ user_id,     │                                                           │
│  │ item_id,     │                                                           │
│  │ interaction  │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        TRAINING PHASE                                 │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐   │   │
│  │  │ Create ID   │───▶│ Build Sparse│───▶│ Train ALS Model         │   │   │
│  │  │ Mappings    │    │ Matrix      │    │ (Learn User & Item      │   │   │
│  │  │             │    │             │    │  Factor Matrices)       │   │   │
│  │  └─────────────┘    └─────────────┘    └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     PICKLE FILE (.pkl)                                │   │
│  │  ┌───────────┬───────────────┬───────────────┬───────────────┐       │   │
│  │  │   model   │ user_id_to_idx│ idx_to_item_id│ item_id_to_idx│       │   │
│  │  └───────────┴───────────────┴───────────────┴───────────────┘       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       INFERENCE PHASE                                 │   │
│  │                                                                       │   │
│  │    ┌─────────────────────────────────────────────────────────────┐   │   │
│  │    │                    THIS SCRIPT                               │   │   │
│  │    │                                                              │   │   │
│  │    │  1. Load pickle ───────────────────────────────────────────▶│   │   │
│  │    │                                                              │   │   │
│  │    │  2. External ID ──▶ user_id_to_idx ──▶ Internal Index       │   │   │
│  │    │                                                              │   │   │
│  │    │  3. model.recommend() / model.similar_items()               │   │   │
│  │    │                                                              │   │   │
│  │    │  4. Internal Index ──▶ idx_to_item_id ──▶ External ID       │   │   │
│  │    │                                                              │   │   │
│  │    │  5. Return recommendations with real product IDs            │   │   │
│  │    │                                                              │   │   │
│  │    └─────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Key Concepts Explained

### 1. Alternating Least Squares (ALS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ALS ALGORITHM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GOAL: Approximate the User-Item Interaction Matrix R as:                   │
│                                                                             │
│                    R ≈ U × I^T                                              │
│                                                                             │
│  Where:                                                                     │
│  • R = Original interaction matrix (users × items)                          │
│  • U = User factors matrix (users × latent_factors)                         │
│  • I = Item factors matrix (items × latent_factors)                         │
│                                                                             │
│  ┌─────────────┐     ┌───────────────┐     ┌─────────────┐                  │
│  │      U      │  ×  │      I^T      │  =  │      R̂      │                  │
│  │ (100 × 50)  │     │  (50 × 1000)  │     │ (100 × 1000)│                  │
│  │             │     │               │     │  Predicted  │                  │
│  │ User        │     │ Item          │     │  Ratings    │                  │
│  │ Embeddings  │     │ Embeddings    │     │             │                  │
│  └─────────────┘     └───────────────┘     └─────────────┘                  │
│                                                                             │
│  TRAINING PROCESS (Alternating):                                            │
│  ────────────────────────────────                                           │
│  1. Initialize U and I randomly                                             │
│  2. Fix I, optimize U using least squares                                   │
│  3. Fix U, optimize I using least squares                                   │
│  4. Repeat steps 2-3 until convergence                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Latent Factors (Embeddings)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LATENT FACTORS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Each user and item is represented as a vector of numbers:                  │
│                                                                             │
│  User "Alice" = [0.8, 0.2, 0.9, 0.1, 0.5]                                   │
│                  │    │    │    │    │                                      │
│                  │    │    │    │    └── Factor 5: Price sensitivity?       │
│                  │    │    │    └─────── Factor 4: Brand loyalty?           │
│                  │    │    └──────────── Factor 3: Quality preference?      │
│                  │    └───────────────── Factor 2: Style preference?        │
│                  └────────────────────── Factor 1: Category interest?       │
│                                                                             │
│  Item "iPhone" = [0.7, 0.3, 0.85, 0.2, 0.9]                                 │
│                                                                             │
│  Similarity = Alice · iPhone = 0.8×0.7 + 0.2×0.3 + ... = HIGH SCORE        │
│                                                                             │
│  🎯 The model LEARNS these factors automatically from interaction data!     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. The Safety Check Explained

```python
if int(item_idx) not in idx_to_item_id:
    continue  # SKIP this item
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WHY SAFETY CHECK?                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROBLEM:                                                                   │
│  ─────────                                                                  │
│  model.item_factors has 1000 rows (indices 0-999)                           │
│  idx_to_item_id only maps indices 0-949 to real product IDs                 │
│                                                                             │
│  model.recommend() might return:                                            │
│  item_indices = [42, 17, 955, 88, 1002, ...]                               │
│                         ^^^       ^^^^                                      │
│                    Not in mapping!  Out of range!                           │
│                                                                             │
│  WITHOUT SAFETY CHECK:                                                      │
│  ────────────────────                                                       │
│  idx_to_item_id[955]  →  KeyError! 💥 Program crashes                       │
│                                                                             │
│  WITH SAFETY CHECK:                                                         │
│  ──────────────────                                                         │
│  if 955 not in idx_to_item_id: continue  →  Skip silently ✅               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ❓ Common Questions & Answers

### Q1: Why pickle and not JSON?

| Pickle | JSON |
|--------|------|
| ✅ Can store Python objects (model) | ❌ Only basic types (dict, list, str) |
| ✅ Preserves numpy arrays | ❌ Arrays become lists |
| ✅ Fast to load | ⚠️ Slower parsing |
| ⚠️ Python-only | ✅ Language-agnostic |

### Q2: What happens with new users/items?

```
New user "NEW_USER_999" tries to get recommendations:

user_id_to_idx["NEW_USER_999"]  →  KeyError!

SOLUTIONS:
1. Return popular items as fallback
2. Use content-based recommendations
3. Retrain model periodically with new data
```

### Q3: Can I update the model without retraining?

**Short answer:** Not with ALS. The embeddings are fixed after training.

**Alternatives:**
- Schedule periodic retraining (daily/weekly)
- Use online learning algorithms (different from ALS)
- Hybrid: ALS for known users + rules for new users

### Q4: What does the score mean?

```
Recommendations for user USR_12345:
Product PROD_XYZ → score: 0.9542
Product PROD_ABC → score: 0.8721
Product PROD_DEF → score: 0.8103

INTERPRETATION:
• Higher score = Higher predicted interaction probability
• Scores are relative, not absolute probabilities
• Compare scores within the same user's recommendations
• DON'T compare scores across different users
```

---

## 🎓 Summary for Mentor Presentation

### The 30-Second Pitch

> "Our recommendation system uses **Alternating Least Squares (ALS)**, which learns hidden patterns from user-item interactions. Each user and item gets a numeric 'embedding' vector. To recommend items for a user, we find items whose embeddings are closest to the user's embedding. The entire trained model is saved as a pickle file for fast production inference."

### Key Takeaways

1. **ALS = Matrix Factorization** - Decomposes user-item matrix into user & item embeddings
2. **ID Mappings Required** - Model uses internal indices, we maintain bidirectional maps
3. **Safety Checks Matter** - Always verify indices exist before lookup
4. **Scores = Similarity** - Higher dot product = stronger match
5. **Static Model** - Must retrain to incorporate new users/items

---

## 📚 Further Reading

- [Implicit Library Documentation](https://benfred.github.io/implicit/)
- [Collaborative Filtering Explained](https://developers.google.com/machine-learning/recommendation/collaborative/basics)
- [ALS Algorithm Deep Dive](https://stanford.edu/~rezab/classes/cme323/S15/notes/lec14.pdf)

---

*Document generated for educational purposes. Good luck with your mentor presentation! 🚀*
