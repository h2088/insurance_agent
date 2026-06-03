import anthropic
import json
import sys
import time
from datetime import datetime

from insurance_agent_tools import tools, execute_function_call

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

client = anthropic.Anthropic()

COMPRESS_THRESHOLD = 8

GREY_BG = "\033[48;5;252m\033[38;5;17m"
RESET = "\033[0m"


def _serialize_messages(messages):
    lines = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            lines.append(f"[{role}]: {content}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        lines.append(f"[{role} (tool_result id={block['tool_use_id']})]: {block['content']}")
                else:
                    if block.type == "text":
                        lines.append(f"[{role}]: {block.text}")
                    elif block.type == "tool_use":
                        lines.append(f"  -> tool_use (id={block.id}): {block.name}({json.dumps(block.input)})")
    return "\n".join(lines)


def summarize_messages(client, messages_to_summarize):
    conversation_text = _serialize_messages(messages_to_summarize)
    prompt = (
        "Summarize the following conversation concisely. "
        "Preserve key facts such as customer needs, compared products, quotes, eligibility results, and decisions.\n\n"
        f"{conversation_text}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def print_context_window(system, messages):
    print(f"\n{GREY_BG}--- Context window ({len(messages) + 1} messages) ---{RESET}")
    for t in tools:
        params = list(t["input_schema"].get("properties", {}).keys())
        required = t["input_schema"].get("required", [])
        param_str = ", ".join(f"{p}{'*' if p in required else '?' }" for p in params)
        print(f"{GREY_BG}[function_call_definition] {t['name']}({param_str}) — {t['description']}{RESET}")
    print(f"{GREY_BG}[system]: {system}{RESET}")
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            print(f"{GREY_BG}[{role}]: {content}{RESET}")
        elif isinstance(content, list):
            has_text = any(not isinstance(b, dict) and b.type == "text" for b in content)
            if not has_text:
                print(f"{GREY_BG}[{role}]:{RESET}")
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        print(f"{GREY_BG}[{role} (tool_result id={block['tool_use_id']})]: {block['content']}{RESET}")
                else:
                    if block.type == "text":
                        print(f"{GREY_BG}[{role}]: {block.text}{RESET}")
                    elif block.type == "tool_use":
                        print(f"{GREY_BG}  -> tool_use (id={block.id}): {block.name}({json.dumps(block.input)}){RESET}")
    print(f"{GREY_BG}---{RESET}\n")


def insurance_shopping_agent(user_message):
    """Insurance shopping assistant with continuous tool calling loop and mid-loop summarization."""
    system = f"""Today is {datetime.today().strftime('%Y-%m-%d')}. You are a helpful insurance shopping assistant.

Use your available tools proactively and in sequence to give complete, actionable advice. Only call tools that are relevant to the user's request.

If the user's request is ambiguous or missing key details (e.g. insurance type, coverage amount, customer age), ask for clarification before calling tools."""

    messages = [{"role": "user", "content": user_message}]

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")

        if len(messages) > COMPRESS_THRESHOLD:
            old_messages = messages[1:-4]
            if old_messages:
                print(f"\n--- Compressing context window ({len(messages)} messages) ---")
                summary = summarize_messages(client, old_messages)
                messages = [
                    messages[0],
                    {"role": "user", "content": f"[Summary of earlier conversation]: {summary}"},
                    *messages[-4:]
                ]

        print_context_window(system, messages)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if text_blocks and not tool_use_blocks:
            print("Assistant:", text_blocks[0].text)

        if tool_use_blocks:
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_call in tool_use_blocks:
                print(f"  -> Calling: {tool_call.name}")
                result = execute_function_call(tool_call)
                print(f"  <- Result: {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
                time.sleep(1)

            messages.append({"role": "user", "content": tool_results})
            continue
        else:
            messages.append({"role": "assistant", "content": response.content})
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                break
            messages.append({"role": "user", "content": user_input})

    if iteration >= max_iterations:
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached. Ending conversation.")


if __name__ == "__main__":
    user_input = input("> ")
    insurance_shopping_agent(user_input)
