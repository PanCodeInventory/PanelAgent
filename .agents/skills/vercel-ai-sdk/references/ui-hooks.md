# AI SDK v6 UI Hooks Reference

## Overview

The `useChat` hook from `@ai-sdk/react` enables building interactive chat UIs with streaming responses, tool integration, and message persistence.

## Installation

```bash
bun add ai @ai-sdk/react
```

## Basic Usage

```typescript
'use client';

import { useChat } from '@ai-sdk/react';
import { useState } from 'react';

export default function Chat() {
  const { messages, sendMessage, status } = useChat();
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage({ text: input });
    setInput('');
  };

  return (
    <div>
      {messages.map((m) => (
        <div key={m.id}>
          <strong>{m.role}:</strong>
          {m.parts.map((part, i) =>
            part.type === 'text' ? <span key={i}>{part.text}</span> : null
          )}
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={status === 'streaming'}
        />
        <button disabled={status === 'streaming'}>Send</button>
      </form>
    </div>
  );
}
```

## Configuration Options

```typescript
const {
  messages,
  sendMessage,
  status,
  error,
  stop,
  regenerate,
  setMessages,
  clearError,
  addToolOutput,
  resumeStream,
} = useChat({
  // API endpoint (default: '/api/chat')
  api: "/api/chat",

  // Unique chat session ID
  id: "my-chat-session",

  // Initial messages
  messages: initialMessages,

  // Custom transport layer
  transport: customTransport,

  // Tool call handler
  onToolCall: async ({ toolCall }) => {
    // Handle client-side tools
  },

  // Called when response completes
  onFinish: (message) => {
    console.log("Response finished:", message);
  },

  // Error handler
  onError: (error) => {
    console.error("Chat error:", error);
  },

  // Auto-send condition
  sendAutomaticallyWhen: (messages) => {
    // Return true to auto-send
    return false;
  },

  // Enable stream resumption
  resume: true,
});
```

## Return Properties

| Property        | Type                 | Description               |
| --------------- | -------------------- | ------------------------- | ------------- | --------- | --------- |
| `messages`      | `UIMessage[]`        | Array of chat messages    |
| `sendMessage`   | `(options) => void`  | Send a message            |
| `status`        | `Status`             | `'submitted'`             | `'streaming'` | `'ready'` | `'error'` |
| `error`         | `Error \| null`      | Current error state       |
| `stop`          | `() => void`         | Abort current stream      |
| `regenerate`    | `() => void`         | Regenerate last response  |
| `setMessages`   | `(messages) => void` | Manually set messages     |
| `clearError`    | `() => void`         | Clear error state         |
| `addToolOutput` | `(output) => void`   | Submit tool result        |
| `resumeStream`  | `() => void`         | Resume interrupted stream |

## Status States

```typescript
status: "submitted"; // Request sent, waiting for response
status: "streaming"; // Receiving streaming response
status: "ready"; // Idle, ready for input
status: "error"; // Error occurred
```

## Message Structure (v6)

Messages in v6 use a parts-based structure:

```typescript
interface UIMessage {
  id: string;
  role: "user" | "assistant" | "system";
  parts: MessagePart[];
}

type MessagePart =
  | { type: "text"; text: string; isStreaming?: boolean }
  | { type: "tool-call"; name: string; args: unknown; state: ToolCallState }
  | { type: "reasoning"; text: string; isStreaming?: boolean }
  | { type: "file"; mediaType: string; url?: string; data?: string }
  | { type: "source"; url?: string; documentId?: string; title?: string }
  | { type: "step" }
  | { type: "data"; data: unknown };
```

## Rendering Messages

