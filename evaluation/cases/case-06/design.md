# Design
An automation service processes external events over mutually authenticated TLS. The verified workload identity is mapped server-side to exactly one tenant, and the backend credential is scoped to that tenant. The service rejects an event when its requested tenant differs from the server-side mapping.

```python
def handle(event, verified_identity):
    tenant = lookup_tenant(verified_identity)
    if event.json["tenant_id"] != tenant:
        return response(status=403)
    return backend.get_customer_data(tenant, credential=tenant_credentials[tenant])
```
