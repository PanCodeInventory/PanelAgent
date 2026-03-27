# AI SDK v6 Agents Reference

## Overview

The `ToolLoopAgent` class in AI SDK v6 provides a framework for building agentic applications that can use tools iteratively to accomplish complex tasks.

## Installation

```bash
bun add ai @ai-sdk/anthropic zod
```

## Model Selection

Agents work with both direct providers and gateway:

```typescript
// Direct provider
import { anthropic } from "@ai-sdk/anthropic";
model: anthropic("claude-sonnet-4-5");

// Gateway (recommended for production)
import { gateway } from "ai";
model: gateway("anthropic/claude-sonnet-4-5");
```

## Basic Agent Setup

```typescript
import { ToolLoopAgent, tool, stepCountIs, gateway } from "ai";
import { z } from "zod";

const myAgent = new ToolLoopAgent({
  model: gateway("anthropic/claude-sonnet-4-5"),
  instructions: "You are a helpful assistant.",
  tools: {
    getData: tool({
      description: "Fetch data from API",
      inputSchema: z.object({
        query: z.string(),
      }),
      execute: async ({ query }) => {
        return { result: "data for " + query };
      },
    }),
  },
  stopWhen: stepCountIs(20),
});
```

## Configuration Options

| Parameter      | Type                              | Description                                                                      |
| -------------- | --------------------------------- | -------------------------------------------------------------------------------- |
| `model`        | `LanguageModel`                   | The AI model (e.g., `gateway('anthropic/claude-sonnet-4-5')` or direct provider) |
| `instructions` | `string`                          | System prompt defining agent behavior                                            |
| `tools`        | `Record<string, Tool>`            | Available tools the agent can call                                               |
| `stopWhen`     | `StopCondition`                   | When to terminate the agent loop                                                 |
| `toolChoice`   | `ToolChoice`                      | Controls tool usage: `'auto'`, `'required'`, `'none'`                            |
| `output`       | `Output<T>`                       | Optional structured output schema                                                |
| `prepareStep`  | `(step: StepInfo) => StepConfig`  | Dynamic per-step configuration                                                   |
| `prepareCall`  | `(call: CallInfo) => CallOptions` | Runtime options injection (e.g., for RAG)                                        |

## Stop Conditions

### Built-in Conditions

```typescript
import { stepCountIs, hasToolCall } from "ai";

// Stop after N steps
stopWhen: stepCountIs(20);

// Stop when specific tool is called
stopWhen: hasToolCall("finalAnswer");
```

### Custom Conditions

```typescript
const customStopCondition = ({ stepCount, totalTokens, cost, toolCalls }) => {
  // Stop if cost exceeds limit
  if (cost > 0.1) return true;

  // Stop if token limit exceeded
  if (totalTokens > 10000) return true;

  // Stop if specific condition met
  return toolCalls.some((tc) => tc.name === "complete");
};

const agent = new ToolLoopAgent({
  // ...
  stopWhen: customStopCondition,
});
```

## Execution Modes

### Non-Streaming

```typescript
const { text, toolCalls, usage } = await myAgent.generate({
  prompt: "Find and analyze user data",
});

console.log(text);
console.log(
  "Tools called:",
  toolCalls.map((tc) => tc.name)
);
console.log("Tokens used:", usage.totalTokens);
```

### Streaming

```typescript
const stream = myAgent.stream({ prompt: "Find and analyze user data" });

for await (const chunk of stream) {
  if (chunk.type === "text-delta") {
    process.stdout.write(chunk.text);
  } else if (chunk.type === "tool-call") {
    console.log("Calling tool:", chunk.name);
  } else if (chunk.type === "tool-result") {
    console.log("Tool result:", chunk.result);
  }
}
```

## API Route Integration

```typescript
// app/api/agent/route.ts
import { createAgentUIStreamResponse } from "ai";
import { myAgent } from "@/agents/my-agent";

export async function POST(request: Request) {
  const { messages } = await request.json();

  return createAgentUIStreamResponse({
    agent: myAgent,
    uiMessages: messages,
  });
}
```

## Dynamic Tool Control with prepareStep

Control which tools are available at each step:

```typescript
const phaseAgent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  instructions: "You are a research assistant.",
  tools: {
    search: searchTool,
    analyze: analyzeTool,
    summarize: summarizeTool,
  },
  prepareStep: ({ stepCount }) => {
    // Phase 1: Only search
    if (stepCount < 3) {
      return { toolChoice: { type: "tool", toolName: "search" } };
    }
    // Phase 2: Analyze results
    if (stepCount < 6) {
      return { toolChoice: { type: "tool", toolName: "analyze" } };
    }
    // Phase 3: Summarize
    return { toolChoice: { type: "tool", toolName: "summarize" } };
  },
  stopWhen: stepCountIs(10),
});
```

## RAG Integration with prepareCall

Inject context dynamically before each model call:

```typescript
const ragAgent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  instructions: "Answer questions using the provided context.",
  tools: {
    /* ... */
  },
  prepareCall: async ({ prompt }) => {
    // Fetch relevant documents
    const relevantDocs = await vectorSearch(prompt);

    return {
      messages: [
        {
          role: "system",
          content: `Context:\n${relevantDocs.join("\n\n")}`,
        },
      ],
    };
  },
});
```

## Structured Output

```typescript
const structuredAgent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  instructions: "Analyze data and provide structured insights.",
  tools: {
    /* ... */
  },
  output: Output.object({
    schema: z.object({
      summary: z.string(),
      keyPoints: z.array(z.string()),
      confidence: z.number().min(0).max(1),
    }),
  }),
});

const { output } = await structuredAgent.generate({
  prompt: "Analyze market trends",
});

console.log(output.summary);
console.log(output.keyPoints);
console.log(output.confidence);
```

## Client-Side Type Safety

```typescript
import type { InferAgentUIMessage } from "ai";

// Get typed messages from agent
type MyAgentMessage = InferAgentUIMessage<typeof myAgent>;

// Use in React component
function Chat() {
  const [messages, setMessages] = useState<MyAgentMessage[]>([]);
  // ...
}
```

## Multi-Agent Patterns

### Sequential Agents

```typescript
async function sequentialAgents(input: string) {
  // Agent 1: Research
  const { text: research } = await researchAgent.generate({
    prompt: `Research: ${input}`,
  });

  // Agent 2: Analyze
  const { text: analysis } = await analysisAgent.generate({
    prompt: `Analyze this research: ${research}`,
  });

  // Agent 3: Report
  const { output } = await reportAgent.generate({
    prompt: `Generate report from: ${analysis}`,
  });

  return output;
}
```

### Orchestrator Pattern

```typescript
const orchestratorAgent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  instructions: "Coordinate specialized agents to complete tasks.",
  tools: {
    delegateToResearch: tool({
      description: "Delegate to research agent",
      inputSchema: z.object({ query: z.string() }),
      execute: async ({ query }) => {
        const result = await researchAgent.generate({ prompt: query });
        return result.text;
      },
    }),
    delegateToAnalysis: tool({
      description: "Delegate to analysis agent",
      inputSchema: z.object({ data: z.string() }),
      execute: async ({ data }) => {
        const result = await analysisAgent.generate({ prompt: data });
        return result.text;
      },
    }),
  },
});
```

## Best Practices

1. **Set appropriate stop conditions** - Prevent runaway agents with `stepCountIs()` or cost limits
2. **Use specific tool descriptions** - Help the model choose the right tool
3. **Handle errors gracefully** - Implement `onError` callbacks
4. **Monitor token usage** - Track costs with the `usage` return value
5. **Test incrementally** - Start with simple tools and add complexity
6. **Use structured output** - When you need predictable response formats

## Common Pitfalls

### Missing tool() wrapper

```typescript
// ❌ WRONG
tools: {
  myTool: {
    description: 'My tool',
    inputSchema: z.object({...}),
  }
}

// ✅ CORRECT
tools: {
  myTool: tool({
    description: 'My tool',
    inputSchema: z.object({...}),
    execute: async (args) => {...},
  }),
}
```

### Infinite loops

```typescript
// ❌ WRONG - No stop condition
const agent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  tools: {
    /* ... */
  },
});

// ✅ CORRECT - With stop condition
const agent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  tools: {
    /* ... */
  },
  stopWhen: stepCountIs(20),
});
```