```typescript
function MessageRenderer({ message }: { message: UIMessage }) {
  return (
    <div>
      <strong>{message.role}:</strong>
      {message.parts.map((part, index) => {
        switch (part.type) {
          case 'text':
            return (
              <span key={index} className={part.isStreaming ? 'streaming' : ''}>
                {part.text}
              </span>
            );

          case 'tool-call':
            return (
              <div key={index} className="tool-call">
                <span>Tool: {part.name}</span>
                <span>State: {part.state}</span>
                {part.state === 'output' && (
                  <pre>{JSON.stringify(part.result, null, 2)}</pre>
                )}
              </div>
            );

          case 'reasoning':
            return (
              <div key={index} className="reasoning">
                <em>Thinking: {part.text}</em>
              </div>
            );

          case 'file':
            return (
              <div key={index}>
                {part.mediaType.startsWith('image/') ? (
                  <img src={part.url || `data:${part.mediaType};base64,${part.data}`} />
                ) : (
                  <a href={part.url}>Download file</a>
                )}
              </div>
            );

          case 'source':
            return (
              <div key={index} className="source">
                <a href={part.url}>{part.title || 'Source'}</a>
              </div>
            );

          default:
            return null;
        }
      })}
    </div>
  );
}
```

## Tool Call Handling

### Server-Side Tools

Tools with `execute` function are handled server-side automatically.

### Client-Side Tools

For tools requiring user interaction:

```typescript
const { messages, sendMessage, addToolOutput } = useChat({
  onToolCall: async ({ toolCall }) => {
    switch (toolCall.name) {
      case "confirm": {
        // Show confirmation dialog
        const confirmed = await showConfirmDialog(toolCall.args.message);
        addToolOutput({
          toolCallId: toolCall.id,
          result: { confirmed },
        });
        break;
      }

      case "selectOption": {
        // Show option selector
        const selected = await showOptionSelector(toolCall.args.options);
        addToolOutput({
          toolCallId: toolCall.id,
          result: { selected },
        });
        break;
      }

      case "uploadFile": {
        // Show file picker
        const file = await showFilePicker();
        addToolOutput({
          toolCallId: toolCall.id,
          result: { fileName: file.name, content: await file.text() },
        });
        break;
      }
    }
  },
});
```

### Tool Call States

```typescript
type ToolCallState =
  | "input-streaming" // Receiving tool call arguments
  | "invoking" // Tool is being executed
  | "output" // Tool completed successfully
  | "output-error"; // Tool execution failed
```

## Custom Transport

```typescript
import { DefaultChatTransport } from "@ai-sdk/react";

const customTransport = new DefaultChatTransport({
  // Custom endpoint
  api: "/api/custom-chat",

  // Custom headers
  headers: () => ({
    Authorization: `Bearer ${getToken()}`,
    "X-Custom-Header": "value",
  }),
});

const { messages, sendMessage } = useChat({
  transport: customTransport,
});
```

## Message Persistence

### Server-Side Persistence

```typescript
// app/api/chat/route.ts
import { streamText, convertToModelMessages, gateway } from "ai";
// Alternative: import { anthropic } from "@ai-sdk/anthropic";

export async function POST(req: Request) {
  const { messages, chatId } = await req.json();

  const result = streamText({
    // Gateway (recommended for production)
    model: gateway("anthropic/claude-sonnet-4-5"),
    // Alternative: model: anthropic("claude-sonnet-4-5"),
    messages: convertToModelMessages(messages),
    onFinish: async ({ text }) => {
      // Save to database after stream completes
      await db.messages.create({
        chatId,
        role: "assistant",
        content: text,
      });
    },
  });

  return result.toUIMessageStreamResponse();
}
```

### Client-Side Initialization

```typescript
'use client';

import { useChat } from '@ai-sdk/react';
import { useEffect, useState } from 'react';

export default function Chat({ chatId }: { chatId: string }) {
  const [initialMessages, setInitialMessages] = useState<UIMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load messages from database
    async function loadMessages() {
      const messages = await fetch(`/api/chats/${chatId}/messages`).then(r => r.json());
      setInitialMessages(messages);
      setIsLoading(false);
    }
    loadMessages();
  }, [chatId]);

  const { messages, sendMessage, status } = useChat({
    id: chatId,
    messages: initialMessages,
  });

  if (isLoading) return <div>Loading...</div>;

  // ...
}
```

## Stream Resumption

