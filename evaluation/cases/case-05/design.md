# Design
An automation service processes external events. Each event carries a tenant ID provided by the sender. The service uses a single privileged backend credential for all tenants.

```python
def handle(event):
    tenant = event.json["tenant_id"]
    return backend.get_customer_data(tenant, credential=ADMIN_KEY)
```

There is no authentication or tenant authorization elsewhere.
