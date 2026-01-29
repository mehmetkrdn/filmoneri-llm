# Amaç: Dosyayı llm modeline uygun jsonl yapısına getirmek. 
# Her satır = 1 diziyi temsil eder. + dizinin dağınık bilgilerini tek anlamlı bilgiye getiririz->doc_text" (embeddingee girecek metin)

import json
import argparse

def clean_list(x):
    """None/boşları temizler, string listesine çevir."""
    if not x:
        return []
    out = []
    for v in x:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            out.append(s)
    return out

def build_doc_text(rec: dict) -> str:
    """
    LLM + embedding için tek metin üretir.
    Mantık: (başlık) + (kısa özet) + (türler) + (keywords) + (cast) + (sezon/bölüm)
    """
    title = (rec.get("title") or rec.get("original_title") or "").strip()
    overview = (rec.get("overview") or "").strip()
    tagline = (rec.get("tagline") or "").strip()

    genres = clean_list(rec.get("genres"))
    keywords = clean_list(rec.get("keywords"))
    cast_top = clean_list(rec.get("cast_top"))
    creators = clean_list(rec.get("creators"))

    seasons = rec.get("seasons_count")
    episodes = rec.get("episodes_count")
    runtime = rec.get("runtime_avg_minutes")

    parts = []

    # 1) Başlık
    if title:
        parts.append(f"Title: {title}")

    # 2) Tagline + Overview
    if tagline:
        parts.append(f"Tagline: {tagline}")
    if overview:
        parts.append(f"Overview: {overview}")

    # 3) Tür
    if genres:
        parts.append("Genres: " + ", ".join(genres))
    if keywords:
        parts.append("Keywords: " + ", ".join(keywords))

    # 4) Aktörler
    if creators:
        parts.append("Creators: " + ", ".join(creators))
    if cast_top:
        parts.append("Cast: " + ", ".join(cast_top[:10]))

    # 5) Sayısal bağlam (LLM’e yardımcı olur)
    extra = []
    if isinstance(seasons, int):
        extra.append(f"seasons={seasons}")
    if isinstance(episodes, int):
        extra.append(f"episodes={episodes}")
    if isinstance(runtime, int):
        extra.append(f"runtime_avg_minutes={runtime}")
    if extra:
        parts.append("Info: " + ", ".join(extra))

    return "\n".join(parts).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="zenginleştirilmiş llm/titles_enriched.jsonl")
    parser.add_argument("--outfile", default="llm_titles.jsonl")
    args = parser.parse_args()

    n_in = 0
    n_out = 0

    with open(args.infile, "r", encoding="utf-8") as f_in, \
         open(args.outfile, "w", encoding="utf-8") as f_out:

        for line in f_in:
            line = line.strip()
            if not line:
                continue

            n_in += 1
            rec = json.loads(line)

            # enrich script hata satırı yazmış olabilir: {"series_id":..., "error": "..."}
            if rec.get("error"):
                continue

            series_id = rec.get("series_id")
            if not isinstance(series_id, int):
                continue

            # İstenen JSONL yapısı: her satır 1 dizi + doc_text
            out = {
                "series_id": series_id,
                "title": rec.get("title"),
                "overview": rec.get("overview"),
                "genres": clean_list(rec.get("genres")),
                "keywords": clean_list(rec.get("keywords")),
                "cast_top": clean_list(rec.get("cast_top")),
                "creators": clean_list(rec.get("creators")),
                "year": rec.get("year"),
                "seasons_count": rec.get("seasons_count"),
                "episodes_count": rec.get("episodes_count"),
                "runtime_avg_minutes": rec.get("runtime_avg_minutes"),
                "vote_average": rec.get("vote_average"),
                "vote_count": rec.get("vote_count"),
                "popularity": rec.get("popularity"),
                "original_language": rec.get("original_language"),
                "origin_country": rec.get("origin_country") or [],
                "poster_url_w500": rec.get("poster_url_w500"),
                "backdrop_url_w780": rec.get("backdrop_url_w780"),
            }

            out["doc_text"] = build_doc_text(out)

            f_out.write(json.dumps(out, ensure_ascii=False) + "\n")
            n_out += 1

    print(f"Input lines read: {n_in}")
    print(f"Output lines written: {n_out}")
    print(f"Saved: {args.outfile}")

if __name__ == "__main__":
    main()
