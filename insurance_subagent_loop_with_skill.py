"""
Subagent pattern for insurance shopping: isolate context by splitting tools
into 4 domain specialists (Health, Auto, Home, Life).

Without subagents (insurance_agent.py):
  Orchestrator context = system + messages + ALL tool defs + every tool call
  -> context grows with every iteration across all domains

With subagents (this file):
  Orchestrator context = system + messages + 4 delegation tools + 2 general
  tools + subagent summaries only
  Each subagent context = isolated per-request loop with 5 domain tools only
  -> orchestrator stays small; subagent contexts are short-lived and never
     merged back
"""

import anthropic
import json
import re
import time
from datetime import datetime
from pathlib import Path

from langsmith import traceable
from langsmith.wrappers import wrap_anthropic

from insurance_agent_tools_extended import tools as all_tools, execute_function_call

# Required env vars: LANGSMITH_API_KEY, LANGSMITH_TRACING=true
# Optional: LANGSMITH_PROJECT (defaults to "default")
client = wrap_anthropic(anthropic.Anthropic())
MAX_API_RETRIES = 5
RETRY_BASE_SECONDS = 2
BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
STRUCTURED_MEMORY_PATH = MEMORY_DIR / "structured_memory.jsonl"
EPISODIC_MEMORY_PATH = MEMORY_DIR / "episodic_memory.jsonl"


def create_message_with_retry(**kwargs):
    """Retry transient Anthropic API failures with exponential backoff."""
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            return client.messages.create(**kwargs)
        except (
            anthropic.RateLimitError,
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.InternalServerError,
        ) as exc:
            if attempt == MAX_API_RETRIES:
                raise
            wait_seconds = RETRY_BASE_SECONDS ** attempt
            print(
                f"[retry] Anthropic API temporary error "
                f"({type(exc).__name__}): retrying in {wait_seconds}s "
                f"({attempt}/{MAX_API_RETRIES})"
            )
            time.sleep(wait_seconds)
        except anthropic.APIStatusError as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code not in {429, 500, 502, 503, 504} or attempt == MAX_API_RETRIES:
                raise
            wait_seconds = RETRY_BASE_SECONDS ** attempt
            print(
                f"[retry] Anthropic API status {status_code}: "
                f"retrying in {wait_seconds}s ({attempt}/{MAX_API_RETRIES})"
            )
            time.sleep(wait_seconds)


HEALTH_TOOL_NAMES = {
    "search_health_plans",
    "get_health_plan_details",
    "calculate_health_premium",
    "check_health_eligibility",
    "add_health_rider",
}
AUTO_TOOL_NAMES = {
    "search_auto_policies",
    "get_auto_policy_details",
    "calculate_auto_premium",
    "check_auto_eligibility",
    "add_auto_rider",
}
HOME_TOOL_NAMES = {
    "search_home_policies",
    "get_home_policy_details",
    "calculate_home_premium",
    "schedule_home_inspection",
    "add_home_rider",
}
LIFE_TOOL_NAMES = {
    "search_life_policies",
    "get_life_policy_details",
    "calculate_life_premium",
    "check_life_eligibility",
    "schedule_medical_exam",
}
CLAIM_TOOL_NAMES = {"file_claim", "check_claim_status"}
GENERAL_TOOL_NAMES = {"get_customer_profile", "purchase_policy"}


def parse_skill_file(filepath):
    with open(BASE_DIR / filepath, encoding="utf-8") as handle:
        content = handle.read()
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        return {"name": filepath, "description": "", "body": content}
    front, body = match.group(1), match.group(2).strip()
    name_match = re.search(r"^name:\s*(.+)$", front, re.MULTILINE)
    desc_match = re.search(r"^description:\s*(.+)$", front, re.MULTILINE)
    return {
        "name": name_match.group(1).strip() if name_match else filepath,
        "description": desc_match.group(1).strip() if desc_match else "",
        "body": body,
    }


ORCHESTRATOR_SKILLS = [
    parse_skill_file("insurance-shopping-coordinator.md"),
    parse_skill_file("claim-processing-coordinator.md"),
]

SPECIALIST_SKILLS = [
    parse_skill_file("life-insurance-specialist.md"),
    parse_skill_file("health-insurance-specialist.md"),
    parse_skill_file("auto-insurance-specialist.md"),
    parse_skill_file("home-insurance-specialist.md"),
]

ALL_SKILLS = ORCHESTRATOR_SKILLS + SPECIALIST_SKILLS

load_skill_tool = {
    "name": "load_skill",
    "description": "Load the full instructions for a named insurance skill when detailed workflow guidance is needed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "The name of the insurance skill to load",
            }
        },
        "required": ["skill_name"],
    },
}


def _filter_tools(names):
    return [t for t in all_tools if t["name"] in names]


health_tools = _filter_tools(HEALTH_TOOL_NAMES)
auto_tools = _filter_tools(AUTO_TOOL_NAMES)
home_tools = _filter_tools(HOME_TOOL_NAMES)
life_tools = _filter_tools(LIFE_TOOL_NAMES)
general_tools = _filter_tools(GENERAL_TOOL_NAMES)
claim_tools = _filter_tools(CLAIM_TOOL_NAMES)


