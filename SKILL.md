# CiteCheck

CiteCheck verifies academic citations so an AI agent can catch hallucinated or unsupported citations before publishing them.

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
{"title": "paper title", "author": "optional author last name", "year": "optional year"}
```

Response:
```json
{"found": true, "title": "...", "authors": ["..."], "journal": "...", "year": 2020, "doi": "...", "url": "..."}
```
or
```json
{"found": false}
```

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

## Honest limitations

- `/verify` and `/verify-batch` confirm the paper exists; they do not check claim accuracy.
- `/verify-claim` only checks the paper's abstract, not its full text. A claim that's only supported in the body or results section (and not reflected in the abstract) may come back `"unclear"` even if it's true.
- A `"found": false` result means unverified, not necessarily fake — very new or non-English papers may not be indexed yet.
