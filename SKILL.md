---
name: rootcite
description: Verifies academic citations exist and checks whether a specific claim is actually supported by the cited paper's abstract, catching hallucinated or misattributed citations.
---

# RootCite

RootCite verifies academic citations so an AI agent can catch hallucinated or unsupported citations before publishing them.

**Base URL:** `https://rootcite.onrender.com`

Note: this runs on a free-tier instance that spins down after inactivity. The first request after idle time may take up to ~50 seconds to respond; subsequent requests are fast.

## What this service does

- Confirms whether a cited paper actually exists (via CrossRef)
- Checks whether a specific claim is actually supported by that paper's abstract (via Semantic Scholar + LLM judgment)

## When to use this

Call this before including any academic citation or claim-with-citation in a piece of writing, report, or research output. Use it as a self-check step to avoid presenting a fabricated or misattributed citation as fact.

## Endpoints

### POST /verify

Check whether a single cited paper exists.

Request body:
```json
{"title": "paper title", "author": "optional author last name", "year": "optional year, e.g. \"2016\""}
```

Response:
```json
{"found": true, "title": "...", "authors": ["..."], "journal": "...", "year": 2020, "doi": "...", "url": "..."}
```
or
```json
{"found": false}
```

Note: `year` in the request is a string used to narrow the search to that publication year; `year` in the response is the integer year returned by CrossRef.

### POST /verify-batch

Check a list of citations at once.

Request body:
```json
{"citations": [{"title": "..."}, {"title": "...", "author": "..."}]}
```

Response: a list of results in the same shape as `/verify`, in the same order as the input list.

### POST /verify-claim

Check whether a specific claim is supported by the cited paper's abstract.

Request body:
```json
{"claim": "the paper argues that X causes Y", "citation": "paper title or DOI"}
```

Response:
```json
{"paper_found": true, "abstract_available": true, "claim_supported": "true", "reasoning": "..."}
```

`claim_supported` is one of `"true"`, `"false"`, or `"unclear"`.

## Errors

If an upstream API (CrossRef, Semantic Scholar, or Claude) fails or times out, endpoints return a 200 response with an honest failure shape rather than a raw 500:

- `/verify` and `/verify-batch`: `{"found": false, "error": "description of what failed"}`
- `/verify-claim`: `{"error": "description of what failed"}`

Treat any response containing an `"error"` field as unverified, not as a negative result.

## Honest limitations

- `/verify` and `/verify-batch` confirm the paper exists; they do not check claim accuracy.
- `/verify-claim` only checks the paper's abstract, not its full text. A claim that's only supported in the body or results section (and not reflected in the abstract) may come back `"unclear"` even if it's true.
- A `"found": false` result means unverified, not necessarily fake — very new or non-English papers may not be indexed yet.