@traceable(name="execute_subagent_tool")
def execute_subagent_tool(tool_call):
    if tool_call.name == "load_skill":
        return execute_load_skill(tool_call.input["skill_name"])
    return execute_function_call(tool_call)


def _tool_signature(tool_call):
    return tool_call.name, json.dumps(tool_call.input, sort_keys=True, ensure_ascii=False)


@traceable(name="run_subagent")
def run_subagent(task: str, domain_tools: list, system_prompt: str, max_iterations: int = 8) -> str:
    """Run an isolated agentic loop with a domain-specific tool subset."""
    messages = [{"role": "user", "content": task}]
    seen_tool_signatures = set()

    for _ in range(max_iterations):
        response = create_message_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=domain_tools,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if not tool_use_blocks:
            return text_blocks[0].text if text_blocks else "(no result)"

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_call in tool_use_blocks:
            signature = _tool_signature(tool_call)
            if signature in seen_tool_signatures:
                result = (
                    "This exact tool call with the same arguments was already executed. "
                    "Do not repeat it. Summarize the current results instead."
                )
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tool_call.id, "content": result}
                )
                continue
            try:
                result = execute_subagent_tool(tool_call)
            except (KeyError, TypeError) as exc:
                result = f"Error: missing required field {exc}. Please retry with all required parameters."
            seen_tool_signatures.add(signature)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": tool_call.id, "content": result}
            )
        messages.append({"role": "user", "content": tool_results})

    return "(subagent reached max iterations without a final response)"


def call_health_agent(task: str) -> str:
    system = (
        "You are a health insurance specialist. Use your tools to search plans, "
        "check details, calculate premiums, verify eligibility, and suggest riders. "
        "Be concise and include numbers (premiums, deductibles) when applicable. "
        "When you need detailed workflow guidance, call load_skill('health-insurance-specialist')."
    )
    return run_subagent(task, health_tools + claim_tools + [load_skill_tool], system)


def call_auto_agent(task: str) -> str:
    system = (
        "You are an auto insurance specialist. Use your tools to search policies, "
        "check details, calculate premiums, verify driving-record eligibility, and suggest riders. "
        "Be concise and include premium estimates when applicable. "
        "When you have found 2-3 suitable options, stop calling tools and summarize them "
        "clearly in your final response. "
        "When you need detailed workflow guidance, call load_skill('auto-insurance-specialist')."
    )
    return run_subagent(task, auto_tools + claim_tools + [load_skill_tool], system)


def call_home_agent(task: str) -> str:
    system = (
        "You are a home insurance specialist. Use your tools to search policies, "
        "check details, calculate premiums, schedule inspections, and suggest riders. "
        "Be concise and include coverage limits and premium estimates. "
        "When you need detailed workflow guidance, call load_skill('home-insurance-specialist')."
    )
    return run_subagent(task, home_tools + claim_tools + [load_skill_tool], system)


def call_life_agent(task: str) -> str:
    system = (
        "You are a life insurance specialist. Use your tools to search policies, "
        "check details, calculate premiums, verify eligibility, and schedule medical exams. "
        "Be concise and include premium estimates and term details. "
        "When you need detailed workflow guidance for life insurance, call load_skill('life-insurance-specialist')."
    )
    return run_subagent(task, life_tools + claim_tools + [load_skill_tool], system)


def execute_load_skill(skill_name: str) -> str:
    for skill in ALL_SKILLS:
        if skill["name"] == skill_name:
            return (
                f"[Skill: {skill['name']}]\n\n{skill['body']}\n\n"
                "The skill above has been loaded. Proceed immediately to follow its instructions "
                "and call the relevant tools. Do not pause for user confirmation."
            )
    return f"Skill '{skill_name}' not found. Available: {[skill['name'] for skill in ALL_SKILLS]}"


