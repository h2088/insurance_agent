import json
import random
from datetime import datetime

# ── Extended insurance product catalog (mock data) ───────────────────────────

INSURANCE_PRODUCTS = {
    # Health
    "HLTH-BASIC-001": {
        "name": "Health Basic",
        "category": "health",
        "monthly_premium_base": 120,
        "deductible": 2500,
        "coverage_limit": 500000,
        "network_size": "medium",
        "features": ["Primary care", "Emergency room", "Generic prescriptions"],
        "riders": ["Dental", "Vision"],
        "best_for": "Individuals on a tight budget"
    },
    "HLTH-SILVER-002": {
        "name": "Health Silver",
        "category": "health",
        "monthly_premium_base": 220,
        "deductible": 1500,
        "coverage_limit": 750000,
        "network_size": "large",
        "features": ["Primary care", "Specialist visits", "Hospitalization", "Generic prescriptions"],
        "riders": ["Dental", "Vision", "Mental health"],
        "best_for": "Young professionals"
    },
    "HLTH-FAMILY-003": {
        "name": "Health Family",
        "category": "health",
        "monthly_premium_base": 340,
        "deductible": 1200,
        "coverage_limit": 1000000,
        "network_size": "large",
        "features": ["Primary care", "Specialist visits", "Maternity", "Pediatric dental", "Vision"],
        "riders": ["Orthodontics", "Mental health", "Wellness programs"],
        "best_for": "Families with children"
    },
    "HLTH-PREM-004": {
        "name": "Health Premium",
        "category": "health",
        "monthly_premium_base": 520,
        "deductible": 500,
        "coverage_limit": 2000000,
        "network_size": "nationwide",
        "features": ["All family features", "Mental health", "Wellness programs", "Concierge care"],
        "riders": ["International coverage", "Alternative medicine"],
        "best_for": "Those wanting comprehensive coverage"
    },
    # Auto
    "AUTO-LIAB-001": {
        "name": "Auto Liability Only",
        "category": "auto",
        "monthly_premium_base": 45,
        "deductible": None,
        "coverage_limit": 50000,
        "features": ["Liability"],
        "riders": ["Uninsured motorist"],
        "best_for": "Minimum legal coverage"
    },
    "AUTO-SAFE-002": {
        "name": "Auto SafeDriver",
        "category": "auto",
        "monthly_premium_base": 85,
        "deductible": 1000,
        "coverage_limit": 100000,
        "features": ["Liability", "Collision", "Roadside assistance"],
        "riders": ["Rental car", "Glass coverage"],
        "best_for": "Safe drivers with clean records"
    },
    "AUTO-STD-003": {
        "name": "Auto Standard",
        "category": "auto",
        "monthly_premium_base": 110,
        "deductible": 750,
        "coverage_limit": 150000,
        "features": ["Liability", "Collision", "Comprehensive"],
        "riders": ["Roadside assistance", "Rental car"],
        "best_for": "Average drivers"
    },
    "AUTO-PREM-004": {
        "name": "Auto TotalProtect",
        "category": "auto",
        "monthly_premium_base": 145,
        "deductible": 500,
        "coverage_limit": 300000,
        "features": ["Liability", "Collision", "Comprehensive", "Rental car", "Roadside assistance"],
        "riders": ["New car replacement", "Gap insurance"],
        "best_for": "Drivers wanting full protection"
    },
    # Home
    "HOME-BASIC-001": {
        "name": "Home Essentials",
        "category": "home",
        "monthly_premium_base": 65,
        "deductible": 2500,
        "coverage_limit": 150000,
        "features": ["Dwelling", "Personal property", "Liability"],
        "riders": ["Sewer backup"],
        "best_for": "First-time homeowners"
    },
    "HOME-STD-002": {
        "name": "Home Standard",
        "category": "home",
        "monthly_premium_base": 95,
        "deductible": 1500,
        "coverage_limit": 300000,
        "features": ["Dwelling", "Personal property", "Liability", "Loss of use"],
        "riders": ["Water damage", "Identity theft"],
        "best_for": "Average homeowners"
    },
    "HOME-PREM-003": {
        "name": "Home Premium",
        "category": "home",
        "monthly_premium_base": 160,
        "deductible": 1000,
        "coverage_limit": 600000,
        "features": ["Dwelling", "Personal property", "Liability", "Flood", "Identity theft protection"],
        "riders": ["Earthquake", "Valuable items"],
        "best_for": "Homeowners with high-value properties"
    },
    "HOME-LUX-004": {
        "name": "Home Luxury",
        "category": "home",
        "monthly_premium_base": 280,
        "deductible": 500,
        "coverage_limit": 1200000,
        "features": ["All premium features", "Landscaping", "Pool", "Guest house"],
        "riders": ["Fine art", "Wine collection", "Cyber home protection"],
        "best_for": "Luxury estate owners"
    },
    # Life
    "LIFE-TERM10-001": {
        "name": "Life Term 10",
        "category": "life",
        "monthly_premium_base": 18,
        "coverage_limit": 150000,
        "features": ["10-year term", "Fixed premium"],
        "riders": ["Accidental death"],
        "best_for": "Short-term affordable protection"
    },
    "LIFE-TERM20-002": {
        "name": "Life Term 20",
        "category": "life",
        "monthly_premium_base": 35,
        "coverage_limit": 250000,
        "features": ["20-year term", "Fixed premium", "Convertible to whole life"],
        "riders": ["Waiver of premium", "Accidental death"],
        "best_for": "Young families needing affordable protection"
    },
    "LIFE-WHOLE-003": {
        "name": "Life Whole Secure",
        "category": "life",
        "monthly_premium_base": 210,
        "coverage_limit": 500000,
        "features": ["Lifetime coverage", "Cash value accumulation", "Dividend eligible"],
        "riders": ["Long-term care rider", "Disability income"],
        "best_for": "Long-term financial planning"
    },
    "LIFE-UNIV-004": {
        "name": "Life Universal Flex",
        "category": "life",
        "monthly_premium_base": 145,
        "coverage_limit": 400000,
        "features": ["Flexible premiums", "Adjustable death benefit", "Cash value growth tied to market index"],
        "riders": ["Guaranteed insurability", "Long-term care rider"],
        "best_for": "Those wanting flexibility"
    },
}

