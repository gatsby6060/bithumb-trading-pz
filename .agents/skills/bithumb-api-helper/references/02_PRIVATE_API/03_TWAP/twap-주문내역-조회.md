# TWAP - 주문 내역 조회

TWAP 주문 목록을 조회합니다.


---

## TWAP - 주문 내역 조회

TWAP 주문 목록을 조회합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `GET` |
| **URL** | `https://api.bithumb.com/v1/twap` |
| **인증** | ✅ JWT Bearer 토큰 필요 |
| **Content-Type** | `application/json` |

### 요청 파라미터

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `market` | string |  | 거래 대상 페어의 고유 심볼 (예시: KRW-BTC) |
| `uuids` | array[string] |  | TWAP 주문 ID 목록 |
| `state` | string |  | 주문 상태
- `progress`: 진행중 (default)
- `done`: 주문 완료
- `cancel`: 취소 (enum: `progress`, `done`, `cancel`) |
| `next_key` | string |  | 다음 페이지 조회를 위한 커서 값 |
| `limit` | integer |  | 개수 제한(max 100) |
| `order_by` | string |  | 조회 결과 정렬 방식
- `asc`: 오래된 주문 순
- `desc`: 최신 주문 순(default) (enum: `asc`, `desc`) |

### 응답

#### `200` ✅ 성공

**응답 예시**

```json
"{\n  \"has_next\": true,\n  \"next_key\": \"NDMyMjM2fEdCRVQtS1JXfDYyNDc3YjYxLWEwZjItNDY1OC04ZGVhLTFkMjQyYjIxZGFmZQ==\",\n  \"orders\": [\n    {\n      \"uuid\": \"TWAP-001-PROGRESS-BID\",\n      \"side\": \"bid\",\n      \"price\": \"92500000\",\n      \"state\": \"progress\",\n      \"market\": \"KRW-BTC\",\n      \"created_at\": \"2025-12-04T10:00:00+09:00\",\n      \"volume\": \"1.0\",\n      \"total_order_count\": 60,\n      \"total_trades_count\": 10,\n      \"progress_count\": 25,\n      \"total_executed_amount\": \"2312500000\",\n      \"total_executed_volume\": \"0.25\",\n      \"avg_trade_price\": \"92500000.000\",\n      \"wallet_id\": \"0000000000-00-0000\"\n    },\n    {\n      \"uuid\": \"TWAP-002-CANCEL-ASK\",\n      \"side\": \"ask\",\n      \"price\": \"5000\",\n      \"state\": \"cancel\",\n      \"market\": \"KRW-XRP\",\n      \"created_at\": \"2025-12-03T09:00:00+09:00\",\n      \"volume\": \"1000\",\n      \"total_order_count\": 120,\n      \"total_trades_count\": 5,\n      \"progress_count\": 15,\n      \"total_executed_amount\": \"25000000\",\n      \"total_executed_volume\": \"5000\",\n      \"avg_trade_price\": \"5000.0\",\n      \"canceled_at\": \"2025-12-03T09:15:00+09:00\",\n      \"cancel_type\": \"user\"\n    }\n  ]\n}"
```

**응답 필드**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `has_next` | boolean |  | 다음 페이지 존재 여부 |
| `next_key` | string |  | 다음 페이지 조회를 위한 커서 값. `hasNext` 가 false 면 null. (형식: Base64 인코딩된 문자열) |
| `orders` | array[object] |  |  |

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
const twapQueryEndpoint = '/v1/twap';

// --- 1. TWAP 주문내역 조회 파라미터 설정 (명세 반영) ---

// 쿼리 파라미터 객체 정의 (uuids는 별도로 처리)
const twapParams = {
    market: 'KRW-BTC',      // 마켓 ID
    state: 'progress',      // 주문 상태: 진행중 (progress), 완료 (done), 취소 (cancel)
    limit: 50,              // 개수 제한 (최대 100)
    order_by: 'desc',       // 정렬방식 (desc: 내림차순, asc: 오름차순)
    // next_key: '커서_값'  // 다음 페이지 조회를 위한 커서 값 (필요 시 주석 해제)
};

