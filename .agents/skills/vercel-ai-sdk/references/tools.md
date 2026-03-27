# AI SDK v6 Tools Reference

## Overview

Tools enable AI models to call functions with structured parameters. In v6, you **must** use the `tool()` helper function.

## Basic Tool Definition

```typescript
import { tool } from "ai";
import { z } from "zod";

const weatherTool = tool({
  description: "Get weather for a location",
  inputSchema: z.object({
    city: z.string().describe("City name"),
    unit: z.enum(["C", "F"]).describe("Temperature unit"),
  }),
  execute: async ({ city, unit }) => {
    // Implement the tool logic
    return {
      temperature: 24,
      unit,
      condition: "Sunny",
    };
  },
});
```

## Required Properties

| Property      | Type                     | Description                                   |
| ------------- | ------------------------ | --------------------------------------------- |
| `inputSchema` | `ZodSchema`              | **Required.** Zod schema for input validation |
| `description` | `string`                 | Helps model decide when to use the tool       |
| `execute`     | `async (args) => result` | Function that performs the action             |

## Optional Properties

| Property       | Type        | Description                  |
| -------------- | ----------- | ---------------------------- |
| `outputSchema` | `ZodSchema` | Schema for validating output |

## CRITICAL: Use tool() Helper

### Wrong (Will Fail)

```typescript
// ❌ WRONG - Plain object without tool() wrapper
tools: {
  myTool: {
    description: 'My tool',
    parameters: z.object({...}),  // ❌ Wrong property name
    execute: async ({...}) => {...},
  }
}
```

**Error:** `Type '{ description: string; parameters: ... }' is not assignable to type '{ inputSchema: FlexibleSchema<any>; ... }'`

### Correct

```typescript
// ✅ CORRECT - Use tool() helper
import { tool } from 'ai';

tools: {
  myTool: tool({
    description: 'My tool',
    inputSchema: z.object({...}),  // ✅ Correct property name
    execute: async ({...}) => {...},
  }),
}
```

## Schema Patterns

### Simple Schema

```typescript
const searchTool = tool({
  description: "Search the web",
  inputSchema: z.object({
    query: z.string(),
  }),
  execute: async ({ query }) => {
    return { results: ["..."] };
  },
});
```

### Complex Schema

```typescript
const createUserTool = tool({
  description: "Create a new user",
  inputSchema: z.object({
    name: z.string().min(1).max(100),
    email: z.string().email(),
    age: z.number().int().min(0).max(150).optional(),
    role: z.enum(["admin", "user", "guest"]).default("user"),
    preferences: z
      .object({
        theme: z.enum(["light", "dark"]),
        notifications: z.boolean(),
      })
      .optional(),
    tags: z.array(z.string()).max(10),
  }),
  execute: async (input) => {
    const user = await db.users.create(input);
    return { id: user.id, created: true };
  },
});
```

### With Output Schema

```typescript
const analyzerTool = tool({
  description: "Analyze text sentiment",
  inputSchema: z.object({
    text: z.string(),
  }),
  outputSchema: z.object({
    sentiment: z.enum(["positive", "neutral", "negative"]),
    confidence: z.number().min(0).max(1),
    keywords: z.array(z.string()),
  }),
  execute: async ({ text }) => {
    // Analysis logic
    return {
      sentiment: "positive",
      confidence: 0.92,
      keywords: ["great", "amazing"],
    };
  },
});
```

## Using Tools with generateText

### With Direct Provider

```typescript
import { generateText, tool } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { z } from "zod";

const { text, toolCalls, toolResults } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  tools: {
    getWeather: tool({
      description: "Get weather for a city",
      inputSchema: z.object({
        city: z.string(),
      }),
      execute: async ({ city }) => {
        return { temp: 24, condition: "Sunny" };
      },
    }),
  },
  prompt: "What is the weather in Tokyo?",
});

console.log(text);
console.log("Tool calls:", toolCalls);
console.log("Tool results:", toolResults);
```

### With Gateway (Recommended for Production)

```typescript
import { generateText, tool, gateway } from "ai";
import { z } from "zod";

const { text, toolCalls, toolResults } = await generateText({
  model: gateway("anthropic/claude-sonnet-4-5"),
  tools: {
    getWeather: tool({
      description: "Get weather for a city",
      inputSchema: z.object({
        city: z.string(),
      }),
      execute: async ({ city }) => {
        return { temp: 24, condition: "Sunny" };
      },
    }),
  },
  prompt: "What is the weather in Tokyo?",
});
```

## Using Tools with streamText

```typescript
import { streamText, tool, convertToModelMessages } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { z } from "zod";
import type { UIMessage } from "ai";

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: anthropic("claude-sonnet-4-5"),
    messages: convertToModelMessages(messages),
    tools: {
      getWeather: tool({
        description: "Get weather for a city",
        inputSchema: z.object({
          city: z.string(),
          unit: z.enum(["C", "F"]).default("C"),
        }),
        execute: async ({ city, unit }) => {
          return `It's 24°${unit} and sunny in ${city}`;
        },
      }),
      searchWeb: tool({
        description: "Search the web",
        inputSchema: z.object({
          query: z.string(),
        }),
        execute: async ({ query }) => {
          // Search implementation
          return { results: ["Result 1", "Result 2"] };
        },
      }),
    },
  });

  return result.toUIMessageStreamResponse();
}
```

## Tool Choice Control

```typescript
// Auto (default) - Model decides when to use tools
const result = await generateText({
  tools: {
    /* ... */
  },
  toolChoice: "auto",
  prompt: "...",
});