CUSTOMER_DB = {
    "CUST-001": {"age": 28, "health_status": "excellent", "location": "New York, NY", "family_size": 1, "driving_record": "clean"},
    "CUST-002": {"age": 42, "health_status": "good", "location": "Austin, TX", "family_size": 4, "driving_record": "minor violation"},
    "CUST-003": {"age": 55, "health_status": "fair", "location": "Miami, FL", "family_size": 2, "driving_record": "clean"},
}

# Mock in-memory claim storage
CLAIMS_DB = {}

# ── Extended tool definitions ────────────────────────────────────────────────

tools = [
    # ── Health tools ─────────────────────────────────────────────────────────
    {
        "name": "search_health_plans",
        "description": "Search available health insurance plans. Returns plan IDs, names, base premiums, and brief summaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "budget_tier": {"type": "string", "enum": ["basic", "standard", "premium"], "description": "Optional budget filter"}
            },
            "required": []
        }
    },
    {
        "name": "get_health_plan_details",
        "description": "Get detailed information about a specific health insurance plan.",
        "input_schema": {
            "type": "object",
            "properties": {"plan_id": {"type": "string"}},
            "required": ["plan_id"]
        }
    },
    {
        "name": "calculate_health_premium",
        "description": "Calculate estimated monthly health premium based on age, family size, and location risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "age": {"type": "integer"},
                "family_size": {"type": "integer"},
                "location_risk": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["plan_id", "age", "family_size", "location_risk"]
        }
    },
    {
        "name": "check_health_eligibility",
        "description": "Check eligibility for a health plan based on pre-existing conditions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "health_conditions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["plan_id", "health_conditions"]
        }
    },
    {
        "name": "add_health_rider",
        "description": "Add a rider to a health plan and return updated premium estimate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "rider_name": {"type": "string"},
                "base_premium": {"type": "number"}
            },
            "required": ["plan_id", "rider_name", "base_premium"]
        }
    },
    # ── Auto tools ───────────────────────────────────────────────────────────
    {
        "name": "search_auto_policies",
        "description": "Search available auto insurance policies. Returns policy IDs, names, base premiums, and brief summaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "coverage_level": {"type": "string", "enum": ["minimum", "standard", "full"], "description": "Optional coverage filter"}
            },
            "required": []
        }
    },
    {
        "name": "get_auto_policy_details",
        "description": "Get detailed information about a specific auto insurance policy.",
        "input_schema": {
            "type": "object",
            "properties": {"policy_id": {"type": "string"}},
            "required": ["policy_id"]
        }
    },
    {
        "name": "calculate_auto_premium",
        "description": "Calculate estimated monthly auto premium based on driver age, vehicle value, and driving record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "driver_age": {"type": "integer"},
                "vehicle_value": {"type": "number"},
                "driving_record": {"type": "string", "enum": ["clean", "minor violation", "major violation"]}
            },
            "required": ["policy_id", "driver_age", "vehicle_value", "driving_record"]
        }
    },
    {
        "name": "check_auto_eligibility",
        "description": "Check eligibility for an auto policy based on driving history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "driving_record": {"type": "string", "enum": ["clean", "minor violation", "major violation"]}
            },
            "required": ["policy_id", "driving_record"]
        }
    },
    {
        "name": "add_auto_rider",
        "description": "Add a rider to an auto policy and return updated premium estimate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "rider_name": {"type": "string"},
                "base_premium": {"type": "number"}
            },
            "required": ["policy_id", "rider_name", "base_premium"]
        }
    },
    # ── Home tools ───────────────────────────────────────────────────────────
    {
        "name": "search_home_policies",
        "description": "Search available home insurance policies. Returns policy IDs, names, base premiums, and brief summaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "home_value_tier": {"type": "string", "enum": ["budget", "standard", "luxury"], "description": "Optional home value filter"}
            },
            "required": []
        }
    },
    {
        "name": "get_home_policy_details",
        "description": "Get detailed information about a specific home insurance policy.",
        "input_schema": {
            "type": "object",
            "properties": {"policy_id": {"type": "string"}},
            "required": ["policy_id"]
        }
    },
    {
        "name": "calculate_home_premium",
        "description": "Calculate estimated monthly home premium based on home value, location risk, and home age.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "home_value": {"type": "number"},
                "location_risk": {"type": "string", "enum": ["low", "medium", "high"]},
                "home_age_years": {"type": "integer"}
            },
            "required": ["policy_id", "home_value", "location_risk", "home_age_years"]
        }
    },
    {
        "name": "schedule_home_inspection",
        "description": "Schedule a home inspection before binding a home policy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "address": {"type": "string"},
                "preferred_date": {"type": "string"}
            },
            "required": ["policy_id", "address", "preferred_date"]
        }
    },
    {
        "name": "add_home_rider",
        "description": "Add a rider to a home policy and return updated premium estimate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "rider_name": {"type": "string"},
                "base_premium": {"type": "number"}
            },
            "required": ["policy_id", "rider_name", "base_premium"]
        }
    },
    # ── Life tools ───────────────────────────────────────────────────────────
    {
        "name": "search_life_policies",
        "description": "Search available life insurance policies. Returns policy IDs, names, base premiums, and brief summaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_type": {"type": "string", "enum": ["term", "whole", "universal"], "description": "Optional policy type filter"}
            },
            "required": []
        }
    },
    {
        "name": "get_life_policy_details",
        "description": "Get detailed information about a specific life insurance policy.",
        "input_schema": {
            "type": "object",
            "properties": {"policy_id": {"type": "string"}},
            "required": ["policy_id"]
        }
    },
    {
        "name": "calculate_life_premium",
        "description": "Calculate estimated monthly life premium based on age, coverage amount, and smoker status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "age": {"type": "integer"},
                "coverage_amount": {"type": "number"},
                "smoker": {"type": "boolean"}
            },
            "required": ["policy_id", "age", "coverage_amount", "smoker"]
        }
    },
    {
        "name": "check_life_eligibility",
        "description": "Check eligibility for a life policy based on age and serious health conditions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "age": {"type": "integer"},
                "health_conditions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["policy_id", "age", "health_conditions"]
        }
    },
    {
        "name": "schedule_medical_exam",
        "description": "Schedule a medical exam required for certain life insurance policies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "applicant_name": {"type": "string"},
                "preferred_date": {"type": "string"}
            },
            "required": ["policy_id", "applicant_name", "preferred_date"]
        }
    },
    # ── Claim tools ──────────────────────────────────────────────────────────
    {
        "name": "file_claim",
        "description": "Submit a new insurance claim. Returns a claim reference number and acknowledgment. Use when the user reports an incident and wants to file a claim.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insurance_type": {
                    "type": "string",
                    "enum": ["health", "auto", "home", "life"],
                    "description": "Type of insurance claim"
                },
                "policy_id": {
                    "type": "string",
                    "description": "Policy or product ID associated with the claim"
                },
                "incident_date": {
                    "type": "string",
                    "description": "Date of the incident in YYYY-MM-DD format"
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what happened"
                },
                "claim_amount": {
                    "type": "number",
                    "description": "Estimated claim amount in USD (optional)"
                }
            },
            "required": ["insurance_type", "policy_id", "incident_date", "description"]
        }
    },
    {
        "name": "check_claim_status",
        "description": "Check the status of an existing claim by its claim reference number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_reference": {
                    "type": "string",
                    "description": "Claim reference number (e.g. CLM-20260421-123456)"
                }
            },
            "required": ["claim_reference"]
        }
    },
    # ── General tools ────────────────────────────────────────────────────────
    {
        "name": "get_customer_profile",
        "description": "Retrieve an existing customer's profile by customer ID.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"]
        }
    },
    {
        "name": "purchase_policy",
        "description": "Purchase a policy for a customer and return a policy number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "customer_id": {"type": "string"}
            },
            "required": ["product_id", "customer_id"]
        }
    },
]

