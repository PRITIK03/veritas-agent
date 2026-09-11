import tiktoken

# Approximate — Gemini doesn't use tiktoken's exact tokenizer,
# this is a close-enough estimate for demo/logging purposes.
_encoder = tiktoken.get_encoding("cl100k_base")

# Gemini 2.0 Flash pricing (USD per 1M tokens) — informational only,
# actual calls run on the free tier so real spend is $0.
INPUT_COST_PER_M = 0.075
OUTPUT_COST_PER_M = 0.30

def count_tokens(text: str) -> int:
    return len(_encoder.encode(text or ""))

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    cost = (input_tokens / 1_000_000) * INPUT_COST_PER_M
    cost += (output_tokens / 1_000_000) * OUTPUT_COST_PER_M
    return round(cost, 6)