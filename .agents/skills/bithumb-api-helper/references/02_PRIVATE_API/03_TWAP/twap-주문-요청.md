# TWAP - 주문 요청

TWAP 주문을 요청합니다.


---

## TWAP - 주문 요청

TWAP 주문을 요청합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `POST` |
| **URL** | `https://api.bithumb.com/v1/twap` |
| **인증** | ✅ JWT Bearer 토큰 필요 |
| **Content-Type** | `application/json` |

### 요청 파라미터

#### 요청 Body

| 파라미터 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `market` | string | ✅ | 거래 대상 페어의 고유 심볼 (예시: KRW-BTC) |
| `side` | string | ✅ | 주문 종류 (enum: `bid`, `ask`) |
| `volume` | string |  | 주문 수량 (매도시 필수) |
| `price` | string |  | 주문 가격(매수시 필수) |
| `duration` | string | ✅ | 주문 시간(twap 주문이 진행되는 시간) - 초(min 300, max 43200) |
| `frequency` | string | ✅ | 주문 간격 - 초 (enum: `15`, `20`, `30`, `60`, `120`) |

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
| `algo_order_id` | string | ✅ | TWAP 주문 ID |

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
const twapEndpoint = '/v1/twap'; // TWAP 주문 엔드포인트

// --- 1. TWAP 주문 파라미터 설정 (명세 반영) ---
// *market, *side, *duration, *frequency 는 필수 필드입니다.
const twapRequestBody = {
    // 필수 필드
    market: 'KRW-BTC', // 마켓 ID
    side: 'bid',       // 주문 종류 (매수: bid, 매도: ask)
    duration: '3600',  // 주문 시간 (총 3600초 = 1시간)
    frequency: '60',   // 주문 간격 (60초마다 분할 주문)

    // 조건부 필수 필드 (매수 시 price, 매도 시 volume 필수)
    volume: '0.5',     // 총 주문량 (0.5 BTC)
    price: '100000000' // 주문 가격 (1억 원)
};

// --- 2. JWT 토큰 생성 ---
// JWT 토큰 생성을 위한 쿼리 문자열 인코딩 및 SHA512 해시 생성
const query = querystring.encode(twapRequestBody);
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
        Authorization: `Bearer ${jwtToken}`, // 생성된 JWT 토큰 사용
        'Content-Type': 'application/json'
    }
};

