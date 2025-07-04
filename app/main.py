import os
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import openai
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session, engine
from .models import Base, RunRecord
from .costs import estimate_cost

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

class RunRequest(BaseModel):
    system_prompt: str = ""
    user_prompt: str
    models: List[str]
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 256
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/api/run")
async def run_prompt(req: RunRequest, session: AsyncSession = Depends(get_session)):
    if not openai.api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY not set")
    results: Dict[str, Any] = {}
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cost = 0.0

    for model in req.models:
        try:
            response = await openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": req.system_prompt},
                    {"role": "user", "content": req.user_prompt},
                ],
                temperature=req.temperature,
                top_p=req.top_p,
                max_tokens=req.max_tokens,
                frequency_penalty=req.frequency_penalty,
                presence_penalty=req.presence_penalty,
            )
        except Exception as e:
            results[model] = {"error": str(e)}
            continue

        choice = response.choices[0]
        results[model] = choice.message.content
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        total_cost += estimate_cost(model, prompt_tokens, completion_tokens)

    record = RunRecord(
        timestamp=datetime.utcnow(),
        system_prompt=req.system_prompt,
        user_prompt=req.user_prompt,
        models=",".join(req.models),
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        frequency_penalty=req.frequency_penalty,
        presence_penalty=req.presence_penalty,
        results=results,
        input_tokens=total_prompt_tokens,
        output_tokens=total_completion_tokens,
        cost=total_cost,
    )
    session.add(record)
    await session.commit()

    return {
        "results": results,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "cost": total_cost,
    }


@app.get("/api/history")
async def get_history(session: AsyncSession = Depends(get_session)):
    res = await session.execute(RunRecord.__table__.select().order_by(RunRecord.id.desc()).limit(20))
    rows = res.fetchall()
    history = []
    for row in rows:
        r = row._mapping
        history.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "models": r["models"],
            "system_prompt": r["system_prompt"],
            "user_prompt": r["user_prompt"],
            "results": r["results"],
            "input_tokens": r["input_tokens"],
            "output_tokens": r["output_tokens"],
            "cost": r["cost"],
        })
    return history
