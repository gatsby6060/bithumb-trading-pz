# API 키 리스트 조회

API 키 리스트와 만료 일자를 조회합니다.

* API는 [해당페이지](https://bithumb.com/react/api-support/management-api)에서 API Key를 발급 받은 후 사용 가능합니다.
* API Key 발급 시에는 API 활성 항목과 해당 API Key를 사용할 IP 주소를 등록해야 합니다.
* IP 주소는 최대 5개까지 등록 가능하며 등록한 IP 주소로 접속한 경우에만 해당 API Key를 사용할 수 있습니다.
* API Key는 계정당 10개까지 발급 받을 수 있으며 API Key 발급이 완료된 이후에는 Secret key를 추가로 확인할 수 없습니다. Secret key는 발급 받은 이후 안전한 곳에 별도 보관해주시기 바랍니다.
* 발급 받은 API Key는 발급일 기준으로 1년 동안 사용 가능하며 기간 연장은 불가능합니다. 1년 경과 시 해당 API Key는 삭제 후 재발급 받아주시기 바랍니다.
* API Key 발급, 수정, 삭제 시에는 2채널 추가 인증이 진행되며, API 활성 항목 변경이 필요한 경우 [API Key 관리](https://bithumb.com/react/api-support/management-api)에서 해당 API Key를 삭제한 후 재발급 받아야 합니다.


---

## API 키 리스트 조회

API 키 리스트와 만료 일자를 조회합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `GET` |
| **URL** | `https://api.bithumb.com/v1/api_keys` |
| **인증** | ✅ JWT Bearer 토큰 필요 |
| **Content-Type** | `application/json` |

### 요청 파라미터

_요청 파라미터 없음_

### 응답

#### `200` ✅ 성공

**응답 예시**

```json
"[\n  {\n    \"access_key\": \"59683c90185742d69fd8fa1bc0cf27785c392afaa56ece\",\n    \"expire_at\": \"2025-06-11T09:00:00+09:00\"\n  },\n  {\n    \"access_key\": \"3e97926e9b75a6aeb637d2c172a292588502daccfb5cab\",\n    \"expire_at\": \"2025-06-12T09:00:00+09:00\"\n  },\n  {\n    \"access_key\": \"400e5bcb69440e7ace08fd7991340c271683f20dba9a6e\",\n    \"expire_at\": \"2025-06-12T09:00:00+09:00\"\n  }\n]"
```

**응답 필드** (배열 항목)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `access_key` | string |  | API KEY |
| `expire_at` | string |  | 만료일시 |

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
const axios = require('axios')

const accessKey = '발급받은 API KEY'
const secretKey = '발급받은 SECRET KEY'
const apiUrl = 'https://api.bithumb.com'

// Generate access token
const payload = {
    access_key: accessKey,
    nonce: uuidv4(),
    timestamp: Date.now()
};
const jwtToken = jwt.sign(payload, secretKey)
const config = {
    headers: {
        Authorization: `Bearer ${jwtToken}`
    }
}

// Call API
axios.get(apiUrl + '/v1/api_keys', config)
    .then((response) => {
        // handle to success
        console.log('status: ', response.status)
        console.log('data: ', response.data)
    })
    .catch((error) => {
        // handle to fail
        console.log(error.response.status)
        console.log(error.response.data)
    });
```

#### Python

```python
# Python 3
# pip3 installl pyJwt
import jwt 
import uuid
import time
import requests

# Set API parameters
accessKey = '발급받은 API KEY'
secretKey = '발급받은 SECRET KEY'
apiUrl = 'https://api.bithumb.com'

# Generate access token
payload = {
    'access_key': accessKey,
    'nonce': str(uuid.uuid4()),
    'timestamp': round(time.time() * 1000)
}
jwt_token = jwt.encode(payload, secretKey)
authorization_token = 'Bearer {}'.format(jwt_token)
headers = {
  'Authorization': authorization_token
}

try:
    # Call API
    response = requests.get(apiUrl + '/v1/api_keys', headers=headers)
    # handle to success or fail
    print(response.status_code)
    print(response.json())
except Exception as err:
    # handle exception
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
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;

import java.nio.charset.StandardCharsets;
import java.util.UUID;

public class GETNoArgs {

    public static void main(String[] args) {
        String accessKey = "발급받은 API KEY";
        String secretKey = "발급받은 SECRET KEY";
        String apiUrl = "https://api.bithumb.com";

        // Generate access token
        Algorithm algorithm = Algorithm.HMAC256(secretKey);
        String jwtToken = JWT.create()
                .withClaim("access_key", accessKey)
                .withClaim("nonce", UUID.randomUUID().toString())
                .withClaim("timestamp", System.currentTimeMillis())
                .sign(algorithm);
        String authenticationToken = "Bearer " + jwtToken;

        // Call API
        final HttpGet httpRequest = new HttpGet(apiUrl + "/v1/api_keys");
        httpRequest.addHeader("Authorization", authenticationToken);

        try (CloseableHttpClient client = HttpClients.createDefault();
             CloseableHttpResponse response = client.execute(httpRequest)) {
            // handle to response
            int httpStatus = response.getStatusLine().getStatusCode();
            String responseBody = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
            System.out.println(httpStatus);
            System.out.println(responseBody);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}

```