// TWAP 주문 ID 목록 (uuids)
const uuids = [
    'TWAP-A01B02C03D04E05F06', 
    'TWAP-002-DONE'
];

// 기본 쿼리 문자열 생성 (uuids 제외)
let query = querystring.encode(twapParams);

// uuids 배열을 'uuids[]=' 형태로 쿼리 문자열에 추가 (있을 경우에만)
const uuid_query = uuids.map(uuid => `uuids[]=${uuid}`).join('&');
if (uuid_query) {
    query = query ? query + "&" + uuid_query : uuid_query;
}

// 최종 쿼리 문자열 예시: market=KRW-BTC&state=progress&limit=50&order_by=desc&uuids[]=TWAP-A01...&uuids[]=TWAP-002...

// --- 2. JWT 토큰 생성 ---
// GET 요청은 쿼리 문자열을 해시하여 서명에 사용합니다.
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
    }
};

// --- 4. API 호출 (GET 메서드 사용) ---
axios.get(apiUrl + twapQueryEndpoint + '?' + query, config)
    .then((response) => {
        // 성공 응답 처리
        console.log('--- TWAP 주문내역 조회 성공 ---');
        console.log('상태 코드: ', response.status);
        console.log('응답 데이터: ', response.data);

        if (response.data && response.data.data) {
             console.log(`조회된 TWAP 주문 건수: ${response.data.data.length}`);
             console.log(`다음 페이지 존재 여부 (has_next): ${response.data.has_next}`);
        }
    })
    .catch((error) => {
        // 실패 응답 처리
        console.error('--- TWAP 주문내역 조회 실패 ---');
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
twapQueryEndpoint = '/v1/twap' # TWAP 주문내역 조회 엔드포인트

# --- 1. TWAP 주문내역 조회 파라미터 설정 (명세 반영) ---

# 기본 쿼리 파라미터 설정
param = dict(
    market='KRW-BTC',      # 마켓 ID (예시 변경)
    state='progress',      # TWAP 주문 상태 (progress, done, cancel)
    limit=50,              # 개수 제한 (default 100, limit 100)
    order_by='desc',       # 정렬방식 (desc: 내림차순)
    # next_key: '커서값'    # 다음 페이지 조회를 위한 커서 (필요 시 주석 해제)
)

# TWAP 주문 ID 목록 (uuids 필드에 해당)
uuids = [
    'TWAP-A01B02C03D04E05F06',  # TWAP 주문 ID 예시
    'TWAP-002-DONE'            # TWAP 주문 ID 예시
]

# 쿼리 문자열 인코딩 (param)
query = urlencode(param)

# uuids 배열을 'uuids[]=' 형태로 쿼리 문자열에 추가 (명세에 따라 'uuids' 필드로 전달)
uuid_query = '&'.join([f'uuids[]={uuid}' for uuid in uuids])
query = query + "&" + uuid_query

# --- 2. JWT 토큰 생성 ---
# GET 요청의 최종 쿼리 문자열을 해시하여 서명에 사용
hash_obj = hashlib.sha512()
hash_obj.update(query.encode('utf-8'))
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
}

try:
    # --- 3. API 호출 (GET 메서드 및 TWAP 엔드포인트 사용) ---
    response = requests.get(
        apiUrl + twapQueryEndpoint + '?' + query, 
        headers=headers
    )
    
    # 응답 처리
    print('--- TWAP 주문내역 조회 요청 결과 ---')
    print('상태 코드:', response.status_code)
    
    response_data = response.json()
    print('데이터:', response_data)
    
    # Response 명세: 데이터 추출
    if response.status_code == 200 and 'data' in response_data:
        print(f"조회된 TWAP 주문 건수: {len(response_data['data'])}")

except Exception as err:
    # 예외 처리
    print('--- TWAP 주문내역 조회 중 오류 발생 ---')
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
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.util.EntityUtils;

import com.fasterxml.jackson.databind.ObjectMapper; // JSON 파싱을 위해 추가

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

public class TwapOrderQueryClient {

    public static void main(String[] args) throws NoSuchAlgorithmException, IOException {
        String accessKey = "발급받은 API KEY";   // 실제 발급받은 Access Key로 변경
        String secretKey = "발급받은 SECRET KEY"; // 실제 발급받은 Secret Key로 변경
        String apiUrl = "https://api.bithumb.com";
        String twapQueryEndpoint = "/v1/twap"; // TWAP 주문내역 조회 엔드포인트

        // --- 1. TWAP 주문내역 조회 파라미터 설정 (명세 반영) ---
        // 기본 파라미터 (map 대신 List<NameValuePair> 사용)
        List<NameValuePair> queryParams = new ArrayList<>();
        queryParams.add(new BasicNameValuePair("market", "KRW-BTC")); // 마켓 ID
        queryParams.add(new BasicNameValuePair("state", "progress")); // TWAP 주문 상태 (progress, done, cancel)
        queryParams.add(new BasicNameValuePair("limit", "50"));
        queryParams.add(new BasicNameValuePair("order_by", "desc"));
        // queryParams.add(new BasicNameValuePair("next_key", "커서값")); // 페이지네이션 커서

        // TWAP 주문 ID 목록 (uuids)
        List<String> uuids = new ArrayList<>();
        uuids.add("TWAP-A01B02C03D04E05F06");
        uuids.add("TWAP-002-DONE");
        
        // uuids 배열을 'uuids[]=' 형태로 쿼리 문자열에 추가
        // Note: URLEncodedUtils.format은 Map이 아닌 List<NameValuePair>만 처리하므로,
        // uuids[]는 별도의 문자열로 구성해야 합니다.
        String uuidQuery = uuids.stream()
                .map(uuid -> "uuids[]=" + uuid)
                .collect(Collectors.joining("&"));
        
        // --- 2. JWT 토큰 생성 ---
        // 쿼리 문자열 인코딩 및 합치기 (서명에 사용)
        String baseQuery = URLEncodedUtils.format(queryParams, StandardCharsets.UTF_8);
        String finalQuery = baseQuery;
        
        if (!uuidQuery.isEmpty()) {
             finalQuery = finalQuery + "&" + uuidQuery;
        }

        // SHA-512 해시 생성
        MessageDigest md = MessageDigest.getInstance("SHA-512");
        md.update(finalQuery.getBytes(StandardCharsets.UTF_8));
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

        // --- 3. API 호출 (GET 메서드 및 TWAP 엔드포인트 사용) ---
        // 최종 쿼리 문자열을 URL에 추가
        final HttpGet httpRequest = new HttpGet(apiUrl + twapQueryEndpoint + "?" + finalQuery);
        httpRequest.addHeader("Authorization", authenticationToken);

        try (CloseableHttpClient client = HttpClients.createDefault();
             CloseableHttpResponse response = client.execute(httpRequest)) {
            
            // 응답 처리
            int httpStatus = response.getStatusLine().getStatusCode();
            String responseBody = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
            
            System.out.println("--- TWAP 주문내역 조회 요청 결과 ---");
            System.out.println("상태 코드: " + httpStatus);
            System.out.println("응답 본문: " + responseBody);
            
            if (httpStatus >= 200 && httpStatus < 300) {
                 ObjectMapper mapper = new ObjectMapper();
                 Map<String, Object> responseMap = mapper.readValue(responseBody, Map.class);
                 List<?> dataList = (List<?>) responseMap.get("data");
                 
                 if (dataList != null) {
                     System.out.println("조회된 TWAP 주문 건수: " + dataList.size());
                 }
            }
        } catch (Exception e) {
            throw new RuntimeException("API 요청 처리 중 예외 발생", e);
        }
    }
}
```
