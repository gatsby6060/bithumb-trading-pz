# API 주요 에러 코드

API 호출 시 발생할 수 있는 주요 에러 코드와 원인을 확인하세요

## 개요

API 요청값이 유효하지 않거나 처리 중 오류가 발생한 경우, HTTP 상태 코드와 함께 다음과 같은 형태의 JSON body가 리턴됩니다.

```json
{
  "error": {
    "name": "",
    "message": ""    
  }
}
```

주요 오류 코드는 다음과 같습니다.

## 400 Bad Request

| 코드                                              | 설명                                          |
| :---------------------------------------------- | :------------------------------------------ |
| `invalid_parameter`                             | 잘못된 파라미터 입니다.                               |
| `invalid_price`                                 | 주문가격 단위를 잘못 입력하셨습니다. 확인 후 시도해주세요.           |
| `under_price_limit_ask` `under_price_limit_bid` | 주문가격은 최소 %s 이상으로 주문 가능합니다.                  |
| `invalid_price_ask` `invalid_price_bid`         | 주문가격 단위를 잘못 입력하셨습니다. 확인 후 시도해주세요.           |
| `bank_account_required`                         | 실명확인 입출금 계좌 등록 후 이용가능합니다.                   |
| `two_factor_auth_required`                      | 유효한 인증채널을 입력하세요.                            |
| `currency does not have a valid value`          | 빗썸에서 지원하지 않는 코인 입니다.                        |
| `cross_trading`                                 | 제출하신 주문은 귀하가 기존에 제출하신 주문과 체결될 수 있어 취소되었습니다. |
| `withdraw_insufficient_balance`                 | 출금 최대 한도가 초과 되었습니다.                         |

## 401 Unauthorized

401 Unauthorized 오류는 대부분 JWT 서명이 올바르게 되지 않았을 때 발생합니다. [인증 토큰 생성하기](https://apidocs.bithumb.com/docs/인증-토큰-생성하기) 문서를 참조하시어 서명이 올바르게 되었는지 확인해주세요.

| 코드                      | 설명                         |
| :---------------------- | :------------------------- |
| `invalid_query_payload` | Jwt의 query를 검증하는데 실패하였습니다. |
| `jwt_verification`      | Jwt 토큰 검증에 실패했습니다.         |
| `expired_jwt`           | Jwt가 만료되었습니다.              |
| `NotAllowIP`            | not allowed client IP      |
| `out_of_scope`          | 권한이 부족합니다.                 |

## 403 Forbidden

403 Forbidden 오류는 대부분 접근 권한이 없거나, 운영 정책에 따라 제한된 기능일 수 있습니다. 더 궁금하신 점은 고객센터로 문의해주세요.

| 코드                  | 설명                                                                           |
| :------------------ | :--------------------------------------------------------------------------- |
| `blocked_member_id` | Service usage has been restricted in accordance with our operational policy. |

## 404 Not Found

| 코드                                       | 설명                |
| :--------------------------------------- | :---------------- |
| `order_not_found`                        | 주문을 찾지 못했습니다.     |
| `deposit_not_found` `withdraw_not_found` | 입출금 정보를 찾지 못했습니다. |

## 422 UNPROCESSABLE_ENTITY

| 코드                | 설명                             |
| :---------------- | :----------------------------- |
| `order_not_ready` | 주문 접수 처리 중입니다. 잠시 후 다시 시도해주세요. |

## 500 Internal Server Error

500 Internal Server Error는 요청에는 문제가 없으나, 서버에서 데이터를 처리하는 과정에서 일시적인 이슈(예: 응답 지연)가 발생했을 때 나타납니다. 잠시 후 다시 시도해주시기 바랍니다.

| 코드             | 설명                               |
| :------------- | :------------------------------- |
| `server_error` | 시스템이 원활하지 않습니다. 잠시 후 다시 시도해 주세요. |


> 에러 코드 목록을 통해 문제를 해결하지 못한 경우 [API 문의 게시판](https://www.bithumb.com/react/login?reurl=/customer_support/question)을 이용해 주세요.
