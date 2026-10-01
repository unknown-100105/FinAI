# FinAI XAI Dashboard Specification

## 1. Purpose

The FinAI XAI Dashboard exposes how a financial request is processed, what authority was used, what result was verified, which model generated the explanation, and whether the generated claims passed verification.

The dashboard is an observability and explainability layer. It does not make financial decisions or authorize actions.

## 2. End-to-End Trace

User Request
    ↓
Input / Language
    ↓
Safety Precheck
    ↓
Intent Router
    ↓
Router Confidence
    ↓
Risk / Policy Controller
    ↓
Authority Contract
    ↓
Execution Capability
    ↓
Finance Engine / Tool Engine / RAG
    ↓
Verified Result
    ↓
Selected Model
    ↓
Response Generation
    ↓
Claim Extraction
    ↓
Claim Verification
    ↓
Fallback / Final Response
    ↓
Final XAI Trace

## 3. Dashboard Sections

### A. Request

Display:
- User request
- Detected language
- Persona
- Timestamp
- Session/turn identifier

### B. Intent

Display:
- Intent
- Router confidence
- Router margin
- Router decision
- UNKNOWN / clarification state when applicable

### C. Risk and Policy

Display:
- Risk level
- Category
- Authentication required
- Confirmation required
- Policy decision
- Authority class
- Authority source

### D. Execution

Display:
- Capability selected
- Execution class
- Component used
- Tool name when applicable
- Finance engine service when applicable
- RAG source when applicable
- Execution status

### E. Verified Result

Display:
- Authoritative result fields
- Source of each result
- Verification state
- Calculation/tool provenance

### F. Model

Display:
- Model ID
- Model role
- Model capabilities
- Generation status
- Generation latency
- Generated tokens
- Tokens per second

### G. Claims

For each extracted model claim display:
- Field
- Proposed value
- Claim type
- Authority source
- Verification status
- Verification reason

Supported claim types:
- CALCULATED
- TOOL_VERIFIED
- RETRIEVED
- USER_PROVIDED
- MODEL_INFERRED
- UNVERIFIED

Verification statuses:
- VERIFIED
- PENDING
- REJECTED
- NOT_APPLICABLE

### H. Final Response

Display:
- Final response
- Response status
- Generated vs fallback
- Verification outcome
- Any rejected or corrected claims

## 4. Key Safety Principle

The LLM is not an authority.

The dashboard must clearly distinguish:

Authoritative:
- deterministic finance calculations
- verified tool results
- retrieved evidence
- explicitly user-provided values

Non-authoritative:
- model-generated explanations
- model-inferred claims

The LLM cannot authorize sensitive actions.

## 5. Suggested Visual Flow

Use a horizontal or vertical trace:

REQUEST
  |
INTENT
  |
POLICY
  |
AUTHORITY
  |
EXECUTION
  |
VERIFIED RESULT
  |
MODEL
  |
CLAIMS
  |
VERIFICATION
  |
FINAL RESPONSE

Each stage should expose a compact status indicator and allow expansion for details.

## 6. Important Metrics

The dashboard should support:

- Router confidence
- Risk level
- Execution latency
- Model latency
- Verification status
- Number of claims
- Number of verified claims
- Number of rejected claims
- Number of unsupported claims
- Fallback usage
- Model ID
- Authority source

## 7. Example: EMI Query

User:
"Calculate EMI for ₹10 lakh at 8.5% for 20 years."

Intent:
EMI_QUERY

Authority:
deterministic_finance_engine

Verified result:
- Principal: ₹1,000,000
- Annual rate: 8.5%
- Tenure: 240 months
- Monthly EMI: ₹8,678.23
- Total payment: ₹2,082,775.76
- Total interest: ₹1,082,775.76

Model:
rLLM-FinQA-4B

Claim verification:
- Monthly EMI → VERIFIED
- Total payment → VERIFIED
- Total interest → VERIFIED

Final response:
Generated explanation using verified values.

## 8. Example: Lost Card

User:
"I lost my card."

Expected trace:

Intent:
CARD_LOST

Risk:
HIGH

Authentication:
REQUIRED

Confirmation:
REQUIRED

Authority:
policy + authorized tool

Action:
block_card

The model must not independently execute or authorize the action.

## 9. Frontend Requirement

The XAI dashboard should never expose secrets, credentials, authentication tokens, or real banking data.

Current project demonstrations use synthetic/mock financial data.

## 10. Future API Contract

The frontend should eventually consume a structured XAI trace containing:

- request
- router
- policy
- authority
- execution
- verified_result
- model
- claims
- verification
- final_response

The existing XAITrace and claim-verification architecture should be reused rather than duplicated.

## 11. Implementation Order

1. Backend XAI trace API
2. Trace JSON schema
3. Frontend trace viewer
4. Claim verification panel
5. Execution/authority panel
6. Model information panel
7. Timeline visualization
8. Final integration testing
