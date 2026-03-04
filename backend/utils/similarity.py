import numpy as np

def cosine_similarity_manual(vecA, vecB):
    """
    Manually compute cosine similarity using numpy.
    """
    vecA = np.array(vecA)
    vecB = np.array(vecB)
    
    if vecA.size == 0 or vecB.size == 0:
        return 0.0
        
    dot_product = np.dot(vecA, vecB)
    normA = np.linalg.norm(vecA)
    normB = np.linalg.norm(vecB)
    
    if normA == 0 or normB == 0:
        return 0.0
        
    return float(dot_product / (normA * normB))
