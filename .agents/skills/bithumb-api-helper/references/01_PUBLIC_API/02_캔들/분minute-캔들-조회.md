# 분(Minute) 캔들 조회

지정한 거래 페어의 분 단위 캔들 데이터를 조회합니다.


---

## 분(Minute) 캔들 조회

지정한 거래 페어의 분 단위 캔들 데이터를 조회합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `GET` |
| **URL** | `https://api.bithumb.com/v1/candles/minutes/{unit}` |
| **인증** | ❌ 인증 불필요 (Public) |
| **Content-Type** | `application/json` |

### 요청 파라미터

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `market` | string | ✅ | 거래 대상 페어의 고유 심볼 (예시: KRW-BTC) |
| `to` | string |  | 조회 기준 시각(KST). 해당 시각의 캔들은 제외되며, 미입력 시 가장 최근 캔들 기준으로 조회합니다. (형식: yyyy-MM-dd HH:mm:ss 또는 yyyy-MM-ddTHH:mm:ss) |
| `count` | integer |  | 조회할 캔들 개수(max 200) |

### 응답

#### `200` ✅ 성공

**응답 예시**

```json
"[\n  {\n    \"market\": \"KRW-BTC\",\n    \"candle_date_time_utc\": \"2018-04-18T10:16:00\",\n    \"candle_date_time_kst\": \"2018-04-18T19:16:00\",\n    \"opening_price\": 8615000,\n    \"high_price\": 8618000,\n    \"low_price\": 8611000,\n    \"trade_price\": 8616000,\n    \"timestamp\": 1524046594584,\n    \"candle_acc_trade_price\": 60018891.90054,\n    \"candle_acc_trade_volume\": 6.96780929,\n    \"unit\": 1\n  }\n]"
```

**응답 필드** (배열 항목)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `market` | string |  | 거래 대상 페어의 고유 심볼 (예시: KRW-BTC) |
| `candle_date_time_utc` | string |  | 캔들 기준 시각(UTC) |
| `candle_date_time_kst` | string |  | 캔들 기준 시각(KST) |
| `opening_price` | number |  | 시가 |
| `high_price` | number |  | 고가 |
| `low_price` | number |  | 저가 |
| `trade_price` | number |  | 종가 |
| `timestamp` | string |  | 캔들 기간 중 발생한 마지막 거래 시각(Unix timestamp, Unit: ms) |
| `candle_acc_trade_price` | number |  | 캔들 기간 중 누적 거래 금액 |
| `candle_acc_trade_volume` | number |  | 캔들 기간 중 누적 거래량 |
| `unit` | integer |  | 분 단위(유닛) |

#### `400` ❌ 오류

**응답 예시**

```json
"{\n    \"error\": {\n        \"name\": \"error name\",\n    \t\t\"message\": \"error message\"\n    }\n}"
```

**응답 필드**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `error` | object | ✅ |  |

### 코드 샘플

#### Javascript

```javascript
const options = {method: 'GET', headers: {accept: 'application/json'}};

fetch('https://api.bithumb.com/v1/candles/minutes/1?market=KRW-BTC&count=1', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

#### Python

```python
import requests

url = "https://api.bithumb.com/v1/candles/minutes/1?market=KRW-BTC&count=1"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)
```

#### Java

```java
OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
  .url("https://api.bithumb.com/v1/candles/minutes/1?market=KRW-BTC&count=1")
  .get()
  .addHeader("accept", "application/json")
  .build();

Response response = client.newCall(request).execute();
```
