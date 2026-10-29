# Service design
The service calls its billing provider using a bearer token. An attacker with a position on the network may intercept or modify outbound traffic.

```python
def fetch_invoice(token):
    return requests.get("https://billing.example.test/invoices", headers={"Authorization": f"Bearer {token}"}, verify=False)
```
