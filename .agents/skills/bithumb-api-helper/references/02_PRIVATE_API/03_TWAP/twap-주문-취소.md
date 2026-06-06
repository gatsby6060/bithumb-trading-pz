# TWAP - 주문 취소

TWAP 주문 취소를 요청합니다.


---

## TWAP - 주문 취소

TWAP 주문 취소를 요청합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `DELETE` |
| **URL** | `https://api.bithumb.com/v1/twap` |
| **인증** | ✅ JWT Bearer 토큰 필요 |
| **Content-Type** | `application/json` |

### 요청 파라미터

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `algo_order_id` | string | ✅ | 취소할 TWAP 주문 ID |

### 응답

#### `200` ✅ 성공

**응답 예시**

```json
{
  "algo_order_id": "TWAP-A01B02C03D04E05F06"
}
```

**응답 필드**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `algo_order_id` | string | ✅ | 취소된 TWAP 주문 ID |

#### `400` ❌ 오류

**응답 예시**

```json
"{\n  \"error\": {\n    \"name\": \"error name\",\n    \"message\": \"error message\"\n  }\n}"
```

**응답 필드**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `error` | object | ✅ |  |

### 코드 샘플

#### Javascript

```javascript
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const crypto = require('crypto');
const querystring = require('querystring');
const axios = require('axios');

// --- 인증 정보 설정 ---
const accessKey = '발급받은 API KEY';   // 실제 발급받은 Access Key로 변경
const secretKey = '발급받은 SECRET KEY'; // 실제 발급받은 Secret Key로 변경
const apiUrl = 'https://api.bithumb.com';
const twapCancelEndpoint = '/v1/twap';

// --- 1. TWAP 주문 취소 파라미터 설정 (명세 반영) ---
const twapCancelParams = {
    algo_order_id: 'TWAP-A01B02C03D04E05F06' // 취소할 실제 TWAP 주문 ID로 변경
};

// --- 2. JWT 토큰 생성 ---
// DELETE 요청이지만, 파라미터를 쿼리 문자열로 인코딩하여 해시 생성
const query = querystring.encode(twapCancelParams);
const alg = 'SHA512';
const hash = crypto.createHash(alg);
const queryHash = hash.update(query, 'utf-8').digest('hex');

// 페이로드 구성
const payload = {
    access_key: accessKey,
    nonce: uuidv4(),
    timestamp: Date.now(),
    query_hash: queryHash,
    query_hash_alg: alg
};

// Secret Key로 서명하여 JWT 토큰 생성
const jwtToken = jwt.sign(payload, secretKey);

// --- 3. HTTP 요청 설정 ---
const config = {
    headers: {
        Authorization: `Bearer ${jwtToken}`
        // DELETE 요청은 Body가 없으므로 Content-Type은 필수가 아닐 수 있습니다.
    },
    // axios.delete에서 params를 사용하면 쿼리 문자열을 자동으로 URL에 추가합니다.
    params: twapCancelParams
};

// --- 4. API 호출 (DELETE 메서드 사용) ---
axios.delete(apiUrl + twapCancelEndpoint, config)
    .then((response) => {
        // 성공 응답 처리 (Response 명세: algo_order_id)
        console.log('--- TWAP 주문 취소 요청 성공 ---');
        console.log('상태 코드: ', response.status);
        console.log('응답 데이터: ', response.data);
        
        if (response.data && response.data.algo_order_id) {
             console.log('취소된 TWAP 주문 ID: ', response.data.algo_order_id);
        }
    })
    .catch((error) => {
        // 실패 응답 처리
        console.error('--- TWAP 주문 취소 요청 실패 ---');
        console.error('상태 코드:', error.response.status);
        console.error('에러 데이터:', error.response.data);
    });
```

#### Python

