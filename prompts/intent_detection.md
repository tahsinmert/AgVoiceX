# Intent Detection Contract

The local model must return JSON only. No markdown, no prose, no tool calls.

Allowed intents:

- `reservation_create`
- `reservation_update`
- `reservation_cancel`
- `reservation_lookup`
- `faq`
- `customer_lookup`
- `admin_report`
- `unknown`

Required output shape:

```json
{
  "intent": "reservation_create",
  "customer_name": "",
  "phone": "",
  "email": "",
  "date": "",
  "time": "",
  "people": 2,
  "reservation_id": null,
  "notes": "",
  "question": "",
  "reply": ""
}
```
