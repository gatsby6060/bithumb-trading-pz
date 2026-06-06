# 일(Day) 캔들 조회

지정한 거래 페어의 일 단위 캔들 데이터를 조회합니다.


---

## 일(Day) 캔들 조회

지정한 거래 페어의 일 단위 캔들 데이터를 조회합니다.

| 항목 | 내용 |
|------|------|
| **Method** | `GET` |
| **URL** | `https://api.bithumb.com/v1/candles/days` |
| **인증** | ❌ 인증 불필요 (Public) |
| **Content-Type** | `application/json` |

### 요청 파라미터

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `market` | string | ✅ | 거래 대상 페어의 고유 심볼 (예시: KRW-BTC) |
| `to` | string |  | 조회 기준 시각(KST). 해당 시각의 캔들은 제외되며, 미입력 시 가장 최근 캔들 기준으로 조회합니다. (형식: yyyy-MM-dd HH:mm:ss 또는 yyyy-MM-ddTHH:mm:ss) |
| `count` | integer |  | 조회할 캔들 개수(max 200) |
| `convertingPriceUnit` | string |  | 원화 마켓이 아닌 다른 마켓의 일봉 요청 시, 종가를 지정한 화폐 단위로 환산하여 `converted_trade_price` 필드로 반환.

- 현재는 `KRW`만 지원합니다. |

### 응답

#### `200` ✅ 성공

**응답 예시**

```json
"[\n  {\n    \"market\": \"KRW-BTC\",\n    \"candle_date_time_utc\": \"2018-04-18T00:00:00\",\n    \"candle_date_time_kst\": \"2018-04-18T09:00:00\",\n    \"opening_price\": 8450000,\n    \"high_price\": 8679000,\n    \"low_price\": 8445000,\n    \"trade_price\": 8626000,\n    \"timestamp\": 1524046650532,\n    \"candle_acc_trade_price\": 107184005903.68721,\n    \"candle_acc_trade_volume\": 12505.93101659,\n    \"prev_closing_price\": 8450000,\n    \"change_price\": 176000,\n    \"change_rate\": 0.0208284024\n  }\n]"
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
| `prev_closing_price` | number |  | 전일 종가(UTC 0시 기준) |
| `change_price` | number |  | 전일 종가 대비 변화 금액 |
| `change_rate` | number |  | 전일 종가 대비 변화율 |
| `converted_trade_price` | number |  | 환산된 종가(`convertingPriceUnit` 요청 시 반환) |

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

fetch('https://api.bithumb.com/v1/candles/days?market=KRW-BTC&count=1', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

#### Python

```python
import requests

url = "https://api.bithumb.com/v1/candles/days?market=KRW-BTC&count=1"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)
```

#### Java

```java
OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
  .url("https://api.bithumb.com/v1/candles/days?market=KRW-BTC&count=1")
  .get()
  .addHeader("accept", "application/json")
  .build();

Response response = client.newCall(request).execute();
```
