from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from orchestrator import verify_claim
from tools import search_crossref

app = FastAPI(title="RootCite")


class VerifyRequest(BaseModel):
    title: str
    author: Optional[str] = None
    year: Optional[str] = None


class VerifyBatchRequest(BaseModel):
    citations: List[VerifyRequest]


class VerifyClaimRequest(BaseModel):
    claim: str
    citation: str


@app.post("/verify")
def verify(req: VerifyRequest):
    return search_crossref(req.title, req.author, req.year)


@app.post("/verify-batch")
def verify_batch(req: VerifyBatchRequest):
    return [search_crossref(c.title, c.author, c.year) for c in req.citations]


@app.post("/verify-claim")
def verify_claim_endpoint(req: VerifyClaimRequest):
    return verify_claim(req.claim, req.citation)
