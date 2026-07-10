# RootCite

A citation-verification service built for NANDAHack. It gives an AI agent a way to catch hallucinated or unsupported citations before publishing them — confirming a cited paper exists, and checking whether a specific claim is actually backed by that paper's abstract.

See [SKILL.md](./SKILL.md) for the agent-facing API spec (endpoints, request/response shapes, and honest limitations).

## How it works

- **`/verify`** and **`/verify-batch`** confirm a paper exists via [CrossRef](https://api.crossref.org) (free, no API key) and return its real metadata if found.
- **`/verify-claim`** runs a Claude tool-use loop: Claude decides when to call CrossRef (to confirm the paper and get its DOI) and [Semantic Scholar](https://api.semanticscholar.org) (to fetch the abstract), then judges — grounded only in the retrieved abstract, never its own prior knowledge — whether a claim is supported, contradicted, or unclear.

## Setup

```bash
cd RootCite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`/verify-claim` calls the Anthropic API, so you'll need an API key from [console.anthropic.com](https://console.anthropic.com):

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Run

```bash
uvicorn main:app --reload
```

Server starts at `http://127.0.0.1:8000`. Interactive test UI (Swagger docs) at `http://127.0.0.1:8000/docs`.

## Example requests

```bash
curl -X POST http://127.0.0.1:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"title": "Deep Residual Learning for Image Recognition", "author": "He"}'

curl -X POST http://127.0.0.1:8000/verify-claim \
  -H "Content-Type: application/json" \
  -d '{"claim": "This paper introduces residual connections to make very deep networks easier to train.", "citation": "Deep Residual Learning for Image Recognition"}'
```

## Limitations

- Existence checks favor precision over recall: a strict title-match threshold means some real papers (especially ones with generic or widely-riffed-on titles) may come back `"found": false` rather than risk confidently returning the wrong paper.
- Claim verification only checks the paper's **abstract**, not full text — a true claim only supported in the body or results section may still come back `"unclear"`.
- A `"found": false` or `"unclear"` result means *unverified*, not necessarily *false*.