// --- 4. API 호출 ---
axios.post(apiUrl + twapEndpoint, twapRequestBody, config)
    .then((response) => {
        // 성공 응답 처리 (Response 명세: algo_order_id)
        console.log('--- TWAP 주문 요청 성공 ---');
        console.log('상태 코드: ', response.status);
        console.log('응답 데이터: ', response.data);
        
        // Response에서 TWAP 주문 ID 추출
        if (response.data && response.data.algo_order_id) {
             console.log('TWAP 주문 ID (algo_order_id): ', response.data.algo_order_id);
        }
    })
    .catch((error) => {
        // 실패 응답 처리
        console.error('--- TWAP 주문 요청 실패 ---');
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
twapEndpoint = '/v1/twap' # TWAP 주문 엔드포인트

# --- 1. TWAP 주문 파라미터 설정 (명세 반영) ---
# TWAP 주문은 market, side, duration, frequency가 필수입니다.
# 매수(bid) 시 price 필수, 매도(ask) 시 volume 필수
requestBody = dict(
    market='KRW-BTC',
    side='bid',
    volume='0.5',          # 총 주문량 (String 타입으로 전달)
    price='100000000',    # 주문 가격 (String 타입으로 전달)
    duration='3600',      # TWAP 주문이 진행되는 총 시간 (초 단위)
    frequency='60'        # 주문이 분할되어 제출될 간격 (초 단위)
)

# --- 2. JWT 토큰 생성 ---
# JWT 토큰 생성을 위해 쿼리 문자열 인코딩 및 SHA512 해시 생성
# 주의: requests.post에 data=json.dumps()를 사용하더라도, JWT 서명 시에는 
#       쿼리 문자열(URL-encoded form data) 기반으로 해시를 생성해야 합니다.
query = urlencode(requestBody).encode('utf-8')
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
jwt_token = jwt.encode(payload, secretKey, algorithm='HS512') # HS512 알고리즘 명시
authorization_token = 'Bearer {}'.format(jwt_token)

# 헤더 설정
headers = {
    'Authorization': authorization_token,
    'Content-Type': 'application/json' # 요청 본문 타입은 JSON
}

try:
    # --- 3. API 호출 (TWAP 엔드포인트 사용) ---
    # TWAP 주문은 JSON 본문을 사용합니다.
    response = requests.post(
        apiUrl + twapEndpoint, 
        data=json.dumps(requestBody), 
        headers=headers
    )
    
    # 응답 처리
    print('--- TWAP 주문 요청 결과 ---')
    print('상태 코드:', response.status_code)
    
    response_data = response.json()
    print('데이터:', response_data)
    
    # Response 명세: algo_order_id 추출
    if response.status_code == 200 and 'algo_order_id' in response_data:
        print(f"TWAP 주문 ID (algo_order_id): {response_data['algo_order_id']}")

except Exception as err:
    # 예외 처리
    print('--- TWAP 주문 요청 중 오류 발생 ---')
    print(err)
```

#### Java

```java
package com.example.sample;

// https://mvnrepository.com/artifact/com.auth0/java-jwt
import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
// https://mvnrepository.com/artifact/org.apache.httpcomponents/httpclient
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.util.EntityUtils;
// https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-databind
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

public class TwapOrderClient {

    public static void main(String[] args) throws NoSuchAlgorithmException, IOException {
        String accessKey = "발급받은 API KEY";   // 실제 발급받은 Access Key로 변경
        String secretKey = "발급받은 SECRET KEY"; // 실제 발급받은 Secret Key로 변경
        String apiUrl = "https://api.bithumb.com";
        String twapEndpoint = "/v1/twap"; // TWAP 주문 엔드포인트

        // --- 1. TWAP 주문 파라미터 설정 (명세 반영) ---
        // 모든 NumberString 타입 필드는 String으로 전달되도록 Map에 String 값을 사용합니다.
        Map<String, String> requestBody = new LinkedHashMap<>();
        requestBody.put("market", "KRW-BTC");
        requestBody.put("side", "bid");
        requestBody.put("volume", "0.5");       // 총 주문량 (NumberString)
        requestBody.put("price", "100000000");  // 주문 가격 (NumberString)
        requestBody.put("duration", "3600");    // TWAP 주문 총 시간 (필수, NumberString)
        requestBody.put("frequency", "60");     // TWAP 주문 간격 (필수, NumberString)

        // --- 2. JWT 토큰 생성 ---
        // 쿼리 파라미터 생성 (JWT 서명은 쿼리 문자열 기반으로 해시를 생성해야 함)
        List<BasicNameValuePair> queryParams = requestBody.entrySet().stream()
                .map(entry -> new BasicNameValuePair(entry.getKey(), entry.getValue()))
                .collect(Collectors.toList());

        String query = URLEncodedUtils.format(queryParams, StandardCharsets.UTF_8);
        
        // SHA-512 해시 생성
        MessageDigest md = MessageDigest.getInstance("SHA-512");
        md.update(query.getBytes(StandardCharsets.UTF_8));
        String queryHash = String.format("%0128x", new BigInteger(1, md.digest()));
        
        // JWT 알고리즘 설정 (Bithumb은 HMAC256이 아니라 HMAC512로 알고리즘을 사용하기도 함. 
        // 여기서는 예시와 같이 HMAC256을 사용하되, 실제 거래소 문서를 확인해야 합니다.)
        Algorithm algorithm = Algorithm.HMAC256(secretKey); 
        
        // JWT 페이로드 및 토큰 생성
        String jwtToken = JWT.create()
                .withClaim("access_key", accessKey)
                .withClaim("nonce", UUID.randomUUID().toString())
                .withClaim("timestamp", System.currentTimeMillis())
                .withClaim("query_hash", queryHash)
                .withClaim("query_hash_alg", "SHA512")
                .sign(algorithm);
        String authenticationToken = "Bearer " + jwtToken;

        // --- 3. API 호출 (TWAP 엔드포인트 사용) ---
        final HttpPost httpRequest = new HttpPost(apiUrl + twapEndpoint);
        httpRequest.addHeader("Authorization", authenticationToken);
        httpRequest.addHeader("Content-type", "application/json");

        // 요청 본문 (requestBody)은 JSON 형태로 변환하여 엔티티에 설정
        String jsonBody = new ObjectMapper().writeValueAsString(requestBody);
        httpRequest.setEntity(new StringEntity(jsonBody, StandardCharsets.UTF_8));

        try (CloseableHttpClient client = HttpClients.createDefault();
             CloseableHttpResponse response = client.execute(httpRequest)) {
            
            // 응답 처리
            int httpStatus = response.getStatusLine().getStatusCode();
            String responseBody = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
            
            System.out.println("--- TWAP 주문 요청 결과 ---");
            System.out.println("상태 코드: " + httpStatus);
            System.out.println("응답 본문: " + responseBody);
            
            // Response 명세: algo_order_id 추출 (Jackson ObjectMapper 사용 가정)
            if (httpStatus >= 200 && httpStatus < 300) {
                 ObjectMapper mapper = new ObjectMapper();
                 Map<String, Object> responseMap = mapper.readValue(responseBody, Map.class);
                 String algoOrderId = (String) responseMap.get("algo_order_id");
                 if (algoOrderId != null) {
                     System.out.println("TWAP 주문 ID (algo_order_id): " + algoOrderId);
                 }
            }
        } catch (Exception e) {
            throw new RuntimeException("API 요청 중 예외 발생", e);
        }
    }
}
```
