# 월(Month) 캔들 조회

지정한 거래 페어의 월 단위 캔들 데이터를 조회합니다.


---

## 월(Month) 캔들 조회

지정한 거래 페어의 월 단위 캔들 데이터를 조회합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `GET` |
| **URL** | `https://api.bithumb.com/v1/candles/months` |
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
"[\n  {\n    \"market\": \"KRW-BTC\",\n    \"candle_date_time_utc\": \"2018-04-16T00:00:00\",\n    \"candle_date_time_kst\": \"2018-04-16T09:00:00\",\n    \"opening_price\": 8665000,\n    \"high_price\": 8840000,\n    \"low_price\": 8360000,\n    \"trade_price\": 8611000,\n    \"timestamp\": 1524046708995,\n    \"candle_acc_trade_price\": 466989414916.1301,\n    \"candle_acc_trade_volume\": 54410.56660813,\n    \"first_day_of_period\": \"2018-04-16\"\n  }\n]"
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
| `first_day_of_period` | string |  | 캔들 기간의 시작일 |

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

fetch('https://api.bithumb.com/v1/candles/months?market=KRW-BTC&count=1', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

#### Python

```python
import requests

url = "https://api.bithumb.com/v1/candles/months?market=KRW-BTC&count=1"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)
```

#### Java

```java
OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
  .url("https://api.bithumb.com/v1/candles/months?market=KRW-BTC&count=1")
  .get()
  .addHeader("accept", "application/json")
  .build();

Response response = client.newCall(request).execute();
```
