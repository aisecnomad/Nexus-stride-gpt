# Design
A customer API authenticates requests. The token middleware provides `request.user` to handlers.

```python
def read_invoice(request, invoice_id):
    invoice = database.get_invoice(invoice_id)
    return json_response(invoice)
```

Invoice IDs are guessable and invoices belong to individual customers.
