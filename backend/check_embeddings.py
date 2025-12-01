import pickle
import numpy as np

try:
    known_embeddings = pickle.load(open("embeddings.pkl", "rb"))
    print(f"Loaded {len(known_embeddings)} students from embeddings.pkl")
    for i, (reg_no, emb) in enumerate(known_embeddings.items(), start=1):
        print(f"{i}. Reg: {reg_no}, Embedding shape: {np.array(emb).shape}")
except Exception as e:
    print(f"Error loading embeddings: {e}")
