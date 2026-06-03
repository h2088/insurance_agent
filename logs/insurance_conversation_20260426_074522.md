# Insurance Conversation Log

- Saved at: 2026-04-26T07:45:22
- Original request: 我30岁，不吸烟，想买20年期寿险，保额30万，先帮我比较3个方案。

## Case State
```json
{
  "primary_goal": "我30岁，不吸烟，想买20年期寿险，保额30万，先帮我比较3个方案。",
  "current_domain": "life",
  "domains": [
    "life",
    "health",
    "auto",
    "home",
    "claim"
  ],
  "age": 30,
  "smoker": false,
  "region": null,
  "family_status": "根据您的需求（30岁、不吸烟、20年期、保额30万美元），我为您找到了以下可选方案：\n\n---\n\n## 方案一：Life Term 20（LIFE-TERM20-002）⭐ **最匹配**\n- **保障期限：** 20年 ✅\n- **保额上",
  "budget_preference": "根据您的需求（30岁、不吸烟、20年期、保额30万美元），我为您找到了以下可选方案：\n\n---\n\n## 方案一：Life Term 20（LIFE-TERM20-002）⭐ **最匹配**\n- **保障期限：** 20年 ✅\n- **保额上限：** $250,000（距离您目标的30万还差5万）\n- **预估月保费：*",
  "coverage_preference": "根据您的需求（30岁、不吸烟、20年期、保额30万美元），我为您找到了以下可选方案：\n\n---\n\n## 方案一：Life Term 20（LIFE-TERM20-002）⭐ **最匹配**\n- **保障期限：** 20年 ✅\n- **保额上限：** $250,000（距离您目标的30万还差5万）\n- **预估月保费：*",
  "cash_value_importance": null,
  "coverage_amount": "30万",
  "term_years": 20,
  "selected_products": [],
  "claim_reference": "a",
  "customer_id": "-",
  "latest_quote": "根据您的需求（30岁、不吸烟、20年期、保额30万美元），我为您找到了以下可选方案：  ---  ## 方案一：Life Term 20（LIFE-TERM20-002）⭐ **最匹配** - **保障期限：** 20年 ✅ - **保额上限：** $250,000（距离您目标的30万还差5万） - **预估月保费：** $35.00 - **特点：** 保费固定，可转换为终身寿险 - **可选附加险：** 保费豁免、意外身故 - **适合人群：** 需要长期保障的年轻家庭  ---  ## 方案二：Life Te",
  "latest_eligibility": "根据您的需求（30岁、不吸烟、20年期、保额30万美元），我为您找到了以下可选方案：  ---  ## 方案一：Life Term 20（LIFE-TERM20-002）⭐ **最匹配** - **保障期限：** 20年 ✅ - **保额上限：** $250,000（距离您目标的30万还差5万） - **预估月保费：** $35.00 - **特点：** 保费固定，可转换为终身寿险 - **可选附加险：** 保费豁免、意外身故 - **适合人群：** 需要长期保障的年轻家庭  ---  ## 方案二：Life Te",
  "open_questions": [],
  "notes": []
}
```

## Messages
### 1. user
我30岁，不吸烟，想买20年期寿险，保额30万，先帮我比较3个方案。

### 2. assistant
[tool_use] load_skill({"skill_name": "insurance-shopping-coordinator"})

### 3. user
[tool_result:tool_bdx2NZJb7yC7m8gnQOxr6Bo7] [Skill: insurance-shopping-coordinator]

# Insurance Shopping Coordinator

Use specialist subagents for domain-specific insurance tasks and use general tools directly for customer lookup and policy purchase.

## Required behavior

- Identify which insurance line or lines the user is asking about.
- Route domain-specific work to the correct specialist subagent.
- If multiple insurance lines are requested, handle each line separately and then synthesize the results.
- Gather only the minimum information needed to produce a useful recommendation, quote, or eligibility result.
- Prefer showing 2-3 relevant options when the user is shopping, instead of immediately narrowing to one.
- Explain tradeoffs clearly, especially around premium, deductible, coverage limit, eligibility, and riders.
- Only use the purchase tool when the user explicitly confirms they want to buy a specific product.

## Routing rules

- Health insurance questions -> `call_health_agent`
- Auto insurance questions -> `call_auto_agent`
- Home insurance questions -> `call_home_agent`
- Life insurance questions -> `call_life_agent`
- Existing customer lookup by customer ID -> `get_customer_profile`
- Finalized purchase request with confirmed `product_id` and `customer_id` -> `purchase_policy`

## Minimum information by insurance type

- Health:
  - age
  - family size
  - location risk
  - relevant health conditions for eligibility if mentioned
- Auto:
  - driver age
  - vehicle value
  - driving record
- Home:
  - home value
  - location risk
  - home age in years
- Life:
  - age
  - coverage amount
  - smoker status
  - relevant health conditions for eligibility if mentioned

## Default assumptions

Unless the user says otherwise, assume:

- location risk: `medium`
- family size: `1`
- smoker: `false`
- driving record: `clean`
- the user is still comparing options unless they explicitly ask to buy

Use defaults only when they are not likely to change the recommendation too drastically, and briefly mention them when they materially affect a quote.

## Interaction rules

