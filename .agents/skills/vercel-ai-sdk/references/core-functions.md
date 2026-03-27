# AI SDK v6 Core Functions Reference

## Overview

AI SDK v6 provides two primary functions for text generation:

- `generateText` - Non-streaming text generation
- `streamText` - Streaming text generation

**Important:** `generateObject` and `streamObject` are **deprecated** in v6. Use `generateText`/`streamText` with `Output` helpers instead.

## generateText

Non-streaming text generation for non-interactive use cases.

### Basic Usage

```typescript
import { generateText } from "ai";
import { anthropic } from "@ai-sdk/anthropic";

const { text } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  prompt: "Why is the sky blue?",
});

console.log(text);
```

### With System Prompt

```typescript
const { text } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  system: "You are a physics professor. Explain concepts simply.",
  prompt: "Why is the sky blue?",
});
```

### Parameters

| Parameter         | Type                   | Description                      |
| ----------------- | ---------------------- | -------------------------------- |
| `model`           | `LanguageModel`        | Required. The model to use       |
| `prompt`          | `string`               | The user prompt                  |
| `system`          | `string`               | Optional system message          |
| `messages`        | `ModelMessage[]`       | For multi-turn conversations     |
| `tools`           | `Record<string, Tool>` | Available tools                  |
| `toolChoice`      | `ToolChoice`           | `'auto'`, `'required'`, `'none'` |
| `maxSteps`        | `number`               | Max tool call iterations         |
| `output`          | `Output<T>`            | Structured output schema         |
| `temperature`     | `number`               | Randomness (0-2)                 |
| `maxOutputTokens` | `number`               | Max tokens to generate           |
| `topP`            | `number`               | Nucleus sampling                 |
| `topK`            | `number`               | Top-k sampling                   |
| `seed`            | `number`               | For reproducibility              |

### Return Value

```typescript
{
  text: string;              // Generated text
  output?: T;                // Typed structured output (if Output specified)
  toolCalls: ToolCall[];     // Tool invocations made
  toolResults: ToolResult[]; // Results from tool executions
  finishReason: string;      // 'stop' | 'length' | 'tool-calls' | etc.
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  response: RawResponse;     // Raw provider response
  warnings: Warning[];       // Provider-specific warnings
}
```

## streamText

Streaming text generation for interactive applications.

### Basic Usage

```typescript
import { streamText } from "ai";
import { anthropic } from "@ai-sdk/anthropic";

const result = streamText({
  model: anthropic("claude-sonnet-4-5"),
  prompt: "Write a poem about AI.",
});

// Iterate over text stream
for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}
```

### For Chat Applications

```typescript
import { streamText, convertToModelMessages } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import type { UIMessage } from "ai";

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: anthropic("claude-sonnet-4-5"),
    system: "You are a helpful assistant.",
    messages: convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
```

### Response Methods

```typescript
// For useChat hook compatibility
result.toUIMessageStreamResponse();

// For simple text streaming
result.toTextStreamResponse();
```

### Callbacks

```typescript
const result = streamText({
  model: anthropic("claude-sonnet-4-5"),
  prompt: "Hello",

  onChunk: ({ chunk }) => {
    // Called for each streaming chunk
    console.log("Chunk:", chunk);
  },

  onStepFinish: ({ stepType, text, toolCalls }) => {
    // Called after each step (text generation or tool call)
    console.log("Step finished:", stepType);
  },

  onFinish: async ({ text, usage, finishReason }) => {
    // Called when generation completes
    console.log("Finished:", finishReason);
    console.log("Total tokens:", usage.totalTokens);

    // Good place for database saves, logging, etc.
    await saveToDatabase(text);
  },

  onError: async (error) => {
    // Called on error
    console.error("Error:", error);
    await logError(error);
  },
});
```

## Structured Output

### Output.object()

Generate typed objects:

```typescript
import { generateText, Output } from "ai";
import { z } from "zod";

const { output } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  output: Output.object({
    schema: z.object({
      sentiment: z.enum(["positive", "neutral", "negative"]),
      topics: z.array(z.string()),
      confidence: z.number().min(0).max(1),
    }),
  }),
  prompt: 'Analyze: "The product is amazing but shipping was slow"',
});

// Typed access
console.log(output.sentiment); // 'positive' | 'neutral' | 'negative'
console.log(output.topics); // string[]
console.log(output.confidence); // number
```

### Output.array()

Generate typed arrays:

```typescript
const { output } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  output: Output.array({
    schema: z.object({
      name: z.string(),
      description: z.string(),
    }),
  }),
  prompt: "List 5 programming languages with descriptions",
});

// output: Array<{ name: string; description: string }>
output.forEach((item) => {
  console.log(item.name, "-", item.description);
});
```

### Output.choice()

Generate enum values:

