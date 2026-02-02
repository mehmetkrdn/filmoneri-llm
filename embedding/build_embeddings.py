import json
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import argparse
from pathlib import Path #gerekli kütüphaneler


def oku_jsonl(path:Path):
  with path.open("r",encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      yield json.loads(line)
      #jsonl okuma yaprız satır satır.



#embedding girecek metni alırız dhasonra sonuçları göstermek için title ve idyi metda saklarız
#hatalı kayıt vea boş doctexti atlarız
def text_ve_meta_yükle(jsonl_path:Path):
  #llm titles.jsonlde
  #text: embeddinge girecek doc_Text kısmı
  #meta: index ile series id title eşlesmesi

  texts = []
  meta = []

  for rec in oku_jsonl(jsonl_path):
    doc_text= (rec.get("doc_text") or "").strip()
    if not doc_text:
      continue

    series_id = rec.get("series_id")
    title = rec.get("title") or rec.get("original_title") or ""

    texts.append(doc_text)
    meta.append({
        "series_id": series_id,
        "title":title
    })
  return texts, meta



#embedding üretme yaparız metin. cosine similarity'de kullanılır(kosinüs benzerliği)
#metin listesini embedding matrisi ile sayısal vektörlere çeviririz. Karşılaştırma için

def build_embeddings(text,model_name:str, batch_size:int):
  model = SentenceTransformer(model_name)
  embeddings = model.encode(
      text, # Corrected: Changed 'texts' to 'text'
      batch_size=batch_size,
      show_progress_bar=True,
      convert_to_numpy=True,
      normalize_embeddings=True #cosine için pratik
  ).astype(np.float32)

  return embeddings

#kaydetme
# embedding.npy hızlı yüklenir daha az yer kaplar
#meta.json: bu embedding hangi diziye aitti sorunun cevabını verir

def save_outputs(embeddings: np.ndarray, meta:list, output_path:Path):
  output_path.mkdir(parents=True, exist_ok=True)

  emb_path = output_path / "embedding.npy"
  meta_path = output_path / "meta.json"

  np.save(emb_path, embeddings)

  with meta_path.open("w",encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

  print("saved:",emb_path)
  print("saved:", meta_path)
  print("embedding shape", embeddings.shape)

#main bloğu dosyalr nerede model hangisibatch kaç kontrolü
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="llme özel hali/llm_titles.jsonl", help="Input JSONL path")#dosya seçme
    parser.add_argument("--outdir", default="vector_store", help="Output folder (embeddings + meta)")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")#embedding modelimiz
    parser.add_argument("--batch_size", type=int, default=64, help="Encoding batch size") #embedding ayaları
    args = parser.parse_args(args=[]) # Fix: Pass an empty list to parse_args()

    infile = Path(args.infile)
    outdir = Path(args.outdir)

    texts, meta = text_ve_meta_yükle(infile) # Corrected function name
    print(f"Loaded texts: {len(texts)}")

    embeddings = build_embeddings(texts, args.model, args.batch_size)
    save_outputs(embeddings, meta, outdir)

if __name__ == "__main__":
    main()

