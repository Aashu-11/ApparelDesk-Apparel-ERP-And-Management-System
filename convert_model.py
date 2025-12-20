"""Convert implicit model to numpy-only format - FIXED version."""
import pickle
import numpy as np

# Load old model backup (need to redo from WSL)
print("This script needs to be run in WSL where implicit is installed.")
print("Run: python3 convert_model.py")
print()

try:
    with open('models/recommender_v1.pkl', 'rb') as f:
        data = pickle.load(f)
    
    # Check if already converted or still has model object
    if 'model' in data:
        model = data['model']
        
        # In implicit, user_factors shape is (n_users, factors)
        # and item_factors shape is (n_items, factors)
        user_factors = np.array(model.user_factors)
        item_factors = np.array(model.item_factors)
        
        print(f'Original user_factors shape: {user_factors.shape}')
        print(f'Original item_factors shape: {item_factors.shape}')
        print(f'Number of users in mapping: {len(data["user_id_to_idx"])}')
        print(f'Number of items in mapping: {len(data["item_id_to_idx"])}')
        
        # Verify shapes match mappings
        n_users = len(data["user_id_to_idx"])
        n_items = len(data["item_id_to_idx"])
        
        # If shapes are swapped, fix them
        if user_factors.shape[0] == n_items and item_factors.shape[0] == n_users:
            print("\nDetected swapped factors - fixing...")
            user_factors, item_factors = item_factors, user_factors
        
        print(f'\nFinal user_factors shape: {user_factors.shape}')
        print(f'Final item_factors shape: {item_factors.shape}')
        
        # Create new model with just numpy arrays
        new_data = {
            'user_factors': user_factors,
            'item_factors': item_factors,
            'user_id_to_idx': data['user_id_to_idx'],
            'idx_to_user_id': data['idx_to_user_id'],
            'item_id_to_idx': data['item_id_to_idx'],
            'idx_to_item_id': data['idx_to_item_id'],
            'config': data.get('config', {}),
            'metadata': data.get('metadata', {})
        }
        
        # Save new model
        with open('models/recommender_v1.pkl', 'wb') as f:
            pickle.dump(new_data, f)
        
        print('\nModel converted and saved! No implicit library needed anymore.')
    else:
        # Already converted - just swap the factors
        print("Model already converted to numpy format.")
        
        user_factors = data['user_factors']
        item_factors = data['item_factors']
        n_users = len(data["user_id_to_idx"])
        n_items = len(data["item_id_to_idx"])
        
        print(f'Current user_factors shape: {user_factors.shape}')
        print(f'Current item_factors shape: {item_factors.shape}')
        print(f'Number of users: {n_users}')
        print(f'Number of items: {n_items}')
        
        # Swap if needed
        if user_factors.shape[0] != n_users:
            print("\nSwapping factors...")
            data['user_factors'], data['item_factors'] = data['item_factors'], data['user_factors']
            
            with open('models/recommender_v1.pkl', 'wb') as f:
                pickle.dump(data, f)
            
            print("Fixed! user_factors now has correct shape.")
        else:
            print("\nShapes are already correct.")

except Exception as e:
    print(f"Error: {e}")
