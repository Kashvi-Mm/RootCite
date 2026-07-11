import difflib

import httpx

CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"


def _title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


TITLE_MATCH_THRESHOLD = 0.92


def search_crossref(title: str, author: str | None = None, year: str | None = None) -> dict:
    params = {"query.bibliographic": title, "rows": 5}
    if author:
        params["query.author"] = author
    if year:
        params["filter"] = f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31"

    try:
        resp = httpx.get(CROSSREF_API, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        return {"found": False, "error": f"CrossRef request failed: {e}"}

    items = resp.json().get("message", {}).get("items", [])

    best_item = None
    best_score = 0.0
    for item in items:
        item_title = item["title"][0] if item.get("title") else ""
        score = _title_similarity(title, item_title)
        if score > best_score:
            best_score = score
            best_item = item

    if best_item is None or best_score < TITLE_MATCH_THRESHOLD:
        return {"found": False}

    authors = [
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in best_item.get("author", [])
    ]
    date_parts = best_item.get("published", {}).get("date-parts", [[None]])

    return {
        "found": True,
        "title": best_item["title"][0] if best_item.get("title") else "",
        "authors": authors,
        "journal": (best_item.get("container-title") or [None])[0],
        "year": date_parts[0][0] if date_parts and date_parts[0] else None,
        "doi": best_item.get("DOI"),
        "url": best_item.get("URL"),
    }


def _semantic_scholar_failure(resp: httpx.Response) -> dict | None:
    if resp.status_code == 429:
        return {"found": False, "error": "Semantic Scholar rate limit exceeded, try again shortly"}
    if resp.status_code >= 500:
        return {"found": False, "error": f"Semantic Scholar server error ({resp.status_code})"}
    return None


def get_semantic_scholar_abstract(doi: str | None = None, title: str | None = None) -> dict:
    try:
        if doi:
            resp = httpx.get(
                f"{SEMANTIC_SCHOLAR_API}/DOI:{doi}",
                params={"fields": "title,abstract"},
                timeout=10.0,
            )
            failure = _semantic_scholar_failure(resp)
            if failure:
                return failure
            if resp.status_code == 200:
                data = resp.json()
                if data.get("abstract"):
                    return {"found": True, "abstract": data["abstract"], "title": data.get("title")}
            # non-200, non-error status (e.g. 404 DOI not found) falls through to title search

        if title:
            resp = httpx.get(
                f"{SEMANTIC_SCHOLAR_API}/search",
                params={"query": title, "fields": "title,abstract", "limit": 1},
                timeout=10.0,
            )
            failure = _semantic_scholar_failure(resp)
            if failure:
                return failure
            if resp.status_code == 200:
                results = resp.json().get("data", [])
                if results and results[0].get("abstract"):
                    return {
                        "found": True,
                        "abstract": results[0]["abstract"],
                        "title": results[0].get("title"),
                    }
    except httpx.HTTPError as e:
        return {"found": False, "error": f"Semantic Scholar request failed: {e}"}

    return {"found": False}
