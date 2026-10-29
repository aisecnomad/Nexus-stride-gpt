# Design
A support assistant reads customer-supplied tickets and drafts replies. It has no tools and no access to account records or secrets. A human reviews its draft and independently decides whether to send it.

```python
def answer(ticket):
    return model.generate(system_prompt, ticket.body)
```
