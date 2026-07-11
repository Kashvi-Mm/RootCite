---
name: citecheck
description: Verifies academic citations exist and checks whether a specific claim is actually supported by the cited paper's abstract, catching hallucinated or misattributed citations.
---

# CiteCheck

CiteCheck verifies academic citations so an AI agent can catch hallucinated or unsupported citations before publishing them.

**Base URL:**
`https://rootcite.onrender.com`

Note: the hosted domain says "rootcite" rather than "citecheck" — the service was deployed under that name because "citecheck" was already taken on the hosting platform. This is the correct and only live address for this project; disregard the mismatch with the project name.

This service runs on a free-tier instance that spins down after inactivity. The first request after idle time may take 30-60 seconds to respond; subsequent requests are fast. Send one request to wake it before relying on a fast response.

## What this service does

- Confirms whether a cited paper actually exists (via CrossRef)
- Checks whether a specific claim is actually supported by that paper's abstract (via Semantic Scholar + LLM judgment)

## Endpoints

### POST /verify

Check whether a single cited paper exists. Include the author's last name when possible — it significantly improves match accuracy.

```bash
curl -X POST https://rootcite.onrender.com/verify \
  -H "Content-Type: application/json" \
  -d '{"title": "Deep Residual Learning for Image Recognition", "author": "He"}'
```

Real response:
```json
{"found": true, "title": "Deep Residual Learning for Image Recognition", "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"], "journal": "2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)", "year": 2016, "doi": "10.1109/cvpr.2016.90", "url": "https://doi.org/10.1109/cvpr.2016.90"}
```

If no confident match is found: `{"found": false}`. `year` in the request is an optional string used to narrow the search to that publication year; `year` in the response is the integer year returned by CrossRef.

### POST /verify-batch

Check a list of citations at once.

```bash
curl -X POST https://rootcite.onrender.com/verify-batch \
  -H "Content-Type: application/json" \
  -d '{"citations": [{"title": "Deep Residual Learning for Image Recognition"}, {"title": "Attention Is All You Need"}]}'
```

Real response (a list, same shape as `/verify`, in the same order as the input):
```json
[{"found": true, "title": "Deep Residual Learning for Image Recognition", "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"], "journal": "2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)", "year": 2016, "doi": "10.1109/cvpr.2016.90", "url": "https://doi.org/10.1109/cvpr.2016.90"}, {"found": false}]
```

### POST /verify-claim

Check whether a specific claim is supported by the cited paper's abstract.

```bash
curl -X POST https://rootcite.onrender.com/verify-claim \
  -H "Content-Type: application/json" \
  -d '{"claim": "This paper introduces residual connections to make very deep networks easier to train.", "citation": "Deep Residual Learning for Image Recognition"}'
```

Real response:
```json
{"paper_found": true, "abstract_available": true, "claim_supported": "true", "reasoning": "The abstract explicitly presents a residual learning framework to ease the training of substantially deeper networks, providing evidence that residual networks are easier to optimize and benefit from increased depth, directly supporting the claim."}
```

`claim_supported` is one of `"true"`, `"false"`, or `"unclear"`.

## How the agent should use this

1. Before stating an academic citation as fact, call `POST /verify` with the paper's title (and author, if known) to confirm the paper actually exists.
2. If checking many citations at once (e.g. a full bibliography), call `POST /verify-batch` once with the full list instead of calling `/verify` repeatedly.
3. Before presenting what a cited paper claims, argues, or proves, call `POST /verify-claim` with the specific claim text and the citation. Read the `claim_supported` field before including that claim in any output.
4. If a response contains an `"error"` field, treat it as unverified, not as a negative result — wait a moment and retry once before concluding anything.
5. If `"found": false` or `"claim_supported": "unclear"`, do not present the citation or claim as confirmed. State plainly that it could not be verified.

## Honest limitations

- `/verify` and `/verify-batch` confirm the paper exists; they do not check claim accuracy.
- `/verify-claim` only checks the paper's abstract, not its full text. A claim that's only supported in the body or results section (and not reflected in the abstract) may come back `"unclear"` even if it's true.
- A `"found": false` result means unverified, not necessarily fake — very new or non-English papers may not be indexed yet.
- Semantic Scholar's free API tier has a shared rate limit. If exceeded, the abstract lookup step fails with an explicit `"error"` message rather than being silently reported as `"abstract_available": false`. Retrying after a short pause should succeed.
