# Design
A support agent reads customer-supplied tickets and can send messages through `send_message(destination, body)`.

```python
def answer(ticket):
    messages = [system_prompt, {"role": "user", "content": ticket.body}]
    return run_agent(messages, tools=[send_message])
```

No downstream policy restricts destinations or requires approval. The agent also has access to confidential account records.
