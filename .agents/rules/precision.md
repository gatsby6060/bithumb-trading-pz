---
trigger: glob
globs:
  - "**/*.py"
  - "**/*.js"
---
# Financial Arithmetic Precision Rule

This rule prevents floating-point precision errors during financial and order value calculations in Python and JavaScript/TypeScript.

## Constraints & Requirements

1. **Ban Direct Float Arithmetic**:
   - Do not perform direct floating-point operations (e.g., `price * quantity`, `balance + profit`) for transaction amounts, order volumes, or prices.
   - Example to avoid: `0.1 + 0.2` resulting in `0.30000000000000004` which can lead to order rejection.

2. **Use Precision Libraries**:
   - **Python**: Always import and use `decimal.Decimal` (and set appropriate rounding context if needed).
   - **JavaScript/TypeScript**: Use precision math libraries like `decimal.js`, `bignumber.js`, or similar, rather than standard `Number` operators.

3. **Validation of Ticker Tick Size**:
   - Before executing/formatting orders, check if the price and quantity conform to Bithumb's minimum tick sizes and decimal limits as specified in the endpoint references.
