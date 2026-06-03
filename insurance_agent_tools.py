import random


tools = [
    {
        "name": "get_customer_profile",
        "description": "Get basic customer information such as age, location, and health status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Unique customer identifier."
                }
            },
            "required": ["customer_id"],
            "additionalProperties": False
        }
    },
    {
        "name": "compare_products",
        "description": "Compare available insurance products based on type, coverage amount, and optional features.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insurance_type": {
                    "type": "string",
                    "enum": ["life", "health", "auto", "home"],
                    "description": "Category of insurance product."
                },
                "coverage_amount": {
                    "type": "number",
                    "description": "Desired coverage amount in USD."
                },
                "term_years": {
                    "type": "number",
                    "description": "Policy term in years (optional)."
                }
            },
            "required": ["insurance_type", "coverage_amount"],
            "additionalProperties": False
        }
    },
    {
        "name": "get_quote",
        "description": "Get a premium quote for a specific insurance product given customer details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Identifier of the insurance product."
                },
                "customer_age": {
                    "type": "number",
                    "description": "Customer age in years."
                },
                "smoker": {
                    "type": "boolean",
                    "description": "Whether the customer is a smoker."
                }
            },
            "required": ["product_id", "customer_age", "smoker"],
            "additionalProperties": False
        }
    },
    {
        "name": "check_eligibility",
        "description": "Check whether a customer is eligible for a given insurance product based on health conditions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Identifier of the insurance product."
                },
                "health_conditions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of pre-existing health conditions."
                }
            },
            "required": ["product_id", "health_conditions"],
            "additionalProperties": False
        }
    },
    {
        "name": "purchase_policy",
        "description": "Purchase an insurance policy for the customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Identifier of the insurance product."
                },
                "customer_id": {
                    "type": "string",
                    "description": "Unique customer identifier."
                }
            },
            "required": ["product_id", "customer_id"],
            "additionalProperties": False
        }
    }
]


# Mock in-memory product catalog
PRODUCT_CATALOG = {
    "life": [
        {"product_id": "LIFE-BASIC-001", "name": "Life Basic", "base_premium": 25, "features": ["term life", "no medical exam"]},
        {"product_id": "LIFE-PLUS-002", "name": "Life Plus", "base_premium": 45, "features": ["whole life", "cash value"]},
    ],
    "health": [
        {"product_id": "HLTH-SILVER-001", "name": "Health Silver", "base_premium": 120, "features": ["hospitalization", "outpatient care"]},
        {"product_id": "HLTH-GOLD-002", "name": "Health Gold", "base_premium": 220, "features": ["dental", "vision", "mental health"]},
    ],
    "auto": [
        {"product_id": "AUTO-STD-001", "name": "Auto Standard", "base_premium": 80, "features": ["liability", "collision"]},
        {"product_id": "AUTO-PREM-002", "name": "Auto Premium", "base_premium": 150, "features": ["comprehensive", "roadside assistance"]},
    ],
    "home": [
        {"product_id": "HOME-BASIC-001", "name": "Home Basic", "base_premium": 60, "features": ["fire", "theft"]},
        {"product_id": "HOME-PREM-002", "name": "Home Premium", "base_premium": 110, "features": ["flood", "natural disaster", "contents cover"]},
    ],
}


def execute_function_call(tool_call):
    """Execute the function call and return the result"""
    tool_call_name = tool_call.name
    arguments = tool_call.input

    if tool_call_name == "get_customer_profile":
        customer_id = arguments["customer_id"]
        ages = [28, 35, 42, 51, 64]
        statuses = ["excellent", "good", "fair"]
        return (
            f"Customer profile for {customer_id}: age {random.choice(ages)}, "
            f"health status {random.choice(statuses)}, location New York, NY"
        )

    elif tool_call_name == "compare_products":
        insurance_type = arguments["insurance_type"]
        coverage_amount = arguments["coverage_amount"]
        term_years = arguments.get("term_years")
        products = PRODUCT_CATALOG.get(insurance_type, [])
        if not products:
            return f"No products found for insurance type '{insurance_type}'."
        lines = [f"Comparing {insurance_type} insurance products for ${coverage_amount:,.0f} coverage"]
        if term_years:
            lines.append(f"Term: {term_years} years")
        for p in products:
            lines.append(
                f"- {p['product_id']}: {p['name']} (base premium ${p['base_premium']}/mo) | Features: {', '.join(p['features'])}"
            )
        return "\n".join(lines)

    elif tool_call_name == "get_quote":
        product_id = arguments["product_id"]
        customer_age = arguments["customer_age"]
        smoker = arguments["smoker"]
        # Simple mock pricing logic
        base = 100
        for category in PRODUCT_CATALOG.values():
            for p in category:
                if p["product_id"] == product_id:
                    base = p["base_premium"]
                    break
        age_factor = 1 + (customer_age - 30) * 0.02
        smoker_factor = 1.5 if smoker else 1.0
        premium = round(base * age_factor * smoker_factor, 2)
        return f"Quote for {product_id}: ${premium}/month (age={customer_age}, smoker={smoker})"

    elif tool_call_name == "check_eligibility":
        product_id = arguments["product_id"]
        health_conditions = arguments["health_conditions"]
        blocked_conditions = {"cancer", "heart disease", "kidney failure"}
        issues = [c for c in health_conditions if c.lower() in blocked_conditions]
        if issues:
            return f"Ineligible for {product_id} due to conditions: {', '.join(issues)}."
        return f"Eligible for {product_id}. No issues found with provided health conditions."

    elif tool_call_name == "purchase_policy":
        product_id = arguments["product_id"]
        customer_id = arguments["customer_id"]
        policy_number = f"POL-{random.randint(100000, 999999)}"
        return (
            f"Policy purchased successfully! Policy number: {policy_number} | "
            f"Product: {product_id} | Customer: {customer_id}"
        )

    return "Function not implemented"