1. Parse the user request for explicit insurance type, budget, coverage preference, age, and other important constraints.
2. Infer safe defaults for missing non-critical fields.
3. Ask follow-up questions only when a missing field blocks a useful search, quote, or eligibility check.
4. For shopping requests, search first, then inspect promising products, then calculate premiums or eligibility when enough information is available.
5. Present 2-3 suitable options when multiple options exist.
6. When the user requests one best recommendation, still explain why it won over the main alternatives.
7. Preserve prior context and constraints across turns unless the user clearly resets the conversation.

## Comparison guidance

When comparing options, emphasize:

- cheapest option
- strongest coverage
- best overall fit for the user's stated needs

When relevant, mention:

- riders worth considering
- deductible versus premium tradeoff
- whether a policy is better for budget sensitivity or broader protection

## Output format

For each recommended option, include when available:

- product ID
- product name
- estimated premium or base premium
- deductible or coverage limit
- best-for summary
- key tradeoff or caution

After listing options, add a short comparison section:

- cheapest option
- strongest coverage
- best overall fit

## Failure handling

- If a quote cannot be produced, explain which missing field is blocking it.
- If eligibility fails, explain the reason briefly and suggest the nearest acceptable alternatives.
- If no options match a preference exactly, present the closest options and explain what assumption or constraint caused the mismatch.
- Never claim a policy has been purchased unless the purchase tool has been called successfully.

## Purchase rules

- Only call `purchase_policy` after explicit user confirmation.
- Before purchase, confirm:
  - the exact `product_id`
  - the `customer_id`
  - that the user intends to proceed now
- If the user has not provided a customer ID, ask for it or use `get_customer_profile` only when a customer ID is available.
- If a domain-specific process implies an inspection or medical exam may be required, mention that requirement before purchase confirmation.

## State management

Maintain the currently active insurance-shopping context throughout the conversation. When the user changes one field, preserve the other known fields unless the user asks to start over.

The skill above has been loaded. Proceed immediately to follow its instructions and call the relevant tools. Do not pause for user confirmation.

### 4. assistant
[tool_use] call_life_agent({"task": "Search for life insurance policies for a 30-year-old non-smoker looking for a 20-year term life policy with $300,000 coverage. Find 2-3 suitable options, get their details, and calculate premiums. Present the comparison with product IDs, names, estimated premiums, coverage limits, and best-for summaries."})

### 5. user
[tool_result:tool_WgZi9o9Bv0AGiFzia0gdVQHC] Based on your search for a 20-year term life policy with $300,000 coverage, here are the available term options and how they compare:

---

## Life Insurance Policy Comparison

| Feature | **Life Term 10** | **Life Term 20** |
|---------|-----------------|------------------|
| **Product ID** | LIFE-TERM10-001 | LIFE-TERM20-002 |
| **Term Length** | 10 years | 20 years |
| **Coverage Limit** | $150,000 | $250,000 |
| **Est. Monthly Premium** *(30, non-smoker)* | $10.80 | $35.00 |
| **Key Features** | Fixed premium | Fixed premium, Convertible to whole life |
| **Riders Available** | Accidental death | Waiver of premium, Accidental death |
| **Best For** | Short-term affordable protection | Young families needing affordable protection |

---

## Important Notes

⚠️ **Coverage Gap**: Neither policy offers your requested $300,000 coverage. The maximum available is $250,000 (Life Term 20).  
⚠️ **Term Mismatch**: Life Term 10 only covers 10 years, not your requested 20-year term.

**Recommendation**: **Life Term 20 (LIFE-TERM20-002)** is your best match — it meets your 20-year term requirement and provides the highest coverage available ($250,000), though it falls short of your $300,000 target. The estimated premium is **$35.00/month**.

If you need the full $300,000 coverage, you may need to:
- Purchase a supplemental policy, or
- Ask if higher coverage tiers are available through underwriting

Would you like me to check your eligibility for the Life Term 20 policy or help you explore next steps?

### 6. assistant
根据您的需求（30岁、不吸烟、20年期、保额30万美元），我为您找到了以下可选方案：

---

## 方案一：Life Term 20（LIFE-TERM20-002）⭐ **最匹配**
- **保障期限：** 20年 ✅
- **保额上限：** $250,000（距离您目标的30万还差5万）
- **预估月保费：** $35.00
- **特点：** 保费固定，可转换为终身寿险
- **可选附加险：** 保费豁免、意外身故
- **适合人群：** 需要长期保障的年轻家庭

---

## 方案二：Life Term 10（LIFE-TERM10-001）
- **保障期限：** 10年 ❌（不符合您的20年需求）
- **保额上限：** $150,000
- **预估月保费：** $10.80
- **特点：** 短期低价保障
- **可选附加险：** 意外身故
- **适合人群：** 预算有限、只需短期保障

---

## ⚠️ 重要说明

目前系统中**最高保额为$250,000**，无法完全满足您$300,000的需求。如果您坚持需要30万保额，建议：

1. **选择Life Term 20** 作为主险（$250,000），再补充一份$50,000的附加保单
2. 或让我帮您检查是否有更高保额可通过核保申请

---

## 对比总结

| 维度 | 最优选择 |
|------|---------|
| **最符合期限** | Life Term 20（20年）|
| **最高保额** | Life Term 20（$250,000）|
| **最低保费** | Life Term 10（$10.80/月）|
| **综合最佳** | **Life Term 20** — 满足您的核心需求（20年期），保额最接近目标 |

---

您希望我先帮您**核保Life Term 20**，还是想了解如何**补充保额到30万**的方案？
