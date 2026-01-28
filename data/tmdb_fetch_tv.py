import os
import json
import time
import argparse
from typing import Dict, Any, Optional, Set

import requests
from tqdm import tqdm
from dotenv import load_dotenv

TMDB_API_BASE = "https://api.themoviedb.org/3"

def tmdb_headers() -> Dict[str, str]:
    """
    Prefer Bearer token (recommended). If not present, fall back to api_key query param.
    """
    bearer = os.getenv("TMDB_BEARER")
    headers = {"accept": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    return headers

def tmdb_get(path: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5) -> Dict[str, Any]:
    """
    Simple retry with exponential backoff + basic 429 handling.
    """
    url = f"{TMDB_API_BASE}{path}"
    headers = tmdb_headers()
    params = params or {}

    api_key = os.getenv("TMDB_API_KEY")
    if api_key and "Authorization" not in headers:
        params["api_key"] = api_key

    backoff = 1.0
    for attempt in range(max_retries):
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()

        # rate limit
        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            sleep_s = float(retry_after) if retry_after else backoff
            time.sleep(sleep_s)
            backoff = min(backoff * 2, 30)
            continue

        # transient
        if r.status_code in (500, 502, 503, 504):
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue

        # fatal
        raise RuntimeError(f"TMDB error {r.status_code}: {r.text[:300]}")

    raise RuntimeError("Max retries exceeded")

def load_existing_ids(jsonl_path: str) -> Set[int]:
    if not os.path.exists(jsonl_path):
        return set()
    ids = set()
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                sid = obj.get("series_id")
                if isinstance(sid, int):
                    ids.add(sid)
            except json.JSONDecodeError:
                continue
    return ids

def build_image_url(file_path: Optional[str], size: str = "w500") -> Optional[str]:
    """
    Simple public base. (TMDB also provides configuration endpoint to list sizes,
    but this is enough for most projects.)
    """
    if not file_path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{file_path}"

def fetch_discover_page(page: int, language: str, sort_by: str, min_votes: int) -> Dict[str, Any]:
    params = {
        "page": page,
        "language": language,
        "sort_by": sort_by,
        "vote_count.gte": min_votes,
        "include_null_first_air_dates": "false",
    }
    return tmdb_get("/discover/tv", params=params)

def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="titles_raw.jsonl", help="Output JSONL path")
    parser.add_argument("--max_pages", type=int, default=100, help="How many pages to pull")
    parser.add_argument("--language", default="tr-TR", help="TMDB language (e.g. tr-TR, en-US)")
    parser.add_argument("--sort_by", default="popularity.desc", help="TMDB sort_by")
    parser.add_argument("--min_votes", type=int, default=50, help="Minimum vote_count threshold")
    parser.add_argument("--sleep", type=float, default=0.25, help="Sleep between requests (seconds)")
    args = parser.parse_args()

    if not os.getenv("TMDB_BEARER") and not os.getenv("TMDB_API_KEY"):
        raise SystemExit("TMDB_BEARER veya TMDB_API_KEY tanımla (.env içine).")

    existing = load_existing_ids(args.out)
    print(f"Existing records: {len(existing)}")

    with open(args.out, "a", encoding="utf-8") as f_out:
        for page in tqdm(range(1, args.max_pages + 1), desc="Discover TV pages"):
            data = fetch_discover_page(page, args.language, args.sort_by, args.min_votes)
            results = data.get("results", [])

            for item in results:
                sid = item.get("id")
                if not isinstance(sid, int) or sid in existing:
                    continue

                record = {
                    "series_id": sid,
                    "title": item.get("name"),
                    "original_title": item.get("original_name"),
                    "overview": item.get("overview"),
                    "first_air_date": item.get("first_air_date"),
                    "genre_ids": item.get("genre_ids") or [],
                    "popularity": item.get("popularity"),
                    "vote_average": item.get("vote_average"),
                    "vote_count": item.get("vote_count"),
                    "origin_country": item.get("origin_country") or [],
                    "original_language": item.get("original_language"),
                    "poster_path": item.get("poster_path"),
                    "backdrop_path": item.get("backdrop_path"),
                    "poster_url_w500": build_image_url(item.get("poster_path"), "w500"),
                    "backdrop_url_w780": build_image_url(item.get("backdrop_path"), "w780"),
                    "source": "tmdb_discover_tv",
                }

                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                existing.add(sid)

            time.sleep(args.sleep)

    print(f"Done. Total records now: {len(existing)}")
    print(f"Output: {args.out}")

if __name__ == "__main__":
    main()