// Required - Must use at least one tool
const result = await generateText({
  tools: {
    /* ... */
  },
  toolChoice: "required",
  prompt: "...",
});

// None - Disable tool usage
const result = await generateText({
  tools: {
    /* ... */
  },
  toolChoice: "none",
  prompt: "...",
});

// Force specific tool
const result = await generateText({
  tools: {
    /* ... */
  },
  toolChoice: { type: "tool", toolName: "getWeather" },
  prompt: "...",
});
```

## Multi-Step Tool Calling

Allow the model to call multiple tools iteratively:

```typescript
const { text } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  tools: {
    search: searchTool,
    analyze: analyzeTool,
    summarize: summarizeTool,
  },
  maxSteps: 5, // Allow up to 5 iterations
  prompt: "Search for AI news, analyze the results, and summarize",
});
```

## Client-Side Tool Handling

For tools that require user interaction:

```typescript
// Define tool without execute (client-side handling)
const confirmTool = tool({
  description: "Ask user for confirmation",
  inputSchema: z.object({
    message: z.string(),
  }),
  // No execute - handled client-side
});

// Client component
("use client");

import { useChat } from "@ai-sdk/react";

function Chat() {
  const { messages, sendMessage, addToolOutput } = useChat({
    onToolCall: async ({ toolCall }) => {
      if (toolCall.name === "confirm") {
        // Show confirmation dialog
        const confirmed = await showConfirmDialog(toolCall.args.message);

        // Send result back
        addToolOutput({
          toolCallId: toolCall.id,
          result: { confirmed },
        });
      }
    },
  });

  // ...
}
```

## Error Handling

```typescript
const safeTool = tool({
  description: "Fetch data from API",
  inputSchema: z.object({
    endpoint: z.string().url(),
  }),
  execute: async ({ endpoint }) => {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      // Return error information instead of throwing
      return {
        error: true,
        message: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },
});
```

## Tool Descriptions Best Practices

Good descriptions help the model choose the right tool:

```typescript
// ❌ BAD - Vague description
tool({
  description: "Do something",
  // ...
});

// ✅ GOOD - Clear, specific description
tool({
  description:
    "Get current weather conditions including temperature, humidity, and forecast for a specific city",
  // ...
});

// ✅ GOOD - Include when to use it
tool({
  description:
    "Search the knowledge base for product documentation. Use when the user asks about product features, pricing, or technical specifications.",
  // ...
});
```

## Schema Descriptions

Add descriptions to schema fields to help the model:

```typescript
const bookingTool = tool({
  description: "Book a restaurant reservation",
  inputSchema: z.object({
    restaurant: z.string().describe("Name of the restaurant"),
    date: z.string().describe("Date in YYYY-MM-DD format"),
    time: z.string().describe("Time in HH:MM format (24-hour)"),
    partySize: z.number().int().min(1).max(20).describe("Number of guests"),
    specialRequests: z
      .string()
      .optional()
      .describe("Dietary restrictions, celebrations, seating preferences"),
  }),
  execute: async (input) => {
    // Booking logic
  },
});
```

## Alternative Schema Libraries

### Valibot

```typescript
import { valibotSchema } from "@ai-sdk/valibot";
import * as v from "valibot";

const myTool = tool({
  description: "My tool",
  inputSchema: valibotSchema(
    v.object({
      query: v.string(),
    })
  ),
  execute: async ({ query }) => {
    // ...
  },
});
```

### Raw JSON Schema

```typescript
const myTool = tool({
  description: "My tool",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string" },
    },
    required: ["query"],
  },
  execute: async ({ query }) => {
    // ...
  },
});
```

## Common Patterns

### API Integration Tool

```typescript
const apiTool = tool({
  description: "Make authenticated API request",
  inputSchema: z.object({
    endpoint: z.string(),
    method: z.enum(["GET", "POST", "PUT", "DELETE"]).default("GET"),
    body: z.record(z.unknown()).optional(),
  }),
  execute: async ({ endpoint, method, body }) => {
    const response = await fetch(`https://api.example.com${endpoint}`, {
      method,
      headers: {
        Authorization: `Bearer ${process.env.API_KEY}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return response.json();
  },
});
```

### Database Query Tool

```typescript
const dbQueryTool = tool({
  description: "Query the database for user information",
  inputSchema: z.object({
    userId: z.string().uuid(),
    fields: z.array(z.enum(["name", "email", "role", "createdAt"])),
  }),
  outputSchema: z.object({
    name: z.string().optional(),
    email: z.string().optional(),
    role: z.string().optional(),
    createdAt: z.string().optional(),
  }),
  execute: async ({ userId, fields }) => {
    const user = await db.users.findUnique({
      where: { id: userId },
      select: Object.fromEntries(fields.map((f) => [f, true])),
    });
    return user || {};
  },
});
```

### File Operations Tool

```typescript
const fileReadTool = tool({
  description: "Read content from a file",
  inputSchema: z.object({
    path: z.string().describe("File path relative to project root"),
    encoding: z.enum(["utf-8", "base64"]).default("utf-8"),
  }),
  execute: async ({ path, encoding }) => {
    const content = await fs.readFile(path, encoding);
    return { content, size: content.length };
  },
});
```

## Tool Checklist

Before implementing any tool:

- \[ ] Import `tool` from 'ai' package
- \[ ] Wrap tool definition with `tool({ ... })`
- \[ ] Use `inputSchema` (not `parameters`)
- \[ ] Use zod schema: `z.object({ ... })`
- \[ ] Add clear `description`
- \[ ] Implement `execute` function
- \[ ] Add descriptions to schema fields
- \[ ] Handle errors gracefully
- \[ ] Consider adding `outputSchema` for validation
