"""
FastAPI REST API for Market Opportunity Detector.

Run with: uvicorn api.main:app --reload
"""

from fastapi import FastAPI
from api.queries import get_categories, get_opportunities, get_keyword_history

app = FastAPI(title="Market Opportunity Detector")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/categories")
def list_categories():
    return get_categories()


@app.get("/opportunities")
def list_opportunities(limit: int = 20):
    return get_opportunities(limit)


@app.get("/keywords/{keyword}/history")
def keyword_history(keyword: str):
    return get_keyword_history(keyword)
