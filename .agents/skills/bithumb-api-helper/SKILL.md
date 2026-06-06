---
name: bithumb-api-helper
description: Assists in generating and validating code that interacts with the Bithumb API. Use when writing code that makes requests to Bithumb's public or private endpoints, or when checking if Bithumb API calls are correctly formatted according to local reference documentation.
---

# Bithumb API Helper Skill

This skill provides comprehensive instructions, patterns, and validation rules for writing Python and Node.js code that integrates with the Bithumb API, based on the local documentation in the workspace.

## Documentation Structure

When looking up API endpoints or developer guides, refer to the following local paths:
- **Developer Guides**: [guides/](file:///c:/260606coin/.agents/skills/bithumb-api-helper/guides/) (Contains auth procedures, rate limits, error codes)
- **API Reference**: [references/](file:///c:/260606coin/.agents/skills/bithumb-api-helper/references/) (Contains structured endpoints and parameter tables)
  - [PUBLIC API](file:///c:/260606coin/.agents/skills/bithumb-api-helper/references/01_PUBLIC_API/) (Candles, Tickers, Orderbooks, Trades)
  - [PRIVATE API](file:///c:/260606coin/.agents/skills/bithumb-api-helper/references/02_PRIVATE_API/) (Assets, Orders, Deposits, Withdrawals, TWAP)

---

## 1. Authentication Flow (Private API)

Every private API request requires a signed JWT token in the `Authorization` header:
`Authorization: Bearer <JWT_TOKEN>`

### JWT Payload requirements:
- `access_key`: Your Bithumb API Access Key.
- `nonce`: A unique UUID string (e.g. `uuid.uuid4()`).
- `timestamp`: Current time in milliseconds.
- `query_hash`: (Required if query parameters or request body exist) The SHA-512 hash of the query string or serialized JSON body.
- `query_hash_alg`: `"SHA512"` (Required if `query_hash` is present).

### Authentication Code Patterns

#### Node.js Authentication (ESM)
```javascript
import crypto from 'crypto';
import { v4 as uuidv4 } from 'uuid';
import jwt from 'jsonwebtoken';

function generateAuthHeader(accessKey, secretKey, queryParams = null, bodyParams = null) {
  const nonce = uuidv4();
  const timestamp = Date.now();
  
  const payload = {
    access_key: accessKey,
    nonce: nonce,
    timestamp: timestamp,
  };

  let serialized = '';
  if (queryParams) {
    // Array parameters must use key[]=val format
    const searchParams = new URLSearchParams();
    for (const [key, val] of Object.entries(queryParams)) {
      if (Array.isArray(val)) {
        val.forEach(v => searchParams.append(`${key}[]`, v));
      } else {
        searchParams.append(key, val);
      }
    }
    serialized = searchParams.toString();
  } else if (bodyParams) {
    serialized = JSON.stringify(bodyParams);
  }

  if (serialized) {
    const queryHash = crypto.createHash('sha512').update(serialized, 'utf-8').digest('hex');
    payload.query_hash = queryHash;
    payload.query_hash_alg = 'SHA512';
  }

  const token = jwt.sign(payload, secretKey);
  return `Bearer ${token}`;
}
```

#### Python Authentication
```python
import time
import uuid
import hashlib
import jwt  # PyJWT
import urllib.parse

def generate_auth_header(access_key, secret_key, query_params=None, body_params=None):
    nonce = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)
    
    payload = {
        "access_key": access_key,
        "nonce": nonce,
        "timestamp": timestamp
    }
    
    serialized = ""
    if query_params:
        # Bithumb requires key[]=val format for lists/arrays
        query_list = []
        for k, v in query_params.items():
            if isinstance(v, list):
                for val in v:
                    query_list.append((f"{k}[]", val))
            else:
                query_list.append((k, v))
        serialized = urllib.parse.urlencode(query_list)
    elif body_params:
        import json
        serialized = json.dumps(body_params)
        
    if serialized:
        query_hash = hashlib.sha512(serialized.encode('utf-8')).hexdigest()
        payload["query_hash"] = query_hash
        payload["query_hash_alg"] = "SHA512"
        
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return f"Bearer {token}"
```

---

## 2. API Parameter Conventions

1. **Array Parameters**:
   - Any parameter that accepts multiple values (e.g. `codes` in ticker query or order status queries) must be serialized using brackets `[]` (e.g., `codes[]=KRW-BTC&codes[]=KRW-ETH`).
   - Standard comma-separated strings (like `KRW-BTC,KRW-ETH`) are invalid for Bithumb API list parameters.

2. **Deposit Address Check**:
   - The "개별 입금 주소 조회" (Get individual deposit address) endpoint requires **two** parameters:
     - `currency`: The coin code (e.g., `BTC`, `ETH`).
     - `net_type`: The network type (e.g., `BTC`, `ERC20`).
   - Verify that any call to this endpoint includes both parameters, as network selection is critical.

---

## 3. Code Generation & Validation Rules

When generating code to query Bithumb APIs:
1. Always look up the exact endpoint definition in the [references/](file:///c:/260606coin/.agents/skills/bithumb-api-helper/references/) subdirectory.
2. Ensure the base URL is `https://api.bithumb.com`.
3. Check the endpoint method (GET, POST, etc.) and version (`/v1` or `/v2`).
4. Validate that all required query and body parameters are included in the code.
5. Apply the authentication helper for private endpoints.
