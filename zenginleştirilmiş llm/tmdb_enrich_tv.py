import os
import json
import time
import argparse
from typing import Dict, Any, Optional

import requests
from tqdm import tqdm
from dotenv import load_dotenv
from pathlib import Path

TMDB_API_BASE = "https://api.themoviedb.org/3"

def load_env():
    # Windows/VS Code için garanti .env okuma
    load_dotenv(Path(__file__).with_name(".env"))

def tmdb_headers() -> Dict[str, str]:
    bearer = os.getenv("TMDB_BEARER")
    headers = {"accept": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    return headers

def tmdb_get(path: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5) -> Dict[str, Any]:
    url = f"{TMDB_API_BASE}{path}"
    headers = tmdb_headers()
    params = params or {}

    api_key = os.getenv("TMDB_API_KEY")
    if api_key and "Authorization" not in headers:
        params["api_key"] = api_key

    backoff = 1.0
    for _ in range(max_retries):
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else backoff)
            backoff = min(backoff * 2, 30)
            continue

        if r.status_code in (500, 502, 503, 504):
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue

        # fatal
        try:
            err = r.json()
        except Exception:
            err = {"raw": r.text[:300]}
        raise RuntimeError(f"TMDB error {r.status_code}: {err}")

    raise RuntimeError("Max retries exceeded")

def build_image_url(file_path: Optional[str], size: str = "w500") -> Optional[str]:
    if not file_path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{file_path}"

def safe_int(x, default=None):
    try:
        return int(x)
    except Exception:
        return default

def enrich_one(series_id: int, language: str, include_credits: bool) -> Dict[str, Any]:
    # details
    details = tmdb_get(f"/tv/{series_id}", params={"language": language})

    # keywords (language paramı yok, TMDB keywordler sabit)
    kw = tmdb_get(f"/tv/{series_id}/keywords")
    keywords = [k.get("name") for k in kw.get("results", []) if k.get("name")]

    cast_top = []
    creators = []

    if include_credits:
        credits = tmdb_get(f"/tv/{series_id}/credits", params={"language": language})
        cast = credits.get("cast", []) or []
        cast_top = [c.get("name") for c in cast[:10] if c.get("name")]

        # creators aslında /tv/{id} içinde created_by olarak da var
        # yine de burada da crew üzerinden kontrol edebiliriz (opsiyonel)
        # biz details.created_by'ı esas alacağız
    created_by = details.get("created_by") or []
    creators = [p.get("name") for p in created_by if p.get("name")]

    genres = [g.get("name") for g in (details.get("genres") or []) if g.get("name")]
    networks = [n.get("name") for n in (details.get("networks") or []) if n.get("name")]

    # episode_run_time list gelebilir (örn [45])
    run_times = details.get("episode_run_time") or []
    runtime_avg = run_times[0] if run_times else None

    enriched = {
        "series_id": series_id,

        # titles & text
        "title": details.get("name"),
        "original_title": details.get("original_name"),
        "overview": details.get("overview"),
        "tagline": details.get("tagline"),

        # taxonomy
        "genres": genres,
        "keywords": keywords,

        # people
        "cast_top": cast_top,
        "creators": creators,

        # dates & counts
        "first_air_date": details.get("first_air_date"),
        "last_air_date": details.get("last_air_date"),
        "year": (details.get("first_air_date") or "")[:4] or None,
        "seasons_count": details.get("number_of_seasons"),
        "episodes_count": details.get("number_of_episodes"),
        "runtime_avg_minutes": runtime_avg,

        # status
        "status": details.get("status"),  # Ended / Returning Series vb.
        "in_production": details.get("in_production"),

        # language & country
        "original_language": details.get("original_language"),
        "origin_country": details.get("origin_country") or [],

        # networks
        "networks": networks,

        # ratings
        "vote_average": details.get("vote_average"),
        "vote_count": details.get("vote_count"),
        "popularity": details.get("popularity"),

        # images
        "poster_path": details.get("poster_path"),
        "backdrop_path": details.get("backdrop_path"),
        "poster_url_w500": build_image_url(details.get("poster_path"), "w500"),
        "backdrop_url_w780": build_image_url(details.get("backdrop_path"), "w780"),

        # bookkeeping
        "source": "tmdb_tv_details+keywords" + ("+credits" if include_credits else ""),
    }

    return enriched

def main():
    load_env()

    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="data/titles_raw.jsonl", help="Input JSONL (from discover)")
    parser.add_argument("--outfile", default="titles_enriched.jsonl", help="Output JSONL")
    parser.add_argument("--language", default="tr-TR", help="Language for /tv/{id}")
    parser.add_argument("--sleep", type=float, default=0.25, help="Sleep between requests")
    parser.add_argument("--include_credits", action="store_true", help="Also call /credits for cast")
    parser.add_argument("--start", type=int, default=0, help="Start line index (0-based)")
    parser.add_argument("--limit", type=int, default=0, help="Limit how many items to process (0=all)")
    args = parser.parse_args()

    if not os.getenv("TMDB_BEARER") and not os.getenv("TMDB_API_KEY"):
        raise SystemExit("TMDB_BEARER veya TMDB_API_KEY yok. .env kontrol et.")

    # input read
    items = []
    with open(args.infile, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                sid = safe_int(obj.get("series_id") or obj.get("id"))
                if sid is not None:
                    items.append(sid)
            except json.JSONDecodeError:
                continue

    # slice
    if args.start > 0:
        items = items[args.start:]
    if args.limit and args.limit > 0:
        items = items[:args.limit]

    # skip already enriched ids (resume)
    done = set()
    if os.path.exists(args.outfile):
        with open(args.outfile, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    sid = obj.get("series_id")
                    if isinstance(sid, int):
                        done.add(sid)
                except json.JSONDecodeError:
                    continue

    with open(args.outfile, "a", encoding="utf-8") as f_out:
        for sid in tqdm(items, desc="Enrich TV"):
            if sid in done:
                continue

            try:
                rec = enrich_one(sid, args.language, args.include_credits)
                f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                done.add(sid)
            except Exception as e:
                # hatalı id'leri atla (logla)
                err = {"series_id": sid, "error": str(e)}
                f_out.write(json.dumps(err, ensure_ascii=False) + "\n")

            time.sleep(args.sleep)

    print(f"Done. Enriched lines: {len(done)}")
    print(f"Output: {args.outfile}")

if __name__ == "__main__":
    main()
