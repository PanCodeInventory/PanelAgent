# AI SDK v6 MCP Integration Reference

## Overview

Model Context Protocol (MCP) allows connecting to external servers for dynamic tool access. AI SDK v6 provides `@ai-sdk/mcp` for seamless integration.

## Installation

```bash
bun add @ai-sdk/mcp @modelcontextprotocol/sdk
```

## Transport Options

### HTTP Transport (Production)

Recommended for production deployments:

```typescript
import { createMCPClient } from "@ai-sdk/mcp";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const httpTransport = new StreamableHTTPClientTransport(
  new URL("https://mcp-server.example.com/mcp"),
  {
    headers: {
      Authorization: `Bearer ${process.env.MCP_API_KEY}`,
    },
  }
);

const mcpClient = await createMCPClient({
  transport: httpTransport,
});
```

### SSE Transport

For Server-Sent Events streaming:

```typescript
import { createMCPClient } from "@ai-sdk/mcp";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const sseTransport = new SSEClientTransport(
  new URL("https://mcp-server.example.com/mcp/sse")
);

const mcpClient = await createMCPClient({
  transport: sseTransport,
});
```

### Stdio Transport (Development)

For local development with subprocess:

```typescript
import { createMCPClient, Experimental_StdioMCPTransport } from "@ai-sdk/mcp";

const stdioTransport = new Experimental_StdioMCPTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
});

const mcpClient = await createMCPClient({
  transport: stdioTransport,
});
```

## Model Selection

MCP integration works with both direct providers and gateway:

```typescript
// Direct provider
import { anthropic } from "@ai-sdk/anthropic";
model: anthropic("claude-sonnet-4-5");

// Gateway (recommended for production)
import { gateway } from "ai";
model: gateway("anthropic/claude-sonnet-4-5");
```

## Basic Usage

### Fetching Tools

```typescript
import { createMCPClient } from "@ai-sdk/mcp";
import { streamText, gateway } from "ai";

const mcpClient = await createMCPClient({ transport });

// Get tools from MCP server
const tools = await mcpClient.tools();

const result = streamText({
  model: gateway("anthropic/claude-sonnet-4-5"),
  tools,
  prompt: "Search for documents about AI",
});
```

### Complete API Route Example

```typescript
// app/api/mcp-chat/route.ts
import { createMCPClient } from "@ai-sdk/mcp";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { streamText, convertToModelMessages, gateway } from "ai";
import type { UIMessage } from "ai";

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  // Create transport
  const httpTransport = new StreamableHTTPClientTransport(
    new URL(process.env.MCP_SERVER_URL!),
    {
      headers: {
        Authorization: `Bearer ${process.env.MCP_API_KEY}`,
      },
    }
  );

  // Create MCP client
  const mcpClient = await createMCPClient({
    transport: httpTransport,
  });

  try {
    // Fetch tools from MCP server
    const tools = await mcpClient.tools();

    // Stream response with MCP tools
    const response = streamText({
      model: gateway("anthropic/claude-sonnet-4-5"),
      messages: convertToModelMessages(messages),
      tools,
      onFinish: async () => {
        await mcpClient.close();
      },
      onError: async () => {
        await mcpClient.close();
      },
    });

    return response.toUIMessageStreamResponse();
  } catch (error) {
    await mcpClient.close();
    console.error("MCP error:", error);
    return new Response("Internal Server Error", { status: 500 });
  }
}
```

## Tool Schema Definition

### Auto-Discovery

Tools are automatically discovered from the MCP server:

```typescript
const tools = await mcpClient.tools();
// tools contains all available tools from the server
```

### Explicit Schema Definition

For type safety, define expected schemas:

```typescript
import { z } from "zod";
import { tool } from "ai";

// Define expected tool schemas locally
const weatherTool = tool({
  description: "Get weather from MCP server",
  inputSchema: z.object({
    city: z.string(),
    units: z.enum(["celsius", "fahrenheit"]),
  }),
  // No execute - MCP server handles execution
});

// Merge with MCP tools
const mcpTools = await mcpClient.tools();
const allTools = {
  ...mcpTools,
  weather: weatherTool, // Override with typed version if needed
};
```

## Accessing Resources

MCP servers can provide resources (documents, data):

```typescript
// List available resources
const resources = await mcpClient.resources();

// Access a specific resource
const document = await mcpClient.readResource("documents://my-doc.md");
console.log(document.content);
```

## Accessing Prompts

MCP servers can provide pre-defined prompts:

```typescript
// List available prompts
const prompts = await mcpClient.prompts();

// Get a specific prompt
const prompt = await mcpClient.getPrompt("summarize", {
  text: "Long document content...",
});

// Use the prompt
const result = await generateText({
  model: anthropic("claude-sonnet-4-5"),
  prompt: prompt.content,
});
```

## Multiple MCP Clients

Combine tools from multiple MCP servers:

```typescript
import { createMCPClient } from "@ai-sdk/mcp";

// Create clients for different servers
const filesystemClient = await createMCPClient({
  transport: filesystemTransport,
});

const databaseClient = await createMCPClient({
  transport: databaseTransport,
});

const searchClient = await createMCPClient({
  transport: searchTransport,
});

// Merge all tools
const allTools = {
  ...(await filesystemClient.tools()),
  ...(await databaseClient.tools()),
  ...(await searchClient.tools()),
};

// Use combined tools
const result = streamText({
  model: anthropic("claude-sonnet-4-5"),
  tools: allTools,
  prompt:
    "Search for files about AI and query the database for related records",
  onFinish: async () => {
    await Promise.all([
      filesystemClient.close(),
      databaseClient.close(),
      searchClient.close(),
    ]);
  },
});
```

## Elicitation Support

For interactive flows requiring user input:

```typescript
const mcpClient = await createMCPClient({
  transport,
  onElicitation: async (request) => {
    // Handle user input request from MCP server
    switch (request.type) {
      case "confirm":
        return await showConfirmDialog(request.message);

      case "select":
        return await showSelectDialog(request.options);

      case "input":
        return await showInputDialog(request.prompt);

      default:
        throw new Error(`Unknown elicitation type: ${request.type}`);
    }
  },
});
```

## OAuth Integration

For MCP servers requiring OAuth:

```typescript
import { createMCPClient } from "@ai-sdk/mcp";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const transport = new StreamableHTTPClientTransport(
  new URL("https://mcp-server.example.com/mcp"),
  {
    // OAuth token management
    getHeaders: async () => {
      const token = await getOAuthToken();
      return {
        Authorization: `Bearer ${token}`,
      };
    },
    // Token refresh handling
    onUnauthorized: async () => {
      await refreshOAuthToken();
      // Transport will retry with new token
    },
  }
);

const mcpClient = await createMCPClient({ transport });
```

## Error Handling

```typescript
import { createMCPClient } from "@ai-sdk/mcp";

try {
  const mcpClient = await createMCPClient({ transport });

  try {
    const tools = await mcpClient.tools();

    const result = streamText({
      model: anthropic("claude-sonnet-4-5"),
      tools,
      prompt: userMessage,
      onFinish: async () => {
        await mcpClient.close();
      },
      onError: async (error) => {
        console.error("Stream error:", error);
        await mcpClient.close();
      },
    });

    return result.toUIMessageStreamResponse();
  } catch (toolError) {
    console.error("Tool execution error:", toolError);
    await mcpClient.close();
    return new Response("Tool execution failed", { status: 500 });
  }
} catch (connectionError) {
  console.error("MCP connection error:", connectionError);
  return new Response("MCP server unavailable", { status: 503 });
}
```

## Client Lifecycle Management

Always close clients properly:

```typescript
// Pattern 1: Using callbacks
const response = streamText({
  model,
  tools,
  prompt,
  onFinish: async () => {
    await mcpClient.close();
  },
  onError: async () => {
    await mcpClient.close();
  },
});

// Pattern 2: Using try-finally
try {
  const tools = await mcpClient.tools();
  const { text } = await generateText({ model, tools, prompt });
  return Response.json({ text });
} finally {
  await mcpClient.close();
}

// Pattern 3: Using a wrapper
async function withMCPClient<T>(
  transport: Transport,
  fn: (client: MCPClient) => Promise<T>
): Promise<T> {
  const client = await createMCPClient({ transport });
  try {
    return await fn(client);
  } finally {
    await client.close();
  }
}

// Usage
const result = await withMCPClient(transport, async (client) => {
  const tools = await client.tools();
  return generateText({ model, tools, prompt });
});
```

## Popular MCP Servers

### Filesystem Server

```typescript
const transport = new Experimental_StdioMCPTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
});
```

### GitHub Server

```typescript
const transport = new Experimental_StdioMCPTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-github"],
  env: {
    GITHUB_TOKEN: process.env.GITHUB_TOKEN,
  },
});
```

### Brave Search Server

```typescript
const transport = new Experimental_StdioMCPTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-brave-search"],
  env: {
    BRAVE_API_KEY: process.env.BRAVE_API_KEY,
  },
});
```

## Best Practices

1. **Use HTTP/SSE for production** - More reliable than Stdio
2. **Always close clients** - Prevent resource leaks
3. **Handle errors gracefully** - MCP servers may be unavailable
4. **Define explicit schemas** - For better type safety
5. **Use OAuth when available** - For secure authentication
6. **Combine tools carefully** - Avoid naming conflicts
7. **Monitor tool usage** - Track which MCP tools are used

## Transport Comparison

| Transport | Use Case          | Pros               | Cons                         |
| --------- | ----------------- | ------------------ | ---------------------------- |
| HTTP      | Production        | Reliable, scalable | Requires server hosting      |
| SSE       | Real-time updates | Built-in streaming | More complex setup           |
| Stdio     | Development       | Easy setup, local  | Single process, not scalable |
