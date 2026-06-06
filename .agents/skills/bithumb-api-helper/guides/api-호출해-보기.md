# API 호출해 보기

Public API로 거래 데이터를 확인하고, 인증 토큰을 적용하여 Private API로 주문을 수행하는 과정을 다룹니다


> 이 문서의 코드를 실행하려면 [개발 환경 설정하기](https://apidocs.bithumb.com/docs/개발-환경-설정하기)에서 패키지 설치와 API 키 설정을 먼저 완료하세요.


## Public API 호출하기

Public API는 인증 없이 호출할 수 있습니다. [빠른 시작 가이드](https://apidocs.bithumb.com/docs/빠른-시작-가이드)에서 거래 대상 페어 목록 조회(`/v1/market/all`)를 다뤘으니, 여기서는 현재가와 호가 정보를 조회합니다.

### 현재가 조회

특정 거래 대상 페어의 현재 가격 정보를 조회합니다.


  
**JavaScript**
```javascript
    const axios = require('axios');

    const apiUrl = 'https://api.bithumb.com';

    axios.get(apiUrl + '/v1/ticker', {
      params: { markets: 'KRW-BTC' }
    })
      .then((response) => {
        const ticker = response.data[0];
        console.log(`거래 대상 페어: ${ticker.market}`);
        console.log(`현재가: ${Number(ticker.trade_price).toLocaleString()}원`);
        console.log(`전일 대비: ${ticker.signed_change_rate > 0 ? '+' : ''}${(ticker.signed_change_rate * 100).toFixed(2)}%`);
        console.log(`거래량(24h): ${ticker.acc_trade_volume_24h}`);
      })
      .catch((error) => {
        console.error(error.response?.data || error.message);
      });
    ```


  
**Python**
```python
    import requests

    api_url = 'https://api.bithumb.com'

    response = requests.get(api_url + '/v1/ticker', params={'markets': 'KRW-BTC'})
    data = response.json()

    if response.status_code == 200:
        ticker = data[0]
        print(f"거래 대상 페어: {ticker['market']}")
        print(f"현재가: {ticker['trade_price']:,.0f}원")
        rate = ticker['signed_change_rate'] * 100
        print(f"전일 대비: {'+' if rate > 0 else ''}{rate:.2f}%")
        print(f"거래량(24h): {ticker['acc_trade_volume_24h']}")
    else:
        print(f"에러: {data}")
    ```


  
**Java**
```java
    import org.apache.http.client.methods.CloseableHttpResponse;
    import org.apache.http.client.methods.HttpGet;
    import org.apache.http.impl.client.CloseableHttpClient;
    import org.apache.http.impl.client.HttpClients;
    import org.apache.http.util.EntityUtils;
    import java.nio.charset.StandardCharsets;

    public class Ticker {
        public static void main(String[] args) {
            String apiUrl = "https://api.bithumb.com";

            HttpGet request = new HttpGet(apiUrl + "/v1/ticker?markets=KRW-BTC");
            request.addHeader("accept", "application/json");

            try (CloseableHttpClient client = HttpClients.createDefault();
                 CloseableHttpResponse response = client.execute(request)) {
                int status = response.getStatusLine().getStatusCode();
                String body = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                System.out.println("HTTP " + status);
                System.out.println(body);
            } catch (Exception e) {
                System.err.println("에러: " + e.getMessage());
            }
        }
    }
    ```


**응답 예시**

```json
[
  {
    "market": "KRW-BTC",
    "trade_price": 136500000,
    "signed_change_rate": 0.0202366864,
    "acc_trade_volume_24h": 27181.31137002,
    "highest_52_week_price": 156000000,
    "lowest_52_week_price": 78000000
    // ... 기타 필드
  }
]
```


> 응답 필드 전체 목록은 [현재가(Ticker) 조회](ref:현재가-조회) API 레퍼런스를 참고하세요.


### 호가 정보 조회

매수·매도 호가 정보를 확인합니다. `markets` 파라미터에 하나의 거래 대상 페어만 입력하면 30호가까지, 여러 거래 대상 페어를 입력하면 15호가까지 제공됩니다.


  
**JavaScript**
```javascript
    const axios = require('axios');

    const apiUrl = 'https://api.bithumb.com';

    axios.get(apiUrl + '/v1/orderbook', {
      params: { markets: 'KRW-BTC' }
    })
      .then((response) => {
        const book = response.data[0];
        console.log(`거래 대상 페어: ${book.market}`);
        console.log(`매도 총 잔량: ${book.total_ask_size}`);
        console.log(`매수 총 잔량: ${book.total_bid_size}`);
        console.log('\n--- 1~3호가 ---');
        book.orderbook_units.slice(0, 3).forEach((unit, i) => {
          console.log(`${i + 1}호가 | 매도: ${Number(unit.ask_price).toLocaleString()}원 (${unit.ask_size}) | 매수: ${Number(unit.bid_price).toLocaleString()}원 (${unit.bid_size})`);
        });
      })
      .catch((error) => {
        console.error(error.response?.data || error.message);
      });
    ```


  
**Python**
```python
    import requests

    api_url = 'https://api.bithumb.com'

    response = requests.get(api_url + '/v1/orderbook', params={'markets': 'KRW-BTC'})
    data = response.json()

    if response.status_code == 200:
        book = data[0]
        print(f"거래 대상 페어: {book['market']}")
        print(f"매도 총 잔량: {book['total_ask_size']}")
        print(f"매수 총 잔량: {book['total_bid_size']}")
        print('\n--- 1~3호가 ---')
        for i, unit in enumerate(book['orderbook_units'][:3]):
            print(f"{i+1}호가 | 매도: {unit['ask_price']:,.0f}원 ({unit['ask_size']}) | 매수: {unit['bid_price']:,.0f}원 ({unit['bid_size']})")
    else:
        print(f"에러: {data}")
    ```


  
**Java**
```java
    import org.apache.http.client.methods.CloseableHttpResponse;
    import org.apache.http.client.methods.HttpGet;
    import org.apache.http.impl.client.CloseableHttpClient;
    import org.apache.http.impl.client.HttpClients;
    import org.apache.http.util.EntityUtils;
    import java.nio.charset.StandardCharsets;

    public class Orderbook {
        public static void main(String[] args) {
            String apiUrl = "https://api.bithumb.com";

            HttpGet request = new HttpGet(apiUrl + "/v1/orderbook?markets=KRW-BTC");
            request.addHeader("accept", "application/json");

            try (CloseableHttpClient client = HttpClients.createDefault();
                 CloseableHttpResponse response = client.execute(request)) {
                int status = response.getStatusLine().getStatusCode();
                String body = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                System.out.println("HTTP " + status);
                System.out.println(body);
            } catch (Exception e) {
                System.err.println("에러: " + e.getMessage());
            }
        }
    }
    ```


> 응답 필드 전체 목록은 [호가 정보(Orderbook) 조회](ref:호가-조회) API 레퍼런스를 참고하세요.


## Private API 호출하기

Private API(계좌 조회, 주문, 출금 등)는 JWT 인증 토큰이 필요합니다. 토큰 생성 과정의 상세 설명은 [인증 토큰 생성하기](https://apidocs.bithumb.com/docs/인증-토큰-생성하기)를 참고하세요.

아래 예제에서는 토큰 생성을 헬퍼 함수로 만들어 재사용합니다.

### 인증 토큰 헬퍼 함수


  
**Node.js**
```javascript title="auth.js"
    const jwt = require('jsonwebtoken');
    const { v4: uuidv4 } = require('uuid');
    const crypto = require('crypto');

    /**
     * JWT 인증 토큰을 생성합니다.
     * @param {string} accessKey - 발급받은 Access Key
     * @param {string} secretKey - 발급받은 Secret Key
     * @param {string} query - 쿼리 문자열 (파라미터가 없으면 빈 문자열)
     */
    function generateToken(accessKey, secretKey, query = '') {
      const payload = {
        access_key: accessKey,
        nonce: uuidv4(),
        timestamp: Date.now(),
      };

      if (query) {
        const hash = crypto.createHash('SHA512');
        payload.query_hash = hash.update(query, 'utf-8').digest('hex');
        payload.query_hash_alg = 'SHA512';
      }

      return jwt.sign(payload, secretKey);
    }

    module.exports = { generateToken };
    ```


  
**Python**
```python title="auth.py"
    import jwt
    import uuid
    import hashlib
    import time


    def generate_token(access_key, secret_key, query=''):
        """JWT 인증 토큰을 생성합니다.

        Args:
            access_key: 발급받은 Access Key
            secret_key: 발급받은 Secret Key
            query: 쿼리 문자열 (파라미터가 없으면 빈 문자열)
        """
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': round(time.time() * 1000),
        }

        if query:
            hash_obj = hashlib.sha512()
            hash_obj.update(query.encode('utf-8'))
            payload['query_hash'] = hash_obj.hexdigest()
            payload['query_hash_alg'] = 'SHA512'

        return jwt.encode(payload, secret_key)
    ```


  
**Java**
```java title="AuthHelper.java"
    import com.auth0.jwt.JWT;
    import com.auth0.jwt.algorithms.Algorithm;
    import java.math.BigInteger;
    import java.nio.charset.StandardCharsets;
    import java.security.MessageDigest;
    import java.util.UUID;

    public class AuthHelper {

        /**
         * JWT 인증 토큰을 생성합니다.
         * @param accessKey 발급받은 Access Key
         * @param secretKey 발급받은 Secret Key
         * @param query     쿼리 문자열 (파라미터가 없으면 빈 문자열)
         */
        public static String generateToken(String accessKey, String secretKey, String query)
                throws Exception {
            Algorithm algorithm = Algorithm.HMAC256(secretKey);
            var builder = JWT.create()
                    .withClaim("access_key", accessKey)
                    .withClaim("nonce", UUID.randomUUID().toString())
                    .withClaim("timestamp", System.currentTimeMillis());

            if (query != null && !query.isEmpty()) {
                MessageDigest md = MessageDigest.getInstance("SHA-512");
                md.update(query.getBytes(StandardCharsets.UTF_8));
                String queryHash = String.format("%0128x", new BigInteger(1, md.digest()));
                builder.withClaim("query_hash", queryHash)
                       .withClaim("query_hash_alg", "SHA512");
            }

            return builder.sign(algorithm);
        }
    }
    ```


### 주문 가능 정보 조회

주문 전에 해당 거래 대상 페어의 수수료, 최소 주문 금액, 계좌 잔고를 확인합니다. 쿼리 파라미터가 있는 GET 요청 예시입니다.


  
**Node.js**
```javascript
    require('dotenv').config();
    const axios = require('axios');
    const { generateToken } = require('./auth');

    const accessKey = process.env.BITHUMB_ACCESS_KEY;
    const secretKey = process.env.BITHUMB_SECRET_KEY;
    const apiUrl = 'https://api.bithumb.com';

    const query = 'market=KRW-BTC';
    const token = generateToken(accessKey, secretKey, query);

    axios.get(apiUrl + '/v1/orders/chance?' + query, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((response) => {
        const data = response.data;
        console.log(`매수 수수료: ${data.bid_fee}`);
        console.log(`매도 수수료: ${data.ask_fee}`);
        console.log(`최소 주문 금액: ${data.market.bid.min_total}`);
        console.log(`주문 가능 잔고: ${data.bid_account.balance} ${data.bid_account.currency}`);
      })
      .catch((error) => {
        console.error(error.response?.data || error.message);
      });
    ```


  
**Python**
```python
    from dotenv import load_dotenv
    import os
    import requests
    from auth import generate_token

    load_dotenv()

    access_key = os.environ['BITHUMB_ACCESS_KEY']
    secret_key = os.environ['BITHUMB_SECRET_KEY']
    api_url = 'https://api.bithumb.com'

    query = 'market=KRW-BTC'
    token = generate_token(access_key, secret_key, query)
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(api_url + '/v1/orders/chance?' + query, headers=headers)
    data = response.json()

    if response.status_code == 200:
        print(f"매수 수수료: {data['bid_fee']}")
        print(f"매도 수수료: {data['ask_fee']}")
        print(f"최소 주문 금액: {data['market']['bid']['min_total']}")
        print(f"주문 가능 잔고: {data['bid_account']['balance']} {data['bid_account']['currency']}")
    else:
        print(f"에러: {data}")
    ```


  
**Java**
```java
    import org.apache.http.client.methods.CloseableHttpResponse;
    import org.apache.http.client.methods.HttpGet;
    import org.apache.http.impl.client.CloseableHttpClient;
    import org.apache.http.impl.client.HttpClients;
    import org.apache.http.util.EntityUtils;
    import java.nio.charset.StandardCharsets;

    public class OrderChance {
        public static void main(String[] args) throws Exception {
            String accessKey = System.getenv("BITHUMB_ACCESS_KEY");
            String secretKey = System.getenv("BITHUMB_SECRET_KEY");
            String apiUrl = "https://api.bithumb.com";

            String query = "market=KRW-BTC";
            String token = AuthHelper.generateToken(accessKey, secretKey, query);

            HttpGet request = new HttpGet(apiUrl + "/v1/orders/chance?" + query);
            request.addHeader("Authorization", "Bearer " + token);

            try (CloseableHttpClient client = HttpClients.createDefault();
                 CloseableHttpResponse response = client.execute(request)) {
                int status = response.getStatusLine().getStatusCode();
                String body = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                System.out.println("HTTP " + status);
                System.out.println(body);
            }
        }
    }
    ```


> 응답 필드 전체 목록은 [주문 가능 정보 조회](ref:주문-가능-정보) API 레퍼런스를 참고하세요.


### 주문 요청

지정가 매수 주문을 생성합니다. POST 요청 시 body 파라미터도 동일하게 쿼리 문자열로 변환하여 `query_hash`를 생성합니다.


  
**Node.js**
```javascript
    require('dotenv').config();
    const axios = require('axios');
    const { generateToken } = require('./auth');

    const accessKey = process.env.BITHUMB_ACCESS_KEY;
    const secretKey = process.env.BITHUMB_SECRET_KEY;
    const apiUrl = 'https://api.bithumb.com';

    const requestBody = {
      market: 'KRW-BTC',
      side: 'bid',
      order_type: 'limit',
      price: 80000000,     // 주문 가격 (원)
      volume: 0.001,       // 주문 수량 (BTC)
    };

    // body 파라미터를 쿼리 문자열로 변환하여 해싱
    const query = Object.entries(requestBody)
      .map(([key, value]) => `${key}=${value}`)
      .join('&');

    const token = generateToken(accessKey, secretKey, query);

    axios.post(apiUrl + '/v2/orders', requestBody, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    })
      .then((response) => {
        console.log('주문 성공');
        console.log(`주문 ID: ${response.data.order_id}`);
        console.log(`거래 대상 페어: ${response.data.market}`);
        console.log(`주문 유형: ${response.data.side}`);
        console.log(`생성 시각: ${response.data.created_at}`);
      })
      .catch((error) => {
        console.error('주문 실패:', error.response?.data || error.message);
      });
    ```


  
**Python**
```python
    from dotenv import load_dotenv
    import os
    import requests
    import json
    from auth import generate_token

    load_dotenv()

    access_key = os.environ['BITHUMB_ACCESS_KEY']
    secret_key = os.environ['BITHUMB_SECRET_KEY']
    api_url = 'https://api.bithumb.com'

    request_body = {
        'market': 'KRW-BTC',
        'side': 'bid',
        'order_type': 'limit',
        'price': 80000000,     # 주문 가격 (원)
        'volume': 0.001,       # 주문 수량 (BTC)
    }

    # body 파라미터를 쿼리 문자열로 변환하여 해싱
    query = '&'.join([f'{k}={v}' for k, v in request_body.items()])
    token = generate_token(access_key, secret_key, query)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        api_url + '/v2/orders',
        data=json.dumps(request_body),
        headers=headers,
    )
    data = response.json()

    if response.status_code == 201:
        print('주문 성공')
        print(f"주문 ID: {data['order_id']}")
        print(f"거래 대상 페어: {data['market']}")
        print(f"주문 유형: {data['side']}")
        print(f"생성 시각: {data['created_at']}")
    else:
        print(f"주문 실패: {data}")
    ```


  
**Java**
```java
    import org.apache.http.client.methods.CloseableHttpResponse;
    import org.apache.http.client.methods.HttpPost;
    import org.apache.http.entity.StringEntity;
    import org.apache.http.impl.client.CloseableHttpClient;
    import org.apache.http.impl.client.HttpClients;
    import org.apache.http.util.EntityUtils;
    import com.fasterxml.jackson.databind.ObjectMapper;
    import java.nio.charset.StandardCharsets;
    import java.util.LinkedHashMap;
    import java.util.Map;

    public class PlaceOrder {
        public static void main(String[] args) throws Exception {
            String accessKey = System.getenv("BITHUMB_ACCESS_KEY");
            String secretKey = System.getenv("BITHUMB_SECRET_KEY");
            String apiUrl = "https://api.bithumb.com";

            // body 파라미터 구성
            Map requestBody = new LinkedHashMap<>();
            requestBody.put("market", "KRW-BTC");
            requestBody.put("side", "bid");
            requestBody.put("order_type", "limit");
            requestBody.put("price", 80000000);    // 주문 가격 (원)
            requestBody.put("volume", 0.001);      // 주문 수량 (BTC)

            // body 파라미터를 쿼리 문자열로 변환하여 해싱
            String query = requestBody.entrySet().stream()
                    .map(entry -> entry.getKey() + "=" + entry.getValue())
                    .collect(java.util.stream.Collectors.joining("&"));

            String token = AuthHelper.generateToken(accessKey, secretKey, query);

            HttpPost request = new HttpPost(apiUrl + "/v2/orders");
            request.addHeader("Authorization", "Bearer " + token);
            request.addHeader("Content-Type", "application/json");
            request.setEntity(new StringEntity(
                    new ObjectMapper().writeValueAsString(requestBody), StandardCharsets.UTF_8));

            try (CloseableHttpClient client = HttpClients.createDefault();
                 CloseableHttpResponse response = client.execute(request)) {
                int status = response.getStatusLine().getStatusCode();
                String body = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                System.out.println("HTTP " + status);
                System.out.println(body);
            }
        }
    }
    ```


> 위 코드를 실행하면 **실제 주문이 접수됩니다.** 테스트 시 가격을 현재 시세보다 충분히 낮게 설정하여 체결되지 않도록 한 뒤, 아래 주문 취소를 통해 취소하세요.


> 응답 필드 전체 목록은 [주문 요청](ref:주문-요청) API 레퍼런스를 참고하세요.


### 주문 취소

접수된 주문을 취소합니다. DELETE 요청 예시입니다.


  
**Node.js**
```javascript
    require('dotenv').config();
    const axios = require('axios');
    const { generateToken } = require('./auth');

    const accessKey = process.env.BITHUMB_ACCESS_KEY;
    const secretKey = process.env.BITHUMB_SECRET_KEY;
    const apiUrl = 'https://api.bithumb.com';

    const orderId = '주문_요청에서_받은_order_id';
    const query = `order_id=${orderId}`;
    const token = generateToken(accessKey, secretKey, query);

    axios.delete(apiUrl + '/v2/order?' + query, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((response) => {
        console.log('주문 취소 성공');
        console.log(`취소된 주문 ID: ${response.data.order_id}`);
      })
      .catch((error) => {
        console.error('주문 취소 실패:', error.response?.data || error.message);
      });
    ```


  
**Python**
```python
    from dotenv import load_dotenv
    import os
    import requests
    from auth import generate_token

    load_dotenv()

    access_key = os.environ['BITHUMB_ACCESS_KEY']
    secret_key = os.environ['BITHUMB_SECRET_KEY']
    api_url = 'https://api.bithumb.com'

    order_id = '주문_요청에서_받은_order_id'
    query = f'order_id={order_id}'
    token = generate_token(access_key, secret_key, query)
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.delete(api_url + '/v2/order?' + query, headers=headers)
    data = response.json()

    if response.status_code == 200:
        print('주문 취소 성공')
        print(f"취소된 주문 ID: {data['order_id']}")
    else:
        print(f"주문 취소 실패: {data}")
    ```


  
**Java**
```java
    import org.apache.http.client.methods.CloseableHttpResponse;
    import org.apache.http.client.methods.HttpDelete;
    import org.apache.http.impl.client.CloseableHttpClient;
    import org.apache.http.impl.client.HttpClients;
    import org.apache.http.util.EntityUtils;
    import java.nio.charset.StandardCharsets;

    public class CancelOrder {
        public static void main(String[] args) throws Exception {
            String accessKey = System.getenv("BITHUMB_ACCESS_KEY");
            String secretKey = System.getenv("BITHUMB_SECRET_KEY");
            String apiUrl = "https://api.bithumb.com";

            String orderId = "주문_요청에서_받은_order_id";
            String query = "order_id=" + orderId;
            String token = AuthHelper.generateToken(accessKey, secretKey, query);

            HttpDelete request = new HttpDelete(apiUrl + "/v2/order?" + query);
            request.addHeader("Authorization", "Bearer " + token);

            try (CloseableHttpClient client = HttpClients.createDefault();
                 CloseableHttpResponse response = client.execute(request)) {
                int status = response.getStatusLine().getStatusCode();
                String body = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                System.out.println("HTTP " + status);
                System.out.println(body);
            }
        }
    }
    ```


> 에러 응답(404, 422 등) 상세는 [주문 취소 접수](ref:주문-취소-접수) API 레퍼런스를 참고하세요.


## 다음 단계


  - [인증 토큰 생성하기](인증-토큰-생성하기): JWT 구조, payload 필드, query_hash 생성 규칙을 상세히 설명합니다.

  - [API 레퍼런스](api-레퍼런스): 전체 엔드포인트의 파라미터, 응답 스키마, 코드 샘플을 확인합니다.
