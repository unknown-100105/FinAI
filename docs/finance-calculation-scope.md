# Financial calculation scope and assumptions

## Active chat calculations

The active `FinanceDispatcher` chat path currently supports:
- `EMI_QUERY`: deterministic EMI calculation.
- `INTEREST_QUERY`: deterministic compound-interest calculation.

The `SIPService` exists and can be invoked directly by application code, but `SIP_QUERY` is not in the active trained intent taxonomy and is not dispatched through the normal chat path. Do not describe SIP calculation as a supported chat capability until the intent, parameter extraction, policy, dispatch, and end-to-end tests are added.

## Calculation assumptions

- **EMI:** fixed nominal annual rate divided by 12, equal monthly payments, and no extra fees, insurance, taxes, or rate changes unless represented in the supplied inputs.
- **Compound interest:** fixed nominal annual rate and the selected compounding frequency; no taxes, fees, contributions, or rate changes.
- **SIP projection:** monthly contributions at period end and a constant annualized return used only for illustration. Actual returns vary and are not guaranteed.

These are deterministic projections, not financial advice or guarantees. Client-facing outputs should display the assumptions alongside results.

## Verification limits

EMI responses and compound-interest responses have operation-specific numeric checks. These checks confirm that key deterministic values are present and labelled; they do not validate every sentence of a generated explanation. High-impact financial claims should remain grounded in deterministic results and undergo additional claim-level or human review.