orchestrator_tools = [load_skill_tool] + [
    {
        "name": "call_health_agent",
        "description": (
            "Delegate health insurance tasks to a specialist subagent. Handles: "
            "search_health_plans, get_health_plan_details, calculate_health_premium, "
            "check_health_eligibility, add_health_rider."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Detailed description of the health insurance task to accomplish",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "call_auto_agent",
        "description": (
            "Delegate auto insurance tasks to a specialist subagent. Handles: "
            "search_auto_policies, get_auto_policy_details, calculate_auto_premium, "
            "check_auto_eligibility, add_auto_rider."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Detailed description of the auto insurance task to accomplish",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "call_home_agent",
        "description": (
            "Delegate home insurance tasks to a specialist subagent. Handles: "
            "search_home_policies, get_home_policy_details, calculate_home_premium, "
            "schedule_home_inspection, add_home_rider."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Detailed description of the home insurance task to accomplish",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "call_life_agent",
        "description": (
            "Delegate life insurance tasks to a specialist subagent. Handles: "
            "search_life_policies, get_life_policy_details, calculate_life_premium, "
            "check_life_eligibility, schedule_medical_exam."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Detailed description of the life insurance task to accomplish",
                }
            },
            "required": ["task"],
        },
    },
] + general_tools

orchestrator_tools += claim_tools

_SUBAGENT_DISPATCHERS = {
    "call_health_agent": lambda args: call_health_agent(args["task"]),
    "call_auto_agent": lambda args: call_auto_agent(args["task"]),
    "call_home_agent": lambda args: call_home_agent(args["task"]),
    "call_life_agent": lambda args: call_life_agent(args["task"]),
}


@traceable(name="execute_orchestrator_tool")
def execute_orchestrator_tool(tool_call):
    handler = _SUBAGENT_DISPATCHERS.get(tool_call.name)
    if handler:
        return handler(tool_call.input)
    if tool_call.name == "load_skill":
        return execute_load_skill(tool_call.input["skill_name"])
    if tool_call.name in GENERAL_TOOL_NAMES or tool_call.name in CLAIM_TOOL_NAMES:
        return execute_function_call(tool_call)
    return f"Unknown orchestrator tool: {tool_call.name}"


GREY_BG = "\033[48;5;252m\033[38;5;17m"
RESET = "\033[0m"


def print_orchestrator_context(system, messages, case_state=None):
    print(f"\n{GREY_BG}--- Orchestrator context ({len(messages) + 1} messages) ---{RESET}")
    for tool_def in orchestrator_tools:
        tool_kind = "subagent_tool" if tool_def["name"] in _SUBAGENT_DISPATCHERS else "tool"
        print(f"{GREY_BG}[{tool_kind}] {tool_def['name']} - {tool_def['description']}{RESET}")
    print(f"{GREY_BG}[system]: {system}{RESET}")
    if case_state is not None:
        print(f"{GREY_BG}[state]: {json.dumps(case_state, ensure_ascii=False)}{RESET}")
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            print(f"{GREY_BG}[{role}]: {content}{RESET}")
        elif isinstance(content, list):
            has_text = any(not isinstance(block, dict) and block.type == "text" for block in content)
            if not has_text:
                print(f"{GREY_BG}[{role}]:{RESET}")
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        preview = str(block["content"])[:400]
                        print(
                            f"{GREY_BG}[{role} (tool_result id={block['tool_use_id']})]: "
                            f"{preview}{'...' if len(str(block['content'])) > 400 else ''}{RESET}"
                        )
                else:
                    if block.type == "text":
                        print(f"{GREY_BG}[{role}]: {block.text}{RESET}")
                    elif block.type == "tool_use":
                        args_preview = json.dumps(block.input, ensure_ascii=False)[:100]
                        print(
                            f"{GREY_BG}  -> tool_use (id={block.id}): "
                            f"{block.name}({args_preview}){RESET}"
                        )
    print(f"{GREY_BG}---{RESET}\n")


def _tool_signature(tool_call):
    return tool_call.name, json.dumps(tool_call.input, sort_keys=True, ensure_ascii=False)


def _should_block_repeated_direct_tool(tool_call, last_direct_tool_signature):
    if tool_call.name in _SUBAGENT_DISPATCHERS or tool_call.name == "load_skill":
        return False
    return _tool_signature(tool_call) == last_direct_tool_signature


def _prompt_for_direct_tool_summary(system, messages):
    summary_messages = messages + [{
        "role": "user",
        "content": (
            "The tool results above already contain the information needed to answer the user. "
            "Respond directly in natural language, summarize the outcome clearly, and do not "
            "call any more tools."
        ),
    }]
    return create_message_with_retry(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=summary_messages,
    )


def _extract_text_from_response(response):
    text_blocks = []
    for block in getattr(response, "content", []):
        if getattr(block, "type", None) == "text":
            text_blocks.append(block.text)
    return "\n".join(text_blocks).strip()


def _init_case_state():
    return {
        "primary_goal": None,
        "current_domain": None,
        "domains": [],
        "age": None,
        "smoker": None,
        "region": None,
        "family_status": None,
        "budget_preference": None,
        "coverage_preference": None,
        "cash_value_importance": None,
        "coverage_amount": None,
        "term_years": None,
        "selected_products": [],
        "claim_reference": None,
        "customer_id": None,
        "latest_quote": None,
        "latest_eligibility": None,
        "open_questions": [],
        "notes": [],
    }


def _dedupe_preserve_order(items):
    seen = set()
    deduped = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _extract_product_names(text):
    names = []
    if not text:
        return names

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        heading_match = re.match(r"^##\s*\d+\.\s*(.+)$", line)
        if heading_match:
            candidate = heading_match.group(1).strip()
            candidate = re.split(r"\s*[—-]\s*", candidate, maxsplit=1)[0].strip()
            candidate = candidate.split("：")[-1].strip()
            if 1 <= len(candidate) <= 80:
                names.append(candidate)
            continue

        label_match = re.search(r"\*\*(?:方案名称|产品名称)\*\*\s*[|：:]\s*([^|]+)", line)
        if label_match:
            candidate = label_match.group(1).strip()
            candidate = re.split(r"\s*[—-]\s*", candidate, maxsplit=1)[0].strip()
            candidate = candidate.split("：")[-1].strip()
            if 1 <= len(candidate) <= 80:
                names.append(candidate)

    return _dedupe_preserve_order(names)


def _update_case_state_from_text(case_state, text, role=None):
    if not text:
        return case_state

    lower_text = text.lower()

    if role == "user" and not case_state.get("primary_goal"):
        case_state["primary_goal"] = text.strip()[:240]

    domain_keywords = {
        "health": ["健康险", "health"],
        "auto": ["车险", "auto", "汽车险", "驾驶"],
        "home": ["家财险", "home", "住房", "房屋"],
        "life": ["寿险", "life", "定期寿险", "终身寿险"],
        "claim": ["理赔", "报案", "赔付", "claim", "报销"],
    }
    for domain, keywords in domain_keywords.items():
        if any(keyword in text or keyword in lower_text for keyword in keywords):
            case_state["current_domain"] = domain
            case_state["domains"] = _dedupe_preserve_order(case_state["domains"] + [domain])

    age_match = re.search(r"(\d{1,3})\s*岁", text)
    if age_match:
        case_state["age"] = int(age_match.group(1))

    if any(marker in text for marker in ["不吸烟", "非吸烟", "不抽烟", "从不吸烟"]) or any(
        marker in lower_text for marker in ["non-smoker", "nonsmoker", "no smoking"]
    ):
        case_state["smoker"] = False
    elif any(marker in text for marker in ["吸烟", "抽烟", "烟龄"]) or any(
        marker in lower_text for marker in ["smoker", "smoking"]
    ):
        case_state["smoker"] = True

    region_match = re.search(
        r"(?:地区|城市|risk area|risk region|region)\s*[:：]?\s*([^\n，。,;；]{2,30})",
        text,
        re.IGNORECASE,
    )
    if region_match:
        case_state["region"] = region_match.group(1).strip()
    elif any(marker in text for marker in ["中等风险地区", "高风险地区", "低风险地区", "一线城市", "二线城市", "三线城市"]):
        case_state["region"] = text.strip()[:80]

    family_markers = ["单身", "未婚", "已婚", "有孩子", "无孩", "一家三口", "一家四口", "家庭"]
    if any(marker in text for marker in family_markers):
        case_state["family_status"] = text.strip()[:120]

    if any(marker in text for marker in ["预算", "price sensitive", "便宜", "性价比", "预算优先"]):
        case_state["budget_preference"] = text.strip()[:160]

    if any(marker in text for marker in ["保障", "coverage", "保额", "全面", "高保额"]):
        case_state["coverage_preference"] = text.strip()[:160]

    if any(marker in text for marker in ["现金价值", "储蓄", "分红", "返还", "cash value"]):
        case_state["cash_value_importance"] = text.strip()[:160]

    coverage_match = re.search(
        r"(?:保额|coverage(?: amount)?|sum insured)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(万|w|W|k|K|元|美元|\$)?",
        text,
        re.IGNORECASE,
    )
    if coverage_match:
        amount = coverage_match.group(1)
        unit = coverage_match.group(2) or ""
        case_state["coverage_amount"] = f"{amount}{unit}"
    else:
        compact_coverage_match = re.search(r"(\d+(?:\.\d+)?)\s*(万|w|W|k|K|元|美元|\$)", text)
        if compact_coverage_match and any(token in text for token in ["保额", "coverage", "sum insured"]):
            case_state["coverage_amount"] = (
                f"{compact_coverage_match.group(1)}{compact_coverage_match.group(2)}"
            )

    term_match = re.search(r"(\d{1,3})\s*(?:年期|年定期|年保障|year term|term)", text, re.IGNORECASE)
    if term_match:
        case_state["term_years"] = int(term_match.group(1))

    product_names = _extract_product_names(text)
    if product_names:
        case_state["selected_products"] = _dedupe_preserve_order(
            case_state["selected_products"] + product_names
        )[:6]

    claim_match = re.search(
        r"(?:claim\s*(?:reference|ref|#)?|理赔(?:单号|编号|参考号)|报案号|案件号|编号)[:：\s]*([A-Za-z0-9-]+)",
        text,
        re.IGNORECASE,
    )
    if claim_match:
        case_state["claim_reference"] = claim_match.group(1).strip()

    customer_match = re.search(
        r"(?:customer\s*id|客户ID|客户编号)[:：\s]*([A-Za-z0-9-]+)",
        text,
        re.IGNORECASE,
    )
    if customer_match:
        case_state["customer_id"] = customer_match.group(1).strip()

    if "quote" in lower_text or "保费" in text or "月保费" in text or "年保费" in text:
        quote_snippet = text.strip().replace("\n", " ")
        case_state["latest_quote"] = quote_snippet[:260]

    if "eligible" in lower_text or "eligibility" in lower_text or "符合" in text or "不符合" in text:
        elig_snippet = text.strip().replace("\n", " ")
        case_state["latest_eligibility"] = elig_snippet[:260]

    return case_state


def _record_case_state_from_message(case_state, role, content):
    if isinstance(content, str):
        _update_case_state_from_text(case_state, content, role=role)
        return case_state

    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "tool_result":
                    _update_case_state_from_text(case_state, str(block.get("content", "")), role=role)
            elif hasattr(block, "type") and block.type == "text":
                _update_case_state_from_text(case_state, block.text, role=role)

    return case_state


def _append_message(messages, case_state, role, content, record_state=True):
    messages.append({"role": role, "content": content})
    if record_state:
        _record_case_state_from_message(case_state, role, content)


def _latest_user_text(messages, fallback=""):
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content
    return fallback


def _extract_text_from_content_blocks(content):
    text_lines = []
    if isinstance(content, list):
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                text_lines.append(block.text)
    return "\n".join(text_lines).strip()


def _stringify_message_content(content):
    if isinstance(content, str):
        return content
    lines = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "tool_result":
                    lines.append(f"[tool_result:{block.get('tool_use_id', '')}] {block.get('content', '')}")
            elif hasattr(block, "type"):
                if block.type == "text":
                    lines.append(block.text)
                elif block.type == "tool_use":
                    lines.append(
                        f"[tool_use] {block.name}({json.dumps(block.input, ensure_ascii=False)})"
                    )
    return "\n".join(lines).strip()


def save_conversation_markdown(messages, case_state, original_user_input):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOGS_DIR / f"insurance_conversation_{ts}.md"
    lines = []
    lines.append("# Insurance Conversation Log")
    lines.append("")
    lines.append(f"- Saved at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Original request: {original_user_input}")
    lines.append("")
    lines.append("## Case State")
    lines.append("```json")
    lines.append(json.dumps(case_state, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Messages")
    for idx, msg in enumerate(messages, start=1):
        role = msg.get("role", "unknown")
        content = _stringify_message_content(msg.get("content"))
        lines.append(f"### {idx}. {role}")
        lines.append(content if content else "(empty)")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def _append_jsonl(path: Path, record: dict):
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path):
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _has_meaningful_state_changes(case_state):
    keys = [
        "age",
        "smoker",
        "region",
        "family_status",
        "budget_preference",
        "coverage_preference",
        "cash_value_importance",
        "coverage_amount",
        "term_years",
        "claim_reference",
        "customer_id",
    ]
    return any(case_state.get(key) is not None for key in keys)


def _build_memory_payload(case_state, messages, event_type):
    last_user_text = None
    last_assistant_text = None
    last_tool_text = None

    for msg in reversed(messages):
        content = msg.get("content")
        if last_user_text is None and msg.get("role") == "user" and isinstance(content, str):
            last_user_text = content
        elif last_assistant_text is None and msg.get("role") == "assistant" and isinstance(content, list):
            texts = [
                block.text for block in content
                if hasattr(block, "type") and block.type == "text"
            ]
            if texts:
                last_assistant_text = "\n".join(texts)
        elif last_tool_text is None and isinstance(content, list):
            tool_texts = [
                str(block.get("content", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "tool_result"
            ]
            if tool_texts:
                last_tool_text = "\n".join(tool_texts)

        if last_user_text and last_assistant_text and last_tool_text:
            break

    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "event_type": event_type,
        "case_state": case_state,
        "last_user_text": last_user_text,
        "last_assistant_text": last_assistant_text,
        "last_tool_text": last_tool_text,
    }


def _structured_state(case_state):
    fields = ["age", "smoker", "region", "family_status", "budget_preference", "coverage_preference", "cash_value_importance"]
    return {key: case_state.get(key) for key in fields if case_state.get(key) not in (None, "", [], {})}


def _episodic_state(case_state):
    fields = ["current_domain", "domains", "coverage_amount", "term_years", "selected_products", "claim_reference", "customer_id", "latest_quote", "latest_eligibility", "primary_goal"]
    return {key: case_state.get(key) for key in fields if case_state.get(key) not in (None, "", [], {})}


def _structured_memory_signature(case_state):
    return json.dumps(_structured_state(case_state), sort_keys=True, ensure_ascii=False)


def _episodic_memory_signature(case_state, detail_text):
    payload = {"state": _episodic_state(case_state), "detail_text": (detail_text or "")[:800]}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _write_structured_memory(case_state, messages, event_type="state_update", last_signature=None):
    relevant_state = _structured_state(case_state)
    if not relevant_state:
        return last_signature
    signature = _structured_memory_signature(case_state)
    if signature == last_signature:
        return last_signature
    _append_jsonl(
        STRUCTURED_MEMORY_PATH,
        {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event_type": event_type,
            "memory_kind": "structured",
            "case_state": relevant_state,
        },
    )
    return signature


def _score_memory_record(record, case_state, user_message, memory_kind):
    score = 0
    query = f"{user_message} {json.dumps(case_state, ensure_ascii=False)}".lower()
    memory_text = json.dumps(record, ensure_ascii=False).lower()

    if memory_kind == "structured":
        for key in ["age", "smoker", "region", "family_status", "budget_preference", "coverage_preference", "cash_value_importance"]:
            value = case_state.get(key)
            if value and str(value).lower() in memory_text:
                score += 3
    else:
        for key in ["customer_id", "claim_reference", "current_domain", "coverage_amount", "term_years"]:
            value = case_state.get(key)
            if value and str(value).lower() in memory_text:
                score += 4

    if case_state.get("age") and str(case_state["age"]) in memory_text:
        score += 2
    if case_state.get("coverage_amount") and str(case_state["coverage_amount"]).lower() in memory_text:
        score += 2
    if case_state.get("term_years") and str(case_state["term_years"]) in memory_text:
        score += 2

    keywords = [w for w in re.split(r"\s+", query) if len(w) >= 2]
    for keyword in keywords[:20]:
        if keyword in memory_text:
            score += 1

    return score


def _retrieve_relevant_memory(case_state, user_message, limit=3, path=STRUCTURED_MEMORY_PATH):
    records = _read_jsonl(path)
    scored = []
    for record in records:
        memory_kind = record.get("memory_kind", "structured" if path == STRUCTURED_MEMORY_PATH else "episodic")
        score = _score_memory_record(record, case_state, user_message, memory_kind)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [record for _, record in scored[:limit]]


def _format_memory_block(records):
    if not records:
        return "[Relevant memory]: none"
    lines = ["[Relevant memory]:"]
    for idx, record in enumerate(records, start=1):
        item = (
            f"{idx}. {record.get('event_type', 'memory')} | "
            f"{json.dumps(record.get('case_state', {}), ensure_ascii=False)}"
        )
        detail_text = str(record.get("detail_text", "")).strip()
        if detail_text:
            detail_preview = detail_text.replace("\n", " ")
            if len(detail_preview) > 180:
                detail_preview = detail_preview[:180] + "..."
            item += f" | detail: {detail_preview}"
        lines.append(item)
    return "\n".join(lines)


def _build_memory_prompt_block(case_state, user_message, limit_structured=2, limit_episodic=3):
    structured_records = _retrieve_relevant_memory(
        case_state,
        user_message,
        limit=limit_structured,
        path=STRUCTURED_MEMORY_PATH,
    )
    episodic_records = _retrieve_relevant_memory(
        case_state,
        user_message,
        limit=limit_episodic,
        path=EPISODIC_MEMORY_PATH,
    )
    lines = [
        _format_memory_block(structured_records).replace("[Relevant memory]", "[Structured memory]"),
        _format_memory_block(episodic_records).replace("[Relevant memory]", "[Episodic memory]"),
    ]
    return "\n".join(lines)


def _write_episodic_memory(case_state, messages, event_type, detail_text, dedupe_key=None, last_signature=None):
    relevant_state = _episodic_state(case_state)
    if not relevant_state and not detail_text:
        return last_signature
    signature = dedupe_key or _episodic_memory_signature(case_state, detail_text)
    if signature == last_signature:
        return last_signature
    payload = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "event_type": event_type,
        "memory_kind": "episodic",
        "case_state": relevant_state,
        "detail_text": detail_text[:800],
    }
    _append_jsonl(EPISODIC_MEMORY_PATH, payload)
    return signature


def _write_memory_for_turn(case_state, messages, user_text="", assistant_text="", tool_text="",
                           last_structured_signature=None, last_episodic_signature=None):
    structured_signature = last_structured_signature
    episodic_signature = last_episodic_signature

    if _structured_state(case_state):
        structured_signature = _write_structured_memory(
            case_state,
            messages,
            event_type="structured_update",
            last_signature=last_structured_signature,
        )

    episodic_text = " ".join(part for part in [user_text, assistant_text, tool_text] if part)
    if _episodic_state(case_state) or episodic_text:
        episodic_signature = _write_episodic_memory(
            case_state,
            messages,
            "episodic_update",
            episodic_text,
            last_signature=last_episodic_signature,
        )

    return structured_signature, episodic_signature


# This counts raw message objects, not user turns.
# One interaction can add multiple messages (assistant/tool_result/user).
MESSAGE_THRESHOLD = 16
RECENT_MESSAGE_WINDOW = 8


def _has_pending_tool_use(messages):
    if not messages:
        return False
    last = messages[-1]
    if last["role"] != "assistant":
        return False
    content = last.get("content", [])
    if isinstance(content, list):
        return any(
            (isinstance(b, dict) and b.get("type") == "tool_use") or
            (hasattr(b, "type") and b.type == "tool_use")
            for b in content
        )
    return False


def _assistant_called_only_load_skill(content):
    if not isinstance(content, list):
        return False
    tool_uses = [block for block in content if hasattr(block, "type") and block.type == "tool_use"]
    if not tool_uses:
        return False
    return all(block.name == "load_skill" for block in tool_uses)


def _just_loaded_skill_without_tools(messages):
    """Check if a load_skill was called recently but no subagent followed."""
    if len(messages) < 3:
        return False

    # 从后往前找到最近一个只调用了 load_skill 的 assistant 消息
    load_skill_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        tool_uses = [block for block in content if hasattr(block, "type") and block.type == "tool_use"]
        if not tool_uses:
            continue
        if all(block.name == "load_skill" for block in tool_uses):
            load_skill_idx = i
            break

    if load_skill_idx == -1:
        return False

    # 检查 load_skill 之后是否有子代理调用
    for j in range(load_skill_idx + 1, len(messages)):
        msg = messages[j]
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if hasattr(block, "type") and block.type == "tool_use" and block.name in _SUBAGENT_DISPATCHERS:
                return False

    # 最后一条消息应该是 assistant 纯文本（没有 tool_use）
    last_msg = messages[-1]
    if last_msg.get("role") != "assistant":
        return False
    last_content = last_msg.get("content", [])
    if isinstance(last_content, list):
        has_tool_use = any(hasattr(block, "type") and block.type == "tool_use" for block in last_content)
        if has_tool_use:
            return False

    return True


def _force_tool_call_after_skill(dynamic_system, messages):
    """Hard fallback: force at least one non-load_skill tool call immediately."""
    force_prompt = (
        "You just loaded a skill but did not call any specialist subagent tool. "
        "You MUST now call the appropriate subagent tool immediately "
        "(call_life_agent, call_health_agent, call_auto_agent, call_home_agent) "
        "or another relevant direct tool. Do not provide narrative text before tool calls."
    )
    forced_messages = messages + [{"role": "user", "content": force_prompt}]
    forced_tools = [tool_def for tool_def in orchestrator_tools if tool_def["name"] != "load_skill"]
    return create_message_with_retry(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=dynamic_system,
        messages=forced_messages,
        tools=forced_tools,
        tool_choice={"type": "any"},
    )


def compress_if_needed(messages, original_user_input, case_state, threshold=MESSAGE_THRESHOLD):
    if len(messages) < threshold:
        return messages
    if _has_pending_tool_use(messages):
        print("[compress] Skipping - pending tool_use in last assistant message.")
        return messages

    print(f"[compress] Compressing {len(messages)} messages into summary...")

    older_messages = messages[:-RECENT_MESSAGE_WINDOW] if len(messages) > RECENT_MESSAGE_WINDOW else []
    transcript_lines = []
    for msg in older_messages:
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            transcript_lines.append(f"{role.upper()}: {content}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        transcript_lines.append(f"TOOL_RESULT: {block['content']}")
                elif hasattr(block, "type"):
                    if block.type == "text":
                        transcript_lines.append(f"{role.upper()}: {block.text}")
                    elif block.type == "tool_use":
                        transcript_lines.append(f"TOOL_USE: {block.name}({json.dumps(block.input, ensure_ascii=False)})")

    transcript = "\n".join(transcript_lines)

    try:
        summary_response = create_message_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": (
                "Summarize the older part of this insurance conversation concisely. Include: "
                "the user's goal, what has already been accomplished, key facts, unresolved "
                "questions, and anything that should be preserved for continuity.\n\n"
                f"<conversation>\n{transcript}\n</conversation>"
            )}]
        )
        summary_text = _extract_text_from_response(summary_response)
        if not summary_text:
            raise ValueError("summary response did not contain any text blocks")
    except Exception as exc:
        print(f"[compress] Summarization failed ({exc}), keeping original messages.")
        return messages

    recent_messages = messages[-RECENT_MESSAGE_WINDOW:] if len(messages) > RECENT_MESSAGE_WINDOW else messages[:]
    compressed = [{
        "role": "user",
        "content": (
            f"[Original request]: {original_user_input}\n\n"
            f"[Structured case state]:\n{json.dumps(case_state, ensure_ascii=False, indent=2)}\n\n"
            f"[Conversation summary so far]:\n{summary_text}"
        ),
    }]
    compressed.extend(recent_messages)
    print(f"[compress] Compressed {len(messages)} -> {len(compressed)} messages.")
    return compressed


