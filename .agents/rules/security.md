---
trigger: always_on
---
# Bithumb API Keys & Security Rule

This rule prevents exposing Bithumb API keys and secrets in the codebase.

## Constraints & Requirements

1. **Never Hardcode Secrets**: 
   - Under no circumstances should `access_key` or `secret_key` values be hardcoded in any script or source file.
   - Always load them from environment variables (e.g. `process.env.BITHUMB_ACCESS_KEY` in Node.js, `os.environ.get("BITHUMB_ACCESS_KEY")` in Python).

2. **Environment File Protection**:
   - Save local keys in a `.env` file at the root of the workspace.
   - Ensure `.env` is listed in your `.gitignore` file before committing any code.

3. **Secret Verification**:
   - If you detect any hardcoded key-like strings (e.g. alphanumeric strings representing access keys or secret keys), replace them with environment variable queries immediately.