Enable stream resumption for interrupted connections:

```typescript
const { messages, sendMessage, resumeStream } = useChat({
  resume: true, // Enable resume capability
});

// Resume if connection was lost
useEffect(() => {
  if (connectionRestored && status === "streaming") {
    resumeStream();
  }
}, [connectionRestored]);
```

## Auto-Send Messages

```typescript
const { messages, sendMessage } = useChat({
  sendAutomaticallyWhen: (messages) => {
    // Auto-send when last message is a specific tool result
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.role === "tool") {
      return true;
    }
    return false;
  },
});
```

## Type Safety with Agents

```typescript
import type { InferAgentUIMessage } from "ai";
import { myAgent } from "@/agents/my-agent";

// Infer message types from agent
type AgentMessage = InferAgentUIMessage<typeof myAgent>;

function Chat() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);

  // Messages are now typed based on agent's tools
}
```

## Migration from v5

### Sending Messages

```typescript
// ❌ v5 (deprecated)
const { append, input, setInput } = useChat();
append({ content: input, role: "user" });

// ✅ v6
const { sendMessage } = useChat();
const [input, setInput] = useState("");
sendMessage({ text: input });
```

### Rendering Messages

```typescript
// ❌ v5 (deprecated)
<div>{message.content}</div>

// ✅ v6
<div>
  {message.parts.map((part, i) =>
    part.type === 'text' ? <span key={i}>{part.text}</span> : null
  )}
</div>
```

### Input State

```typescript
// ❌ v5 - useChat managed input
const { input, setInput, handleInputChange } = useChat();

// ✅ v6 - Manage input yourself
const [input, setInput] = useState("");
```

## Common Patterns

### With Loading States

```typescript
function Chat() {
  const { messages, sendMessage, status } = useChat();
  const [input, setInput] = useState('');

  const isLoading = status === 'submitted' || status === 'streaming';

  return (
    <div>
      {messages.map(m => <Message key={m.id} message={m} />)}

      {isLoading && <div className="loading">AI is typing...</div>}

      <form onSubmit={handleSubmit}>
        <input value={input} onChange={e => setInput(e.target.value)} />
        <button disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
```

### With Error Handling

```typescript
function Chat() {
  const { messages, sendMessage, status, error, clearError } = useChat({
    onError: (err) => {
      console.error('Chat error:', err);
      toast.error('Failed to send message');
    },
  });

  return (
    <div>
      {messages.map(m => <Message key={m.id} message={m} />)}

      {error && (
        <div className="error">
          <p>{error.message}</p>
          <button onClick={clearError}>Dismiss</button>
          <button onClick={regenerate}>Retry</button>
        </div>
      )}

      {/* ... */}
    </div>
  );
}
```

### With Stop Button

```typescript
function Chat() {
  const { messages, sendMessage, status, stop } = useChat();

  return (
    <div>
      {messages.map(m => <Message key={m.id} message={m} />)}

      {status === 'streaming' && (
        <button onClick={stop} className="stop-button">
          Stop generating
        </button>
      )}

      {/* ... */}
    </div>
  );
}
```

### With Regenerate

```typescript
function Chat() {
  const { messages, sendMessage, status, regenerate } = useChat();

  const lastMessage = messages[messages.length - 1];
  const canRegenerate = lastMessage?.role === 'assistant' && status === 'ready';

  return (
    <div>
      {messages.map(m => <Message key={m.id} message={m} />)}

      {canRegenerate && (
        <button onClick={regenerate}>
          Regenerate response
        </button>
      )}

      {/* ... */}
    </div>
  );
}
```

## Best Practices

1. **Manage input state yourself** - Don't rely on useChat for input
2. **Handle all message part types** - Especially tool-call and reasoning
3. **Show streaming indicators** - Use `isStreaming` on text parts
4. **Implement error handling** - Use `onError` and show user-friendly messages
5. **Support stream control** - Provide stop/regenerate buttons
6. **Persist chats server-side** - Use `onFinish` callback
7. **Use unique chat IDs** - For multi-conversation support
