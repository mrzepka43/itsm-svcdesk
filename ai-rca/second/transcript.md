# Second investigation transcript

## Context supplied to the investigator

The investigator received the following verified readings from recording lab4-rec-1: at 05:04:30Z the checkout `PlaceOrder` and frontend `POST /api/checkout` p95 were 5.5 seconds; the checkout internal span, product-catalog, and shipping p95 values remained near their baseline readings; email `POST /send_order_confirmation` p95 was 110 ms; Ad-service errors were 0.01078/s; checkout `PlaceOrder` rate was 0.075/s. At the healthy baseline 04:56:00Z, checkout `PlaceOrder` p95 was 48 ms, checkout internal span p95 47.88 ms, product-catalog p95 31.93 ms, shipping p95 1.9 ms, and email p95 7.7 ms. The investigator was not given the sealed flag state.

## Investigator response

**Second on-call assessment — Lab 4**

At 05:04:30Z, checkout `PlaceOrder` and frontend `POST /api/checkout` p95 were 5.5 s, while the measured checkout internal span and product-catalog and shipping p95s remained near baseline. Email `POST /send_order_confirmation` was 110 ms, but that is not directly comparable to the 7.7 ms baseline email server span. Ad-server errors were 0.01078/s; checkout `PlaceOrder` rate was 0.075/s. These observations identify symptoms, not causes.

**PromQL limitation:** The supplied results do not include metric names or label keys. To avoid inventing them, the queries below are templates, not executable until placeholders are replaced with the exact selectors used by recording lab4-rec-1.

1. **Checkout outer path:** The slowdown may be outside the measured internal span or dependencies. Test whether PlaceOrder p95 rose while the internal-span p95 stayed near baseline:
   ```promql
   histogram_quantile(0.95, sum by (le) (rate(<PLACEORDER_BUCKET_METRIC>{<PLACEORDER_LABELS>}[5m])))
   ```
   Compare with the corresponding internal-span bucket query over the same window.

2. **Ad-server errors:** Ad-server errors may coincide with the checkout slowdown, but the observed error rate alone does not establish impact. Test their rate around onset and compare it with PlaceOrder latency:
   ```promql
   rate(<AD_SERVER_ERROR_COUNTER>{<AD_SERVER_LABELS>}[5m])
   ```
   ```promql
   histogram_quantile(0.95, sum by (le) (rate(<PLACEORDER_BUCKET_METRIC>{<PLACEORDER_LABELS>}[5m])))
   ```

3. **Email endpoint:** The 110 ms email endpoint p95 may be a contributor only if checkout waits on that operation; the snapshots do not establish that relationship. Test whether its p95 rose during the same interval:
   ```promql
   histogram_quantile(0.95, sum by (le) (rate(<EMAIL_SEND_BUCKET_METRIC>{<EMAIL_SEND_LABELS>}[5m])))
   ```

The incident onset was 05:01:00Z; `ShopCheckoutSlow` was detected at 05:06:19Z. The available snapshots cannot determine root cause or prove a causal link between these symptoms.
