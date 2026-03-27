# AI SDK v6 Middleware Reference

## Overview

Middleware intercepts and modifies model behavior. Use it for logging, caching, RAG, guardrails, and more.

## Model Selection

Middleware works with both direct providers and gateway:

```typescript
// Direct provider
import { anthropic } from "@ai-sdk/anthropic";
const model = anthropic("claude-sonnet-4-5");

// Gateway (recommended for production)
import { gateway } from "ai";
const model = gateway("anthropic/claude-sonnet-4-5");
```

## Built-in Middleware

### Extract Reasoning

Extract thinking/reasoning from models like Claude:

```typescript
import { extractReasoningMiddleware, wrapLanguageModel, gateway } from "ai";

const modelWithReasoning = wrapLanguageModel({
  model: gateway("anthropic/claude-sonnet-4-5"),
  middleware: extractReasoningMiddleware({
    tagName: "thinking",
  }),
});

const { text, reasoning } = await generateText({
  model: modelWithReasoning,
  prompt: "Solve this step by step: What is 15% of 80?",
});

console.log("Reasoning:", reasoning);
console.log("Answer:", text);
```

### Simulate Streaming

Convert non-streaming responses to streaming:

```typescript
import { simulateStreamingMiddleware, wrapLanguageModel } from "ai";

const streamingModel = wrapLanguageModel({
  model: someNonStreamingModel,
  middleware: simulateStreamingMiddleware(),
});
```

### Default Settings

Apply consistent configuration:

```typescript
import { defaultSettingsMiddleware, wrapLanguageModel } from "ai";

const modelWithDefaults = wrapLanguageModel({
  model: anthropic("claude-sonnet-4-5"),
  middleware: defaultSettingsMiddleware({
    temperature: 0.7,
    maxOutputTokens: 1000,
    topP: 0.9,
  }),
});
```

## Custom Middleware

### Middleware Hooks

| Hook              | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `transformParams` | Modify request parameters before sending |
| `wrapGenerate`    | Wrap non-streaming generation            |
| `wrapStream`      | Wrap streaming generation                |

### Logging Middleware

```typescript
import { LanguageModelMiddleware, wrapLanguageModel } from "ai";

const loggingMiddleware: LanguageModelMiddleware = {
  transformParams: async ({ params }) => {
    console.log("Request:", {
      prompt: params.prompt,
      temperature: params.temperature,
    });
    return params;
  },

  wrapGenerate: async ({ doGenerate, params }) => {
    const startTime = Date.now();
    const result = await doGenerate();
    const duration = Date.now() - startTime;

    console.log("Response:", {
      text: result.text?.substring(0, 100),
      tokens: result.usage?.totalTokens,
      duration,
    });

    return result;
  },
};

const loggedModel = wrapLanguageModel({
  model: anthropic("claude-sonnet-4-5"),
  middleware: loggingMiddleware,
});
```

### Caching Middleware

```typescript
const cache = new Map<string, unknown>();

const cachingMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    // Create cache key from params
    const cacheKey = JSON.stringify({
      prompt: params.prompt,
      system: params.system,
      temperature: params.temperature,
    });

    // Check cache
    if (cache.has(cacheKey)) {
      console.log("Cache hit");
      return cache.get(cacheKey) as any;
    }

    // Generate and cache
    const result = await doGenerate();
    cache.set(cacheKey, result);

    return result;
  },
};
```

### RAG Middleware

Inject context from vector search:

```typescript
const ragMiddleware: LanguageModelMiddleware = {
  transformParams: async ({ params }) => {
    // Extract query from prompt
    const query =
      typeof params.prompt === "string"
        ? params.prompt
        : params.messages?.[params.messages.length - 1]?.content;

    if (!query) return params;

    // Search for relevant documents
    const relevantDocs = await vectorDB.search(query, { limit: 5 });
    const context = relevantDocs.map((d) => d.content).join("\n\n");

    // Inject context into system message
    const enhancedSystem = params.system
      ? `${params.system}\n\nRelevant context:\n${context}`
      : `Use this context to answer:\n${context}`;

    return {
      ...params,
      system: enhancedSystem,
    };
  },
};

const ragModel = wrapLanguageModel({
  model: anthropic("claude-sonnet-4-5"),
  middleware: ragMiddleware,
});
```

### Guardrails Middleware

Filter sensitive content:

```typescript
const guardrailsMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    const result = await doGenerate();

    // Filter output
    if (result.text) {
      // Remove sensitive patterns
      result.text = result.text
        .replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[SSN REDACTED]")
        .replace(
          /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
          "[EMAIL REDACTED]"
        )
        .replace(/\b\d{16}\b/g, "[CARD NUMBER REDACTED]");
    }

    return result;
  },

  wrapStream: async ({ doStream, params }) => {
    const stream = await doStream();

    // For streaming, you need to buffer and filter
    // This is more complex and may require custom implementation
    return stream;
  },
};
```

