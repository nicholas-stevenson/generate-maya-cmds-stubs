from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import List

import bs4
import httpx

# Base URL for the Maya Commands online documentation
DOCS_BASE_URL = "https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/Commands"
INDEX_URL = f"{DOCS_BASE_URL}/index_all.html"

# Max simultaneous in-flight requests. Autodesk's CDN handles this fine at 20;
# lower it if you start seeing 429s.
CONCURRENCY = 20

source_folder_path = os.getenv(
    "CMDS_STUBS_SOURCE_DIR", os.path.join(os.getcwd(), "source")
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def fetch_index(client: httpx.AsyncClient) -> List[str]:
    """Fetch the command index page and return a list of .html filenames."""
    response = await client.get(INDEX_URL, headers=HEADERS, follow_redirects=True)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    return [a["href"] for a in soup.find_all("a", href=True)]


async def fetch_page(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    filename: str,
    dest_path: str,
    progress: list,
    total: int,
) -> bool:
    """Download a single doc page to dest_path. Returns True if fetched, False if skipped."""
    if os.path.exists(dest_path):
        progress[0] += 1
        print(f"\r  {progress[0]}/{total} (skipped cached)", end="", flush=True)
        return False

    url = f"{DOCS_BASE_URL}/{filename}"
    async with semaphore:
        try:
            response = await client.get(url, headers=HEADERS, follow_redirects=True)
            response.raise_for_status()
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            progress[0] += 1
            print(f"\r  {progress[0]}/{total}", end="", flush=True)
            return True
        except httpx.HTTPStatusError as e:
            print(f"\n  Warning: HTTP {e.response.status_code} for {filename} — skipping")
            progress[0] += 1
            return False
        except Exception as e:
            print(f"\n  Warning: Failed to fetch {filename}: {e} — skipping")
            progress[0] += 1
            return False


async def do_it():
    if not os.path.exists(source_folder_path):
        os.makedirs(source_folder_path)

    print(f"Fetching command index from:\n  {INDEX_URL}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        filenames = await fetch_index(client)

    print(f"Found {len(filenames)} command pages.")

    already_cached = sum(
        1 for f in filenames
        if os.path.exists(os.path.join(source_folder_path, f))
    )
    to_fetch = len(filenames) - already_cached

    if to_fetch == 0:
        print(f"All {len(filenames)} pages already cached in: {source_folder_path}")
        print("Nothing to download. Run main.py to generate stubs.")
        return

    if already_cached:
        print(f"  {already_cached} already cached, {to_fetch} to download.")

    print(f"\nDownloading to: {source_folder_path}")
    print(f"  0/{len(filenames)}", end="", flush=True)

    semaphore = asyncio.Semaphore(CONCURRENCY)
    progress = [0]

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            fetch_page(
                client,
                semaphore,
                filename,
                os.path.join(source_folder_path, filename),
                progress,
                len(filenames),
            )
            for filename in filenames
        ]
        results = await asyncio.gather(*tasks)

    fetched = sum(1 for r in results if r)
    print(f"\n\nDone! Downloaded {fetched} new pages ({already_cached} were already cached).")
    print("Run main.py to generate stubs.")


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(do_it())
    end = time.perf_counter()
    print(f"Finished in {end - start:0.4f} seconds")
