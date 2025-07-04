COSTS = {
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
}

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    info = COSTS.get(model, {"prompt": 0, "completion": 0})
    return (prompt_tokens * info["prompt"] + completion_tokens * info["completion"]) / 1000