```python
# Python 3
# pip3 install pyjwt requests
import jwt 
import uuid
import hashlib
import time
from urllib.parse import urlencode
import requests
import json

# --- 인증 정보 설정 ---
accessKey = '발급받은 API KEY'  # 실제 발급받은 Access Key로 변경
secretKey = '발급받은 SECRET KEY' # 실제 발급받은 Secret Key로 변경
apiUrl = 'https://api.bithumb.com'
twapCancelEndpoint = '/v1/twap' # TWAP 주문 취소 엔드포인트

# --- 1. TWAP 주문 취소 파라미터 설정 (명세 반영) ---
# algo_order_id를 사용하여 취소할 주문 ID 지정
param = dict(
    algo_order_id='TWAP-A01B02C03D04E05F06'  # 취소할 실제 TWAP 주문 ID로 변경
)

# --- 2. JWT 토큰 생성 ---
# DELETE 요청이지만, 파라미터는 쿼리 문자열 형태로 인코딩하여 해시 생성
query = urlencode(param).encode('utf-8')
hash_obj = hashlib.sha512()
hash_obj.update(query)
query_hash = hash_obj.hexdigest()

# 페이로드 구성
payload = {
    'access_key': accessKey,
    'nonce': str(uuid.uuid4()),
    'timestamp': round(time.time() * 1000), 
    'query_hash': query_hash,
    'query_hash_alg': 'SHA512',
}    
# Secret Key로 서명하여 JWT 토큰 생성
jwt_token = jwt.encode(payload, secretKey, algorithm='HS512')
authorization_token = 'Bearer {}'.format(jwt_token)

# 헤더 설정
headers = {
    'Authorization': authorization_token
    # DELETE 요청이므로 Content-Type은 필수가 아닙니다.
}

try:
    # --- 3. API 호출 (DELETE 메서드 및 TWAP 엔드포인트 사용) ---
    # requests.delete의 params 인자는 쿼리 문자열로 URL에 자동 추가됩니다.
    response = requests.delete(
        apiUrl + twapCancelEndpoint, 
        params=param, 
        headers=headers
    )
    
    # 응답 처리
    print('--- TWAP 주문 취소 요청 결과 ---')
    print('상태 코드:', response.status_code)
    
    response_data = response.json()
    print('데이터:', response_data)
    
    # Response 명세: algo_order_id 추출
    if response.status_code == 200 and 'algo_order_id' in response_data:
        print(f"취소된 TWAP 주문 ID: {response_data.get('algo_order_id')}")

except Exception as err:
    # 예외 처리
    print('--- TWAP 주문 취소 요청 중 오류 발생 ---')
    print(err)
```

#### Java

```java
package com.example.sample;

// https://mvnrepository.com/artifact/com.auth0/java-jwt
import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
// https://mvnrepository.com/artifact/org.apache.httpcomponents/httpclient
import org.apache.http.NameValuePair;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpDelete; // HttpDelete 사용
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.util.EntityUtils;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class TwapOrderCancelClient {

    public static void main(String[] args) throws NoSuchAlgorithmException, IOException {
        String accessKey = "발급받은 API KEY";   // 실제 발급받은 Access Key로 변경
        String secretKey = "발급받은 SECRET KEY"; // 실제 발급받은 Secret Key로 변경
        String apiUrl = "https://api.bithumb.com";
        String twapCancelEndpoint = "/v1/twap"; // TWAP 주문 취소 엔드포인트

        // --- 1. TWAP 주문 취소 파라미터 설정 (명세 반영) ---
        List<NameValuePair> queryParams = new ArrayList<>();
        // 'uuid' 대신 'algo_order_id' 사용
        queryParams.add(new BasicNameValuePair("algo_order_id", "TWAP-A01B02C03D04E05F06")); // 취소할 실제 TWAP 주문 ID로 변경

        // --- 2. JWT 토큰 생성 ---
        // 쿼리 문자열 인코딩 (서명에 사용)
        String query = URLEncodedUtils.format(queryParams, StandardCharsets.UTF_8);
        
        // SHA-512 해시 생성
        MessageDigest md = MessageDigest.getInstance("SHA-512");
        md.update(query.getBytes(StandardCharsets.UTF_8));
        String queryHash = String.format("%0128x", new BigInteger(1, md.digest()));
        
        // JWT 페이로드 및 토큰 생성
        Algorithm algorithm = Algorithm.HMAC256(secretKey);
        String jwtToken = JWT.create()
                .withClaim("access_key", accessKey)
                .withClaim("nonce", UUID.randomUUID().toString())
                .withClaim("timestamp", System.currentTimeMillis())
                .withClaim("query_hash", queryHash)
                .withClaim("query_hash_alg", "SHA512")
                .sign(algorithm);
        String authenticationToken = "Bearer " + jwtToken;

        // --- 3. API 호출 (DELETE 메서드 및 TWAP 엔드포인트 사용) ---
        // DELETE 요청 시 파라미터를 쿼리 문자열로 URL에 추가
        final HttpDelete httpDeleteRequest = new HttpDelete(apiUrl + twapCancelEndpoint + "?" + query);
        httpDeleteRequest.addHeader("Authorization", authenticationToken);
        // DELETE 요청은 Body가 없으므로 Content-Type 헤더는 필수가 아닐 수 있습니다.

        try (CloseableHttpClient client = HttpClients.createDefault();
             CloseableHttpResponse response = client.execute(httpDeleteRequest)) {
            
            // 응답 처리
            int httpStatus = response.getStatusLine().getStatusCode();
            String responseBody = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
            
            System.out.println("--- TWAP 주문 취소 요청 결과 ---");
            System.out.println("상태 코드: " + httpStatus);
            System.out.println("응답 본문: " + responseBody);
            
            // 응답에 algo_order_id가 포함되어 있는지 확인 (JSON 파싱 로직 추가 필요)
            // if (httpStatus == 200) { ... }
            
        } catch (IOException | RuntimeException e) {
            throw new RuntimeException("API 요청 처리 중 예외 발생", e);
        }
    }
}
```
