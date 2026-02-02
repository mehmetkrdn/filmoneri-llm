# recommend.py
import json
import numpy as np
import argparse
from pathlib import Path
from sentence_transformers import SentenceTransformer

def resolve_store_dir(store_arg: str) -> Path:
    """
    Kullanıcı --store ile 'embedding' verirse:
      store_dir = ./embedding
    Kullanıcı yanlışlıkla '.' verirse:
      ./embedding varsa ona düşer.
    """
    p = Path(store_arg)

    # Eğer direkt klasör verilmişse kullan
    if p.exists() and p.is_dir():
        # İçinde embeddings.npy/meta.json yoksa ve p/embedding varsa ona geç
        if not (p / "embeddings.npy").exists() and (p / "embedding").is_dir():
            return p / "embedding"
        return p

    # Klasör yoksa ama current altında embedding varsa
    if (Path(".") / p).is_dir():
        p2 = Path(".") / p
        if not (p2 / "embeddings.npy").exists() and (p2 / "embedding").is_dir():
            return p2 / "embedding"
        return p2

    return p  # son çare (hata mesajı için)

def load_store(store_dir: Path):
    """
    store_dir klasörü içinde şu iki dosyayı arar:
      embeddings.npy
      meta.json
    """
    emb_path = store_dir / "embeddings.npy"
    meta_path = store_dir / "meta.json"

    if not emb_path.exists() or not meta_path.exists():
        tried = [
            str(emb_path),
            str(meta_path),
            str(store_dir / "embedding" / "embeddings.npy"),
            str(store_dir / "embedding" / "meta.json"),
        ]
        raise FileNotFoundError(
            "Embedding dosyaları bulunamadı.\n"
            f"Beklenen: {emb_path} ve {meta_path}\n"
            "Denediğim yollar:\n- " + "\n- ".join(tried)
        )

    embeddings = np.load(emb_path)  # (N, D)
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    if len(meta) != embeddings.shape[0]:
        raise ValueError(f"meta uzunluğu ({len(meta)}) embeddings satır sayısı ({embeddings.shape[0]}) ile eşleşmiyor.")

    return embeddings, meta

def topk_search(model, embeddings: np.ndarray, meta: list, query: str, k: int = 5):
    # query -> embedding
    q = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]  # (D,)

    # normalize olduğu için cosine similarity = dot product
    scores = embeddings @ q  # (N,)

    k = min(k, len(scores))
    top_idx = np.argpartition(-scores, kth=k-1)[:k]
    top_idx = top_idx[np.argsort(-scores[top_idx])]

    results = []
    for rank, idx in enumerate(top_idx, start=1):
        results.append({
            "rank": rank,
            "series_id": meta[idx].get("series_id"),
            "title": meta[idx].get("title"),
            "score": float(scores[idx]),
        })
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", default="embedding", help="embeddings.npy + meta.json klasörü (örn: embedding)")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")
    parser.add_argument("--query", required=True, help="User preference text")
    parser.add_argument("--k", type=int, default=5, help="Top K results")
    args = parser.parse_args()

    store_dir = resolve_store_dir(args.store)

    print("Store dir:", store_dir.resolve())
    embeddings, meta = load_store(store_dir)

    print("Embeddings shape:", embeddings.shape, "| Meta:", len(meta))

    model = SentenceTransformer(args.model)

    results = topk_search(model, embeddings, meta, args.query, args.k)
    for r in results:
        print(f"{r['rank']}) {r['title']} (id={r['series_id']}) score={r['score']:.4f}")

if __name__ == "__main__":
    main()
