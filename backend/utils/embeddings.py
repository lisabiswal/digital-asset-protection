import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np
from PIL import Image
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, use_gpu: bool = False):
        """
        Initializes the MobileNetV2 model for embedding generation.
        """
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing EmbeddingGenerator on device: {self.device}")
        
        # Load pretrained MobileNetV2
        # Using weights=MobileNet_V2_Weights.IMAGENET1K_V1 for the newer API
        self.model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
        
        # Strip the classifier head to get the 1280-dim feature vector
        self.model.classifier = nn.Identity()
        self.model.to(self.device)
        self.model.eval()
        
        # Preprocessing transforms (ImageNet standards)
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

    def _l2_normalize(self, x: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(x)
        if norm == 0:
            return x
        return x / norm

    @torch.no_grad()
    def generate_embedding(self, frame: np.ndarray) -> np.ndarray:
        """
        Generates a 1280-dimensional L2-normalized embedding for a single frame.
        """
        # Convert numpy array (RGB) to PIL Image
        img = Image.fromarray(frame)
        
        # Preprocess and add batch dimension
        img_tensor = self.preprocess(img).unsqueeze(0).to(self.device)
        
        # Forward pass
        features = self.model(img_tensor)
        
        # Global Average Pooling is already done by MobileNetV2 features + Identity classifier
        # but we ensure it's flattened
        embedding = features.squeeze().cpu().numpy()
        
        # L2 Normalize for cosine similarity
        return self._l2_normalize(embedding)

    @torch.no_grad()
    def generate_embeddings_batch(self, frames: List[np.ndarray], batch_size: int = 16) -> np.ndarray:
        """
        Generates embeddings for a list of frames in batches.
        """
        all_embeddings = []
        
        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i : i + batch_size]
            batch_tensors = []
            
            for frame in batch_frames:
                img = Image.fromarray(frame)
                batch_tensors.append(self.preprocess(img))
            
            input_batch = torch.stack(batch_tensors).to(self.device)
            features = self.model(input_batch)
            
            # Flatten features
            batch_embeddings = features.cpu().numpy()
            
            # L2 Normalize each embedding in the batch
            for emb in batch_embeddings:
                all_embeddings.append(self._l2_normalize(emb))
        
        return np.array(all_embeddings)

# Singleton instance
_generator = None

def get_embedding_generator():
    global _generator
    if _generator is None:
        _generator = EmbeddingGenerator()
    return _generator

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    gen = get_embedding_generator()
    
    # Create a random dummy frame (RGB)
    dummy_frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    
    emb = gen.generate_embedding(dummy_frame)
    print(f"Embedding shape: {emb.shape}")
    print(f"Embedding L2 Norm: {np.linalg.norm(emb):.4f}")
    
    # Batch test
    dummy_frames = [dummy_frame] * 5
    embs = gen.generate_embeddings_batch(dummy_frames)
    print(f"Batch embeddings shape: {embs.shape}")
    print(f"First embedding L2 Norm: {np.linalg.norm(embs[0]):.4f}")
