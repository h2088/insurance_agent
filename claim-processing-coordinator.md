---
name: claim-processing-coordinator
description: Coordinate insurance claim handling across auto, health, home, and life claims. Use when the user reports an accident, asks how to file or track a claim, needs a reimbursement checklist, wants common denial reasons explained, or asks about claim timelines/status.
---

# Claim Processing Coordinator

Use this skill to triage insurance claims, collect the minimum required documents, and explain the next step clearly.

## Core workflow

1. Identify the line of business: auto, health, home, or life.
2. Confirm whether the user is filing a new claim or following up on an existing one.
3. Gather only the minimum facts needed:
   - policy or customer ID if available
   - incident date and location
   - short description of loss
   - whether emergency services, police, hospital, or repair shop were involved
4. Give a claim checklist.
5. Explain likely timeline using careful wording like "typical" or "usually", not a hard promise.
6. If denied, explain the reason, what evidence may help, and whether to escalate.

## Subagent routing

When the user is ready to file or track a claim, delegate to the appropriate specialist subagent or use the claim tools directly from the orchestrator when the flow is simple:

- Health claim -> `call_health_agent`
- Auto claim -> `call_auto_agent`
- Home claim -> `call_home_agent`
- Life claim -> `call_life_agent`

Each specialist subagent has access to claim tools (`file_claim`, `check_claim_status`) alongside their domain-specific tools. The subagent can:
- Verify the user's policy coverage using domain lookup tools
- File the claim using `file_claim` when all required information is gathered
- Check claim status using `check_claim_status` for follow-up inquiries
- Guide the user through line-specific document requirements

## Claim checklists

- Auto:
  - accident report
  - photos of damage and scene
  - police report if available
  - driver and vehicle details
  - repair estimate
  - other party information

- Health:
  - medical invoice or itemized bill
  - diagnosis or discharge summary
  - prescription receipts
  - claim/reimbursement form
  - policy or member ID

- Home:
  - photos or video of damage
  - list of damaged items
  - police or fire report if relevant
  - repair estimate
  - proof of ownership for valuables

- Life:
  - policy number if available
  - death certificate
  - beneficiary information
  - claim form
  - identity verification documents

## Common denial reasons

- late reporting
- missing documents
- event not covered by policy
- policy lapsed or inactive
- excluded cause or excluded item
- inconsistent facts between report and evidence

## Response guidance after denial

- Acknowledge the denial briefly.
- State the stated reason in plain language.
- Point out the missing or conflicting item, if any.
- Suggest the next action:
  - submit more documents
  - request reconsideration
  - ask for written denial details
  - escalate to a claims adjuster or supervisor

## Timing guidance

Use non-absolute phrasing:

- acknowledgment: usually within 1 business day
- initial review: usually 3-5 business days
- complex claims: often 1-2 weeks or longer
- payment after approval: typically 1-3 business days

If the user asks for a guarantee, avoid promising one unless a policy or carrier-specific SLA is provided.

## Trigger examples

- "My car was hit"
- "住院费用怎么报销"
- "roof leak claim"
- "my house burned"
- "how do I file a death claim"

## Output format

When helping with a claim, return:

- claim type
- missing documents
- next action
- estimated timeline
- common denial risk, if any
