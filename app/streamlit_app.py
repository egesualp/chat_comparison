import os
from datetime import datetime
import json

import streamlit as st
import openai
from sqlalchemy.orm import sessionmaker

from .database import engine
from .models import Base, RunRecord
from .costs import estimate_cost

# initialize DB
Base.metadata.create_all(engine.sync_engine)
SessionLocal = sessionmaker(bind=engine.sync_engine)

st.title("Chat Comparison")

api_key = st.text_input("OpenAI API Key", type="password")
if api_key:
    openai.api_key = api_key
else:
    openai.api_key = os.getenv("OPENAI_API_KEY", "")

system_prompt = st.text_area("System Prompt", value="")
user_prompt = st.text_area("User Prompt", value="")

models = st.multiselect(
    "Models",
    ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
    default=["gpt-3.5-turbo"],
)

temperature = st.slider("Temperature", 0.0, 2.0, 1.0, 0.1)
top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05)
max_tokens = st.slider("Max Tokens", 1, 4096, 256)
frequency_penalty = st.slider("Frequency Penalty", -2.0, 2.0, 0.0, 0.1)
presence_penalty = st.slider("Presence Penalty", -2.0, 2.0, 0.0, 0.1)

run_clicked = st.button("Run")

if run_clicked:
    if not openai.api_key:
        st.error("No OpenAI API key provided.")
    elif not models:
        st.error("Select at least one model.")
    else:
        results = {}
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        for model in models:
            try:
                response = openai.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                )
                message = response.choices[0].message.content
                usage = response.usage
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                cost = estimate_cost(model, prompt_tokens, completion_tokens)
                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens
                total_cost += cost
                results[model] = {
                    "text": message,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": cost,
                }
            except Exception as e:
                results[model] = {"error": str(e)}

        with SessionLocal() as session:
            record = RunRecord(
                timestamp=datetime.utcnow(),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                models=",".join(models),
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                results={m: r.get("text", r.get("error")) for m, r in results.items()},
                input_tokens=total_prompt_tokens,
                output_tokens=total_completion_tokens,
                cost=total_cost,
            )
            session.add(record)
            session.commit()

        st.write(
            f"Prompt tokens: {total_prompt_tokens}  Completion tokens: {total_completion_tokens}  Estimated cost: ${total_cost:.5f}"
        )

        cols = st.columns(len(models))
        for (model, data), col in zip(results.items(), cols):
            with col:
                st.subheader(model)
                if "error" in data:
                    st.error(data["error"])
                else:
                    st.write(data["text"])
                    st.caption(
                        f"Tokens: {data['prompt_tokens']} + {data['completion_tokens']}  Cost: ${data['cost']:.5f}"
                    )

st.markdown("---")
with st.expander("History (last 20 runs)"):
    with SessionLocal() as session:
        rows = session.query(RunRecord).order_by(RunRecord.id.desc()).limit(20).all()
        for run in rows:
            with st.expander(f"{run.timestamp} | models: {run.models} | cost: ${run.cost:.5f}"):
                st.write(run.user_prompt)
                for m, text in run.results.items():
                    st.write(f"### {m}")
                    st.write(text)