```typescript
const { output } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  output: Output.choice({
    choices: ["technical", "billing", "general"] as const,
  }),
  prompt: 'Classify this query: "How do I reset my password?"',
});

// output: 'technical' | 'billing' | 'general'
switch (output) {
  case "technical":
    return handleTechnicalQuery();
  case "billing":
    return handleBillingQuery();
  case "general":
    return handleGeneralQuery();
}
```

### Output.json()

Generate unstructured JSON:

```typescript
const { output } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  output: Output.json(),
  prompt: "Return user preferences as JSON",
});

// output: unknown (untyped JSON)
```

## Tool Calling

### Basic Tool Usage

```typescript
import { generateText, tool } from "ai";
import { z } from "zod";

const { text, toolCalls, toolResults } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  tools: {
    getWeather: tool({
      description: "Get weather for a location",
      inputSchema: z.object({
        city: z.string(),
        unit: z.enum(["C", "F"]),
      }),
      execute: async ({ city, unit }) => {
        // API call
        return { temp: 24, unit, condition: "Sunny" };
      },
    }),
  },
  prompt: "What is the weather in Tokyo?",
});
```

### Multi-Step Tool Calling

```typescript
const { text } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  tools: {
    search: searchTool,
    analyze: analyzeTool,
    summarize: summarizeTool,
  },
  maxSteps: 5, // Allow up to 5 tool call iterations
  prompt: "Search for AI trends, analyze them, and summarize",
});
```

### Tool Choice Control

```typescript
// Auto (default) - Model decides when to use tools
toolChoice: 'auto'

// Required - Must use at least one tool
toolChoice: 'required'

// None - Disable tool calling
toolChoice: 'none'

// Force specific tool
toolChoice: { type: 'tool', toolName: 'getWeather' }
```

## Model Specification

### Provider Functions (Direct)

```typescript
import { anthropic } from "@ai-sdk/anthropic";
import { openai } from "@ai-sdk/openai";
import { google } from "@ai-sdk/google";

// Anthropic models
anthropic("claude-sonnet-4-5");
anthropic("claude-opus-4-5");
anthropic("claude-haiku-4-5");

// OpenAI models
openai("gpt-4o");
openai("gpt-4o-mini");
openai("gpt-4-turbo");

// Google models
google("gemini-2.0-flash");
google("gemini-2.0-pro");
```

### Vercel AI Gateway (Recommended for Production)

```typescript
import { gateway } from "ai";

// Anthropic models via gateway
gateway("anthropic/claude-sonnet-4-5");
gateway("anthropic/claude-haiku-4-5");
gateway("anthropic/claude-opus-4-5");

// Example usage
const { text } = await generateText({
  model: gateway("anthropic/claude-sonnet-4-5"),
  prompt: "Hello, world!",
});
```

**Benefits of Gateway:**

- Unified interface across providers
- Built-in rate limiting and caching
- Observability and analytics
- Automatic retries and error handling

### Provider Options

```typescript
const { text } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  prompt: "Hello",
  // Provider-specific options
  providerOptions: {
    anthropic: {
      thinking: { type: "enabled", budgetTokens: 10000 },
    },
  },
});
```

## Generation Parameters

```typescript
const { text } = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  prompt: "Write a story",

  // Temperature: 0 = deterministic, 2 = very random
  temperature: 0.7,

  // Max tokens to generate
  maxOutputTokens: 1000,

  // Nucleus sampling
  topP: 0.9,

  // Top-k sampling
  topK: 40,

  // Frequency penalty
  frequencyPenalty: 0.5,

  // Presence penalty
  presencePenalty: 0.5,

  // Stop sequences
  stopSequences: ["END", "---"],

  // Seed for reproducibility
  seed: 12345,
});
```

## Migration from v5

### Deprecated: generateObject

```typescript
// ❌ v5 (deprecated)
import { generateObject } from 'ai';
const result = await generateObject({
  model: anthropic('claude-sonnet-4-5'),
  schema: z.object({...}),
  prompt: '...',
});
const data = result.object;

// ✅ v6
import { generateText, Output } from 'ai';
const { output } = await generateText({
  model: anthropic('claude-sonnet-4-5'),
  output: Output.object({ schema: z.object({...}) }),
  prompt: '...',
});
```

### Deprecated: streamObject

```typescript
// ❌ v5 (deprecated)
import { streamObject } from 'ai';
const result = streamObject({...});

// ✅ v6
import { streamText, Output } from 'ai';
const result = streamText({
  output: Output.object({ schema: z.object({...}) }),
  ...
});
```

### Response Methods

```typescript
// ❌ v5
return result.toDataStreamResponse();

// ✅ v6
return result.toUIMessageStreamResponse();
```

## Best Practices

1. **Use structured output for predictable responses** - `Output.object()` ensures type safety
2. **Set appropriate token limits** - Prevent runaway costs with `maxOutputTokens`
3. **Use callbacks for side effects** - `onFinish` for saves, `onError` for logging
4. **Handle tool errors** - Wrap tool execute functions in try-catch
5. **Convert messages properly** - Always use `convertToModelMessages()` in API routes