@traceable(name="insurance_coordinator_with_subagents")
def insurance_coordinator_with_subagents(user_message: str):
    """Coordinator that delegates to specialist insurance subagents."""
    skills_summary = "\n".join(f"- {skill['name']}: {skill['description']}" for skill in ORCHESTRATOR_SKILLS)
    system = (
        f"Today is {datetime.today().strftime('%Y-%m-%d')}. "
        "You are an insurance coordinator. You help users with shopping for insurance, filing claims, "
        "tracking claim status, and general insurance inquiries. You have access to specialized skills. "
        "When a user request matches a skill, call load_skill first to get the full instructions "
        "before proceeding.\n\n"
        f"Available skills:\n{skills_summary}\n\n"
        "Delegate domain-specific tasks to the appropriate specialist subagent(s), and use "
        "general tools directly when you need customer profile lookups or policy purchase execution. "
        "Use claim tools directly for claim filing and claim status checks, or delegate claim-related "
        "tasks to specialist subagents when appropriate. Synthesize all results into a final response. "
        "Each subagent runs its own "
        "tool calls internally, and you only receive their final text summaries. If a tool "
        "result already answers the user's request, respond directly in natural language and "
        "do not call more tools. Do not repeat the same tool call with the same arguments "
        "unless the user has provided new information."
    )

    case_state = _init_case_state()
    messages = [{"role": "user", "content": user_message}]
    _record_case_state_from_message(case_state, "user", user_message)
    max_iters = 20
    last_direct_tool_signature = None
    last_structured_memory_signature = None
    last_episodic_memory_signature = None

    for iteration in range(1, max_iters + 1):
        print(f"\n--- Orchestrator Iteration {iteration} ---")
        messages = compress_if_needed(messages, user_message, case_state)
        current_user_text = _latest_user_text(messages, fallback=user_message)
        memory_block = _build_memory_prompt_block(case_state, current_user_text)
        dynamic_system = f"{system}\n\n{memory_block}"
        prompt_messages = messages
        print_orchestrator_context(dynamic_system, prompt_messages, case_state)

        response = create_message_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=dynamic_system,
            messages=prompt_messages,
            tools=orchestrator_tools,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if not tool_use_blocks:
            print("Assistant:", text_blocks[0].text if text_blocks else "(no response)")
            _append_message(messages, case_state, "assistant", response.content)

            # 兜底：刚 load skill 但没调子代理 → 当轮强制触发工具调用
            if _just_loaded_skill_without_tools(messages):
                print(
                    "\n[orchestrator] Skill loaded but no subagent called. "
                    "Enforcing immediate tool call..."
                )
                forced_response = _force_tool_call_after_skill(dynamic_system, messages)
                forced_tool_use_blocks = [b for b in forced_response.content if b.type == "tool_use"]
                forced_text_blocks = [b for b in forced_response.content if b.type == "text"]
                if not forced_tool_use_blocks:
                    print("Assistant:", forced_text_blocks[0].text if forced_text_blocks else "(no response)")
                    _append_message(messages, case_state, "assistant", forced_response.content)
                    user_input = input("\n> ")
                    if user_input.lower() == "exit":
                        saved_path = save_conversation_markdown(messages, case_state, user_message)
                        print(f"\nConversation saved to: {saved_path}")
                        break
                    _append_message(messages, case_state, "user", user_input)
                    last_structured_memory_signature, last_episodic_memory_signature = _write_memory_for_turn(
                        case_state,
                        messages,
                        user_text=user_input,
                        assistant_text=forced_text_blocks[0].text if forced_text_blocks else "",
                        tool_text="",
                        last_structured_signature=last_structured_memory_signature,
                        last_episodic_signature=last_episodic_memory_signature,
                    )
                    continue

                # Replace with forced tool response so this iteration continues with tool execution.
                response = forced_response
                tool_use_blocks = forced_tool_use_blocks
                text_blocks = forced_text_blocks
                _append_message(
                    messages,
                    case_state,
                    "assistant",
                    forced_response.content,
                    record_state=False,
                )
                # fall through to tool execution below

            if not tool_use_blocks:
                user_input = input("\n> ")
                if user_input.lower() == "exit":
                    saved_path = save_conversation_markdown(messages, case_state, user_message)
                    print(f"\nConversation saved to: {saved_path}")
                    break
                _append_message(messages, case_state, "user", user_input)
                last_structured_memory_signature, last_episodic_memory_signature = _write_memory_for_turn(
                    case_state,
                    messages,
                    user_text=user_input,
                    assistant_text=text_blocks[0].text if text_blocks else "",
                    tool_text="",
                    last_structured_signature=last_structured_memory_signature,
                    last_episodic_signature=last_episodic_memory_signature,
                )
                continue

        _append_message(messages, case_state, "assistant", response.content)
        tool_results = []
        direct_tools_called = False
        for tool_call in tool_use_blocks:
            if _should_block_repeated_direct_tool(tool_call, last_direct_tool_signature):
                blocked_result = (
                    "The same direct tool call was just executed with identical arguments and "
                    "already answered the user's request. Respond to the user with a concise "
                    "natural-language summary instead of repeating the tool call."
                )
                print(f"  -> Blocking repeated tool: {tool_call.name}")
                print(f"  <- Tool result: {blocked_result[:120]}...")
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tool_call.id, "content": blocked_result}
                )
                continue

            if tool_call.name in _SUBAGENT_DISPATCHERS:
                print(f"  -> Delegating to: {tool_call.name}")
                print(f"    task: {tool_call.input['task']}")
            elif tool_call.name == "load_skill":
                print(f"  -> Calling tool: {tool_call.name}")
                print(f"    args: {json.dumps(tool_call.input, ensure_ascii=False)}")
            else:
                direct_tools_called = True
                print(f"  -> Calling tool: {tool_call.name}")
                print(f"    args: {json.dumps(tool_call.input, ensure_ascii=False)}")
            result = execute_orchestrator_tool(tool_call)
            result_label = "Subagent summary" if tool_call.name in _SUBAGENT_DISPATCHERS else "Tool result"
            print(f"  <- {result_label}: {result[:120]}...")
            tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})
            if tool_call.name in _SUBAGENT_DISPATCHERS or tool_call.name == "load_skill":
                last_direct_tool_signature = None
            else:
                last_direct_tool_signature = _tool_signature(tool_call)
        _append_message(messages, case_state, "user", tool_results)
        final_assistant_text = ""
        if direct_tools_called:
            followup_response = _prompt_for_direct_tool_summary(dynamic_system, messages)
            followup_text_blocks = [b for b in followup_response.content if b.type == "text"]
            print("Assistant:", followup_text_blocks[0].text if followup_text_blocks else "(no response)")
            _append_message(messages, case_state, "assistant", followup_response.content)
            final_assistant_text = followup_text_blocks[0].text if followup_text_blocks else ""
            last_direct_tool_signature = None
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                saved_path = save_conversation_markdown(messages, case_state, user_message)
                print(f"\nConversation saved to: {saved_path}")
                break
            _append_message(messages, case_state, "user", user_input)
        else:
            final_assistant_text = _extract_text_from_content_blocks(response.content)
            if not final_assistant_text and text_blocks:
                final_assistant_text = text_blocks[0].text

        turn_user_text = _latest_user_text(messages, fallback=current_user_text)
        last_structured_memory_signature, last_episodic_memory_signature = _write_memory_for_turn(
            case_state,
            messages,
            user_text=turn_user_text,
            assistant_text=final_assistant_text,
            tool_text="\n".join(str(item.get("content", "")) for item in tool_results),
            last_structured_signature=last_structured_memory_signature,
            last_episodic_signature=last_episodic_memory_signature,
        )
    else:
        print(f"\nMax iterations ({max_iters}) reached.")
        saved_path = save_conversation_markdown(messages, case_state, user_message)
        print(f"Conversation saved to: {saved_path}")


if __name__ == "__main__":
    user_input = input("> ")
    insurance_coordinator_with_subagents(user_input)
