from sentence_transformers import SentenceTransformer

QUERY_PREFIX="Represent this sentence for searching relevant passages: "

class Embedder:
    def __init__(self,model_name:str):
        self.model=SentenceTransformer(model_name)

    def embed_documents(self,texts:list[str],batch_size:int=32) -> list[list[float]]:
        vectors=self.model.encode(texts,batch_size=batch_size,normalize_embeddings=True,show_progress_bar=True)
        return vectors.tolist()

    def embed_query(self,text:str) -> list[float]:
        vector=self.model.encode(QUERY_PREFIX+text,normalize_embeddings=True)
        return vector.tolist()