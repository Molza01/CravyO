# cravyo-agent A2A API Reference

**Endpoint:** `POST http://localhost:5000/a2a/v1`  
**Content-Type:** `application/json`  
**Auth:** none required — agent runs in `permissive` mode

---

## Envelope (every call)

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "method": "message/send",
  "params": {
    "message": {
      "kind": "message",
      "messageId": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "parts": [ "...see actions below..." ]
    }
  }
}
```

Two part styles work interchangeably:

| Style | Example |
|---|---|
| **DataPart** — raw object in `"data"` field | `{"kind": "data", "data": {"action": "..."}}` |
| **TextPart** — JSON string in `"text"` field | `{"kind": "text", "text": "{\"action\": \"...\"}"}` |

---

## Actions

### `analyze` — detect cravings from a real Instagram / YouTube feed

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440001",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "analyze",
          "username": "foodie_reel",
          "platform": "instagram",
          "dietary": "veg",
          "near_restaurant": true,
          "location": { "lat": 18.52, "lng": 73.85 }
        }
      }]
    }
  }
}
```

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `username` | string | required | Instagram username or YouTube channel handle |
| `platform` | `"instagram"` \| `"youtube"` | `"instagram"` | Which platform to scrape |
| `dietary` | `"all"` \| `"veg"` \| `"non-veg"` \| `"gym"` \| `"diet"` \| `"vegan"` | `"all"` | Dietary filter applied to suggestions |
| `near_restaurant` | boolean | `false` | Enables Dineout mode when user is near a restaurant |
| `location` | `{lat, lng}` | `{lat: 18.52, lng: 73.85}` | GPS coordinates for city-aware suggestions |

---

### `analyze_mock` — run the pipeline on caller-supplied posts (no scraping)

```json
{
  "jsonrpc": "2.0",
  "id": "req-2",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440002",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "analyze_mock",
          "posts": [
            {
              "caption": "biryani night! 🍛 #biryani",
              "hashtags": ["biryani"],
              "thumbnail_url": ""
            },
            {
              "caption": "hakka noodles obsession #noodles",
              "hashtags": ["noodles"],
              "thumbnail_url": ""
            }
          ],
          "dietary": "all",
          "near_restaurant": false,
          "time_context": "evening",
          "city": "Pune"
        }
      }]
    }
  }
}
```

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `posts` | array | required | List of `{caption, hashtags, thumbnail_url}` objects |
| `dietary` | string | `"all"` | Same options as `analyze` |
| `near_restaurant` | boolean | `false` | |
| `time_context` | `"morning"` \| `"afternoon"` \| `"evening"` \| `"late_night"` | `"afternoon"` | Affects suggestion tone |
| `city` | string | `"Pune"` | City for price comparison |

---

### `compare_prices` — price breakdown across Swiggy channels

```json
{
  "jsonrpc": "2.0",
  "id": "req-3",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440003",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "compare_prices",
          "dish": "chicken biryani",
          "city": "Mumbai"
        }
      }]
    }
  }
}
```

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `dish` | string | required | Dish name to compare |
| `city` | string | `"Pune"` | City for pricing context |

---

### `record_order` — save a confirmed order to personalization memory

```json
{
  "jsonrpc": "2.0",
  "id": "req-4",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440004",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "record_order",
          "restaurant": "Behrouz Biryani",
          "dish": "Chicken Dum Biryani",
          "channel": "food_delivery",
          "price": 349,
          "cuisine": "indian",
          "rating": 5
        }
      }]
    }
  }
}
```

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `restaurant` | string | required | |
| `dish` | string | required | |
| `channel` | `"food_delivery"` \| `"instamart"` \| `"dineout"` | `"food_delivery"` | |
| `price` | number | optional | Price in INR |
| `cuisine` | string | optional | e.g. `"indian"`, `"chinese"` |
| `rating` | integer 1–5 | optional | Star rating |

---

### `skip` — dismiss a restaurant (stops appearing after 2 skips)

```json
{
  "jsonrpc": "2.0",
  "id": "req-5",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440005",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "skip",
          "restaurant": "McDonald's"
        }
      }]
    }
  }
}
```

---

### `rate_last_order` — rate the most recent order 1–5 stars

```json
{
  "jsonrpc": "2.0",
  "id": "req-6",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440006",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "rate_last_order",
          "rating": 4
        }
      }]
    }
  }
}
```

---

### `get_memory` — retrieve user preferences and order history

```json
{
  "jsonrpc": "2.0",
  "id": "req-7",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440007",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": { "action": "get_memory" }
      }]
    }
  }
}
```

---

### `clear_memory` — wipe all stored preferences

```json
{
  "jsonrpc": "2.0",
  "id": "req-8",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440008",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": { "action": "clear_memory" }
      }]
    }
  }
}
```

---

### `get_trends` — craving trends for the past 30 days

```json
{
  "jsonrpc": "2.0",
  "id": "req-9",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440009",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": { "action": "get_trends" }
      }]
    }
  }
}
```

---

### `get_demo_posts` — fetch a preset batch of posts for testing

```json
{
  "jsonrpc": "2.0",
  "id": "req-10",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440010",
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "action": "get_demo_posts",
          "preset": "chinese"
        }
      }]
    }
  }
}
```

**Presets:** `chinese` | `snacks` | `indian` | `gym` | `italian`

---

### Natural-language fallback (LangChain / Groq)

No `action` field — plain text is routed to the Groq LLM agent which
can call all the above actions autonomously as tools.

```json
{
  "jsonrpc": "2.0",
  "id": "req-11",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440011",
      "role": "user",
      "parts": [{
        "kind": "text",
        "text": "What should I eat tonight based on my order history?"
      }]
    }
  }
}
```

---

### Multi-turn conversation — `contextId`

Pass the same `contextId` on every message in a session. The agent uses
it as the per-sender key for conversation history.

```json
{
  "jsonrpc": "2.0",
  "id": "req-12",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "550e8400-e29b-41d4-a716-446655440012",
      "contextId": "user-session-abc123",
      "role": "user",
      "parts": [{ "kind": "text", "text": "Actually, make it vegan." }]
    }
  }
}
```

---

## Response shape

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "result": {
    "id": "<task-id>",
    "contextId": "<context-id>",
    "status": { "state": "completed" },
    "artifacts": [{
      "artifactId": "<uuid>",
      "name": "result",
      "parts": [{
        "kind": "data",
        "data": {
          "success": true,
          "result": "Craving detected: Biryani! Order from Behrouz Biryani ..."
        }
      }]
    }]
  }
}
```

## Error response

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "result": {
    "id": "<task-id>",
    "contextId": "<context-id>",
    "status": { "state": "failed" },
    "artifacts": [{
      "name": "result",
      "parts": [{ "kind": "data", "data": { "success": false, "error": "..." } }]
    }]
  }
}
```

## JSON-RPC error codes

| Code | Meaning |
|---|---|
| `-32700` | Parse error — body is not valid JSON |
| `-32600` | Invalid request — not a valid JSON-RPC 2.0 envelope |
| `-32601` | Method not found |
| `-32602` | Invalid params — `message` shape is wrong |
| `-32603` | Internal server error |
| `-32001` | Task not found |
| `-32100` | Auth failed (strict mode only) |
| `-32101` | Replay detected (strict mode only) |
| `-32102` | Auth expired (strict mode only) |
