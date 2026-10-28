---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review the design of this REST API:

```
POST /api/getUser         body: { "id": 5 }
POST /api/createOrder
GET  /api/orders/list?page=2
POST /api/deleteOrder/12
```

Every call returns HTTP 200. Failures come back as { "success": false, "msg": "..." }.
