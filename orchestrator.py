import json

import anthropic

from tools import get_semantic_scholar_abstract, search_crossref

client = anthropic.Anthropic()

MODEL = "claude-opus-4-8"

TOOLS = [
    {
        "name": "search_crossref",
        "description": (
            "Search CrossRef for an academic paper by title and optional author/year. "
            "Returns whether the paper exists and its metadata (DOI, authors, journal, year) if found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The paper's title"},
                "author": {"type": "string", "description": "An author's last name, optional"},
                "year": {"type": "string", "description": "Publication year, optional"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "get_semantic_scholar_abstract",
        "description": (
            "Fetch a paper's abstract from Semantic Scholar, given a DOI (preferred) or title. "
            "Returns the abstract text if available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doi": {"type": "string", "description": "The paper's DOI, if known"},
                "title": {"type": "string", "description": "The paper's title, used if DOI is not known"},
            },
        },
    },
]

SYSTEM_PROMPT = """You verify whether a claim is supported by a cited academic paper.

You have two tools:
- search_crossref: confirms the paper exists and returns its DOI and metadata
- get_semantic_scholar_abstract: fetches the paper's abstract

Process:
1. Call search_crossref to confirm the citation exists and get its DOI. The citation title
   alone is often not enough to find the right paper - CrossRef's search can be crowded out
   by other papers with similar-sounding titles. If your first search_crossref call comes
   back not found, and you can recall a plausible author surname for this paper from your
   own general knowledge, retry search_crossref once more with that author included before
   concluding the paper does not exist. This author guess is only a search aid to disambiguate
   candidates - it never counts as evidence about the paper's contents.
2. Call get_semantic_scholar_abstract (using the DOI if you have one) to get the abstract.
3. Judge whether the claim is supported by, contradicted by, or absent from the abstract text.

Base your judgment of the CLAIM only on the tool results returned to you. Never use your own
prior knowledge about the paper's contents to judge the claim - if the abstract isn't
available, say so rather than guessing. (The one exception is step 1: you may use your own
knowledge to guess an author name purely to improve search recall, never to judge the claim
itself.)

When you have gathered enough information, respond with ONLY a JSON object (no other text)
in this exact shape:
{"paper_found": true/false, "abstract_available": true/false, "claim_supported": "true"|"false"|"unclear", "reasoning": "one or two sentence explanation"}
"""


def _run_tool(name: str, tool_input: dict) -> dict:
    if name == "search_crossref":
        return search_crossref(tool_input.get("title"), tool_input.get("author"), tool_input.get("year"))
    if name == "get_semantic_scholar_abstract":
        return get_semantic_scholar_abstract(tool_input.get("doi"), tool_input.get("title"))
    return {"error": f"unknown tool {name}"}


def verify_claim(claim: str, citation: str) -> dict:
    messages = [{"role": "user", "content": f"Claim: {claim}\n\nCitation: {citation}"}]

    response = None
    for _ in range(6):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        except anthropic.APIError as e:
            return {"error": f"Claude API request failed: {e}"}

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(_run_tool(block.name, block.input)),
            }
            for block in response.content
            if block.type == "tool_use"
        ]
        messages.append({"role": "user", "content": tool_results})
    else:
        return {"error": "max iterations reached without a final verdict"}

    final_text = "".join(block.text for block in response.content if block.type == "text")
    try:
        return json.loads(final_text)
    except json.JSONDecodeError:
        return {"error": "could not parse verdict", "raw": final_text}