### Rate Limiting Middleware

```typescript
const rateLimiter = new Map<string, number[]>();
const RATE_LIMIT = 10; // requests
const WINDOW_MS = 60000; // per minute

const rateLimitMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    const userId = (params.providerMetadata?.userId as string) || "default";
    const now = Date.now();

    // Get user's request history
    const requests = rateLimiter.get(userId) || [];

    // Filter to requests within window
    const recentRequests = requests.filter((t) => now - t < WINDOW_MS);

    if (recentRequests.length >= RATE_LIMIT) {
      throw new Error("Rate limit exceeded");
    }

    // Record this request
    recentRequests.push(now);
    rateLimiter.set(userId, recentRequests);

    return doGenerate();
  },
};
```

### Cost Tracking Middleware

```typescript
const costTracker = new Map<string, number>();

const COST_PER_1K_TOKENS = {
  "claude-sonnet-4-5": { input: 0.003, output: 0.015 },
};

const costTrackingMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    const result = await doGenerate();

    const userId = (params.providerMetadata?.userId as string) || "default";
    const modelCosts = COST_PER_1K_TOKENS["claude-sonnet-4-5"];

    const cost =
      (result.usage.promptTokens / 1000) * modelCosts.input +
      (result.usage.completionTokens / 1000) * modelCosts.output;

    const totalCost = (costTracker.get(userId) || 0) + cost;
    costTracker.set(userId, totalCost);

    console.log(`User ${userId} cost: $${totalCost.toFixed(4)}`);

    return result;
  },
};
```

## Combining Multiple Middleware

```typescript
const enhancedModel = wrapLanguageModel({
  model: anthropic("claude-sonnet-4-5"),
  middleware: [
    loggingMiddleware,
    rateLimitMiddleware,
    cachingMiddleware,
    ragMiddleware,
    guardrailsMiddleware,
  ],
});
```

**Execution order:** First middleware in array wraps all subsequent ones:
`loggingMiddleware(rateLimitMiddleware(cachingMiddleware(ragMiddleware(guardrailsMiddleware(model)))))`

## Passing Metadata

Pass context through `providerOptions`:

```typescript
// In API route
const result = await generateText({
  model: enhancedModel,
  prompt: userMessage,
  providerOptions: {
    metadata: {
      userId: session.user.id,
      requestId: crypto.randomUUID(),
      timestamp: Date.now(),
    },
  },
});

// In middleware
const myMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    const { userId, requestId } = params.providerMetadata as {
      userId: string;
      requestId: string;
    };

    console.log(`Processing request ${requestId} for user ${userId}`);

    return doGenerate();
  },
};
```

## Stream Handling

Handling streams requires buffering:

```typescript
const streamFilterMiddleware: LanguageModelMiddleware = {
  wrapStream: async ({ doStream, params }) => {
    const originalStream = await doStream();

    // Create a transform stream to filter chunks
    const filteredStream = new TransformStream({
      transform(chunk, controller) {
        // Filter or modify chunk
        if (chunk.type === "text-delta") {
          // Example: Remove certain words
          chunk.text = chunk.text.replace(/badword/gi, "***");
        }
        controller.enqueue(chunk);
      },
    });

    return {
      ...originalStream,
      stream: originalStream.stream.pipeThrough(filteredStream),
    };
  },
};
```

## Best Practices

1. **Order matters** - Put logging first, caching early, guardrails last
2. **Handle errors** - Wrap in try-catch, provide fallbacks
3. **Be type-safe** - Use TypeScript for middleware parameters
4. **Consider streaming** - Implement both `wrapGenerate` and `wrapStream`
5. **Minimize latency** - Cache results, use async operations wisely
6. **Log for debugging** - Especially during development
7. **Test thoroughly** - Middleware can have subtle bugs

## Common Patterns

### Development vs Production

```typescript
const middleware =
  process.env.NODE_ENV === "development"
    ? [loggingMiddleware, developmentCacheMiddleware]
    : [productionCacheMiddleware, guardrailsMiddleware];

const model = wrapLanguageModel({
  model: anthropic("claude-sonnet-4-5"),
  middleware,
});
```

### Per-Request Middleware

```typescript
export async function POST(req: Request) {
  const { prompt, useRag } = await req.json();

  const middleware = [loggingMiddleware];

  if (useRag) {
    middleware.push(ragMiddleware);
  }

  const model = wrapLanguageModel({
    model: anthropic("claude-sonnet-4-5"),
    middleware,
  });

  const result = await generateText({ model, prompt });

  return Response.json({ text: result.text });
}
```