# ── Tool execution dispatcher ────────────────────────────────────────────────

def execute_function_call(tool_call):
    """Execute insurance tool calls against mock data."""
    name = tool_call.name
    args = tool_call.input

    def _get_product(pid, expected_category=None):
        product = INSURANCE_PRODUCTS.get(pid)
        if not product:
            return None, f"Product '{pid}' not found."
        if expected_category and product["category"] != expected_category:
            return None, f"Product '{pid}' is not a {expected_category} product."
        return product, None

    def _search(category, budget_tier=None, coverage_level=None, home_value_tier=None, policy_type=None):
        matches = []
        for pid, p in INSURANCE_PRODUCTS.items():
            if p["category"] != category:
                continue
            # simple tier mapping
            tier_ok = True
            if budget_tier:
                base = p["monthly_premium_base"]
                tier_map = {"basic": base <= 150, "standard": 150 < base <= 300, "premium": base > 300}
                tier_ok = tier_map.get(budget_tier, True)
            if coverage_level:
                features = p.get("features", [])
                cov_map = {
                    "minimum": len(features) <= 2,
                    "standard": 2 < len(features) <= 4,
                    "full": len(features) >= 4
                }
                tier_ok = cov_map.get(coverage_level, True)
            if home_value_tier:
                limit = p.get("coverage_limit", 0)
                hvt_map = {"budget": limit <= 200000, "standard": 200000 < limit <= 600000, "luxury": limit > 600000}
                tier_ok = hvt_map.get(home_value_tier, True)
            if policy_type:
                tier_ok = policy_type.lower() in p["name"].lower()
            if tier_ok:
                matches.append({
                    "product_id": pid,
                    "name": p["name"],
                    "monthly_premium_base": p["monthly_premium_base"],
                    "best_for": p["best_for"]
                })
        return json.dumps(matches, indent=2)

    def _details(pid):
        p, error = _get_product(pid)
        if error:
            return error
        return json.dumps(p, indent=2)

    def _add_rider(pid, rider_name, base_premium):
        p, error = _get_product(pid)
        if error:
            return error
        if rider_name not in p.get("riders", []):
            return f"Rider '{rider_name}' not available for {p['name']}. Available riders: {', '.join(p.get('riders', []))}"
        new_premium = round(base_premium * 1.12, 2)
        return json.dumps({
            "product_id": pid,
            "product_name": p["name"],
            "added_rider": rider_name,
            "updated_monthly_premium": new_premium
        }, indent=2)

    # ── Health handlers ────────────────────────────────────────────────────
    if name == "search_health_plans":
        return _search("health", budget_tier=args.get("budget_tier"))
    elif name == "get_health_plan_details":
        return _details(args["plan_id"])
    elif name == "calculate_health_premium":
        product, error = _get_product(args["plan_id"], "health")
        if error:
            return error
        base = product["monthly_premium_base"]
        age_factor = 1.0 + max(0, (args["age"] - 30)) * 0.015
        family_factor = 1.0 + (args["family_size"] - 1) * 0.45
        risk_factor = {"low": 0.9, "medium": 1.0, "high": 1.15}.get(args["location_risk"], 1.0)
        estimated = round(base * age_factor * family_factor * risk_factor, 2)
        return json.dumps({"plan_id": args["plan_id"], "estimated_monthly_premium": estimated}, indent=2)
    elif name == "check_health_eligibility":
        blocked = {"cancer", "heart disease", "kidney failure", "end stage renal disease"}
        issues = [c for c in args["health_conditions"] if c.lower() in blocked]
        if issues:
            return f"Ineligible for {args['plan_id']} due to: {', '.join(issues)}."
        return f"Eligible for {args['plan_id']}. No issues found."
    elif name == "add_health_rider":
        return _add_rider(args["plan_id"], args["rider_name"], args["base_premium"])

    # ── Auto handlers ──────────────────────────────────────────────────────
    elif name == "search_auto_policies":
        return _search("auto", coverage_level=args.get("coverage_level"))
    elif name == "get_auto_policy_details":
        return _details(args["policy_id"])
    elif name == "calculate_auto_premium":
        product, error = _get_product(args["policy_id"], "auto")
        if error:
            return error
        base = product["monthly_premium_base"]
        age_factor = 1.0 + max(0, (args["driver_age"] - 30)) * 0.02
        value_factor = 1.0 + (args["vehicle_value"] / 50000) * 0.1
        record_factor = {"clean": 0.9, "minor violation": 1.1, "major violation": 1.4}.get(args["driving_record"], 1.0)
        estimated = round(base * age_factor * value_factor * record_factor, 2)
        return json.dumps({"policy_id": args["policy_id"], "estimated_monthly_premium": estimated}, indent=2)
    elif name == "check_auto_eligibility":
        if args["driving_record"] == "major violation":
            return f"Ineligible for {args['policy_id']} due to major driving violation."
        return f"Eligible for {args['policy_id']}."
    elif name == "add_auto_rider":
        return _add_rider(args["policy_id"], args["rider_name"], args["base_premium"])

    # ── Home handlers ──────────────────────────────────────────────────────
    elif name == "search_home_policies":
        return _search("home", home_value_tier=args.get("home_value_tier"))
    elif name == "get_home_policy_details":
        return _details(args["policy_id"])
    elif name == "calculate_home_premium":
        product, error = _get_product(args["policy_id"], "home")
        if error:
            return error
        base = product["monthly_premium_base"]
        value_factor = 1.0 + (args["home_value"] / 300000) * 0.15
        risk_factor = {"low": 0.85, "medium": 1.0, "high": 1.25}.get(args["location_risk"], 1.0)
        age_factor = 1.0 + (args["home_age_years"] / 50) * 0.2
        estimated = round(base * value_factor * risk_factor * age_factor, 2)
        return json.dumps({"policy_id": args["policy_id"], "estimated_monthly_premium": estimated}, indent=2)
    elif name == "schedule_home_inspection":
        confirmation = f"INS-HOME-{random.randint(10000,99999)}"
        return (
            f"Home inspection scheduled for {args['policy_id']} at {args['address']} "
            f"on {args['preferred_date']}. Confirmation: {confirmation}"
        )
    elif name == "add_home_rider":
        return _add_rider(args["policy_id"], args["rider_name"], args["base_premium"])

    # ── Life handlers ──────────────────────────────────────────────────────
    elif name == "search_life_policies":
        return _search("life", policy_type=args.get("policy_type"))
    elif name == "get_life_policy_details":
        return _details(args["policy_id"])
    elif name == "calculate_life_premium":
        product, error = _get_product(args["policy_id"], "life")
        if error:
            return error
        base = product["monthly_premium_base"]
        age_factor = 1.0 + max(0, (args["age"] - 30)) * 0.025
        coverage_factor = args["coverage_amount"] / 250000
        smoker_factor = 1.6 if args["smoker"] else 1.0
        estimated = round(base * age_factor * coverage_factor * smoker_factor, 2)
        return json.dumps({"policy_id": args["policy_id"], "estimated_monthly_premium": estimated}, indent=2)
    elif name == "check_life_eligibility":
        blocked = {"cancer", "heart disease", "als", "hiv/aids"}
        issues = [c for c in args["health_conditions"] if c.lower() in blocked]
        if args["age"] > 75:
            return f"Ineligible for {args['policy_id']} due to age over 75."
        if issues:
            return f"Ineligible for {args['policy_id']} due to: {', '.join(issues)}."
        return f"Eligible for {args['policy_id']}."
    elif name == "schedule_medical_exam":
        confirmation = f"INS-LIFE-{random.randint(10000,99999)}"
        return (
            f"Medical exam scheduled for {args['policy_id']} for applicant {args['applicant_name']} "
            f"on {args['preferred_date']}. Confirmation: {confirmation}"
        )

    # ── Claim handlers ─────────────────────────────────────────────────────
    elif name == "file_claim":
        insurance_type = args["insurance_type"]
        policy_id = args["policy_id"]
        incident_date = args["incident_date"]
        description = args["description"]
        claim_amount = args.get("claim_amount")
        claim_ref = f"CLM-{incident_date.replace('-', '')}-{random.randint(100000, 999999)}"
        CLAIMS_DB[claim_ref] = {
            "claim_reference": claim_ref,
            "insurance_type": insurance_type,
            "policy_id": policy_id,
            "incident_date": incident_date,
            "description": description,
            "claim_amount": claim_amount,
            "status": "submitted",
            "submitted_at": datetime.now().isoformat(),
        }
        return json.dumps({
            "claim_reference": claim_ref,
            "status": "submitted",
            "message": f"Claim filed successfully. Reference: {claim_ref}. A claims adjuster will review within 3-5 business days."
        }, indent=2)
    elif name == "check_claim_status":
        claim_ref = args["claim_reference"]
        claim = CLAIMS_DB.get(claim_ref)
        if not claim:
            return f"Claim '{claim_ref}' not found. Please verify the reference number."
        return json.dumps(claim, indent=2)

    # ── General handlers ───────────────────────────────────────────────────
    elif name == "get_customer_profile":
        cust = CUSTOMER_DB.get(args["customer_id"])
        if not cust:
            return f"Customer {args['customer_id']} not found."
        return json.dumps(cust, indent=2)
    elif name == "purchase_policy":
        product, error = _get_product(args["product_id"])
        if error:
            return error
        if args["customer_id"] not in CUSTOMER_DB:
            return f"Customer {args['customer_id']} not found."
        policy_number = f"POL-{random.randint(100000, 999999)}"
        return (
            f"Policy purchased successfully! Policy number: {policy_number} | "
            f"Product: {product['name']} ({args['product_id']}) | Customer: {args['customer_id']}"
        )

    return "Function not implemented"
