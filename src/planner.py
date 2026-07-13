"""LLM waypoint planner: assembles the system prompt from the map, sends one
command, returns the parsed plan plus timing. Provider-agnostic (OpenAI or
Anthropic) so the dissertation can compare models with zero code changes."""

import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "map" / "warehouse_map.json"
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v1")
PROMPT_PATH = ROOT / "prompts" / f"system_prompt_{PROMPT_VERSION}.md"

PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini" if PROVIDER == "openai" else "claude-haiku-4-5-20251001")


def build_system_prompt() -> str:
    md = PROMPT_PATH.read_text(encoding="utf-8")
    # Everything above the first --- is design commentary, not prompt content.
    prompt = md.split("---", 1)[1].strip()
    map_json = json.dumps(json.loads(MAP_PATH.read_text(encoding="utf-8")), indent=2)
    return prompt.replace("{MAP_JSON}", map_json)


def plan_command(command: str, system_prompt: str | None = None) -> dict:
    """Returns {'raw': str, 'plan': dict|None, 'parse_error': str|None, 'latency_s': float}."""
    system_prompt = system_prompt or build_system_prompt()
    t0 = time.perf_counter()

    if PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command},
            ],
        )
        raw = resp.choices[0].message.content or ""
    elif PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": command}],
        )
        raw = resp.content[0].text
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")

    latency = time.perf_counter() - t0

    plan, parse_error = None, None
    try:
        text = raw.strip()
        if text.startswith("```"):  # tolerate fenced output; log it as a deviation
            text = text.strip("`").lstrip("json").strip()
        plan = json.loads(text)
    except json.JSONDecodeError as e:
        parse_error = str(e)

    return {"raw": raw, "plan": plan, "parse_error": parse_error, "latency_s": round(latency, 3)}


if __name__ == "__main__":
    import sys
    cmd = " ".join(sys.argv[1:]) or "Go to the loading dock"
    result = plan_command(cmd)
    print(f"[{PROVIDER}/{MODEL}] {result['latency_s']}s")
    print(json.dumps(result["plan"], indent=2) if result["plan"] else f"PARSE ERROR: {result['parse_error']}\n{result['raw']}")
