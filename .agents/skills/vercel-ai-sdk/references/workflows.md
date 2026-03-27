# AI SDK v6 Workflow Patterns Reference

## Overview

This guide covers five structured approaches for building reliable AI workflows using the Vercel AI SDK v6.

## Core Patterns

| Pattern             | Use Case             | Characteristics                 |
| ------------------- | -------------------- | ------------------------------- |
| Sequential (Chains) | Dependent steps      | Steps execute one after another |
| Parallel            | Independent tasks    | Run concurrently for efficiency |
| Routing             | Query classification | Direct to appropriate handlers  |
| Orchestrator-Worker | Complex tasks        | Coordinate specialized workers  |
| Evaluator-Optimizer | Quality control      | Iterate until quality threshold |

## Model Selection

All workflow examples use direct provider imports by default. For production, consider using the Vercel AI Gateway:

```typescript
// Direct provider
import { anthropic } from "@ai-sdk/anthropic";
model: anthropic("claude-sonnet-4-5");

// Gateway (recommended for production)
import { gateway } from "ai";
model: gateway("anthropic/claude-sonnet-4-5");
```

## 1. Sequential (Chain) Pattern

Steps execute in predefined order, each building on the previous result.

### Basic Example

```typescript
import { generateText, Output, gateway } from "ai";
import { z } from "zod";

async function contentPipeline(topic: string) {
  // Step 1: Research
  const { text: research } = await generateText({
    model: gateway("anthropic/claude-sonnet-4-5"),
    prompt: `Research key points about: ${topic}`,
  });

  // Step 2: Draft
  const { text: draft } = await generateText({
    model: gateway("anthropic/claude-sonnet-4-5"),
    prompt: `Write an article based on this research:\n\n${research}`,
  });

  // Step 3: Edit
  const { text: final } = await generateText({
    model: gateway("anthropic/claude-sonnet-4-5"),
    prompt: `Edit and improve this article:\n\n${draft}`,
  });

  return final;
}
```

### With Quality Gates

```typescript
async function contentPipelineWithQuality(topic: string) {
  // Step 1: Generate draft
  const { text: draft } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    prompt: `Write marketing copy for: ${topic}`,
  });

  // Step 2: Evaluate quality
  const { output: evaluation } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    output: Output.object({
      schema: z.object({
        score: z.number().min(1).max(10),
        issues: z.array(z.string()),
        passesQuality: z.boolean(),
      }),
    }),
    prompt: `Evaluate this copy (score 1-10):\n\n${draft}`,
  });

  // Step 3: Improve if needed
  if (!evaluation.passesQuality) {
    const { text: improved } = await generateText({
      model: anthropic("claude-sonnet-4-5"),
      prompt: `Improve this copy based on these issues: ${evaluation.issues.join(", ")}\n\nOriginal:\n${draft}`,
    });
    return improved;
  }

  return draft;
}
```

## 2. Parallel Pattern

Independent tasks run simultaneously for efficiency.

### Basic Example

```typescript
async function comprehensiveReview(code: string) {
  const [security, performance, style] = await Promise.all([
    generateText({
      model: anthropic("claude-sonnet-4-5"),
      prompt: `Review for security vulnerabilities:\n\n${code}`,
    }),
    generateText({
      model: anthropic("claude-sonnet-4-5"),
      prompt: `Review for performance issues:\n\n${code}`,
    }),
    generateText({
      model: anthropic("claude-sonnet-4-5"),
      prompt: `Review for code style and maintainability:\n\n${code}`,
    }),
  ]);

  return {
    security: security.text,
    performance: performance.text,
    style: style.text,
  };
}
```

### With Structured Output

```typescript
async function multiDimensionalAnalysis(document: string) {
  const analysisSchema = z.object({
    score: z.number().min(0).max(100),
    findings: z.array(z.string()),
    recommendations: z.array(z.string()),
  });

  const [sentiment, accuracy, clarity] = await Promise.all([
    generateText({
      model: anthropic("claude-sonnet-4-5"),
      output: Output.object({ schema: analysisSchema }),
      prompt: `Analyze sentiment of:\n\n${document}`,
    }),
    generateText({
      model: anthropic("claude-sonnet-4-5"),
      output: Output.object({ schema: analysisSchema }),
      prompt: `Check factual accuracy of:\n\n${document}`,
    }),
    generateText({
      model: anthropic("claude-sonnet-4-5"),
      output: Output.object({ schema: analysisSchema }),
      prompt: `Evaluate clarity of:\n\n${document}`,
    }),
  ]);

  return {
    sentiment: sentiment.output,
    accuracy: accuracy.output,
    clarity: clarity.output,
    overallScore:
      (sentiment.output.score + accuracy.output.score + clarity.output.score) /
      3,
  };
}
```

## 3. Routing Pattern

Direct queries to appropriate handlers based on classification.

### Basic Example

```typescript
async function routeCustomerQuery(query: string) {
  // Classify the query
  const { output: category } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    output: Output.choice({
      choices: ["technical", "billing", "sales", "general"] as const,
    }),
    prompt: `Classify this customer query: "${query}"`,
  });

  // Route to appropriate handler
  switch (category) {
    case "technical":
      return handleTechnicalQuery(query);
    case "billing":
      return handleBillingQuery(query);
    case "sales":
      return handleSalesQuery(query);
    case "general":
      return handleGeneralQuery(query);
  }
}

async function handleTechnicalQuery(query: string) {
  return generateText({
    model: anthropic("claude-sonnet-4-5"),
    system:
      "You are a technical support specialist. Provide detailed technical solutions.",
    prompt: query,
  });
}

async function handleBillingQuery(query: string) {
  return generateText({
    model: anthropic("claude-sonnet-4-5"),
    system:
      "You are a billing specialist. Help with payment and subscription issues.",
    prompt: query,
  });
}
```

### Multi-Level Routing

```typescript
async function intelligentRouter(query: string) {
  // Level 1: Primary classification
  const { output: primaryCategory } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    output: Output.object({
      schema: z.object({
        category: z.enum(["product", "support", "account"]),
        urgency: z.enum(["low", "medium", "high", "critical"]),
        sentiment: z.enum(["positive", "neutral", "negative"]),
      }),
    }),
    prompt: `Classify: "${query}"`,
  });

  // Level 2: Sub-category routing
  if (primaryCategory.category === "support") {
    const { output: supportType } = await generateText({
      model: anthropic("claude-sonnet-4-5"),
      output: Output.choice({
        choices: ["bug", "howto", "feature_request", "integration"] as const,
      }),
      prompt: `What type of support issue is this: "${query}"`,
    });

    return handleSupportQuery(query, supportType, primaryCategory.urgency);
  }

  // Handle other categories...
}
```

## 4. Orchestrator-Worker Pattern

A central orchestrator coordinates specialized workers.

### Basic Example

```typescript
async function orchestratedFeatureImplementation(requirement: string) {
  // Orchestrator: Plan the work
  const { output: plan } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    output: Output.object({
      schema: z.object({
        tasks: z.array(
          z.object({
            id: z.string(),
            type: z.enum(["frontend", "backend", "database", "testing"]),
            description: z.string(),
            dependencies: z.array(z.string()),
          })
        ),
      }),
    }),
    prompt: `Break down this feature into implementation tasks: ${requirement}`,
  });

  // Identify tasks with no dependencies (can run in parallel)
  const independentTasks = plan.tasks.filter(
    (t) => t.dependencies.length === 0
  );
  const dependentTasks = plan.tasks.filter((t) => t.dependencies.length > 0);

  // Execute independent tasks in parallel
  const initialResults = await Promise.all(
    independentTasks.map((task) => executeWorkerTask(task))
  );

  // Execute dependent tasks sequentially
  const allResults = [...initialResults];
  for (const task of dependentTasks) {
    const result = await executeWorkerTask(task);
    allResults.push(result);
  }

  // Orchestrator: Combine results
  const { text: finalOutput } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    prompt: `Combine these implementation results into a coherent feature:\n\n${allResults
      .map((r) => `[${r.type}]: ${r.output}`)
      .join("\n\n")}`,
  });

  return finalOutput;
}

async function executeWorkerTask(task: { type: string; description: string }) {
  const systemPrompts: Record<string, string> = {
    frontend: "You are a frontend developer. Write React/TypeScript code.",
    backend: "You are a backend developer. Write Node.js/TypeScript code.",
    database: "You are a database engineer. Write SQL and schema definitions.",
    testing: "You are a QA engineer. Write test cases and test code.",
  };

  const { text } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    system: systemPrompts[task.type] || "You are a software developer.",
    prompt: task.description,
  });

  return { type: task.type, output: text };
}
```

### With Agent Delegation

```typescript
import { ToolLoopAgent, tool } from "ai";

const orchestratorAgent = new ToolLoopAgent({
  model: anthropic("claude-sonnet-4-5"),
  instructions: "You coordinate specialized agents to complete complex tasks.",
  tools: {
    delegateToResearcher: tool({
      description: "Delegate research tasks",
      inputSchema: z.object({ topic: z.string() }),
      execute: async ({ topic }) => {
        const { text } = await researchAgent.generate({ prompt: topic });
        return text;
      },
    }),
    delegateToWriter: tool({
      description: "Delegate writing tasks",
      inputSchema: z.object({ content: z.string(), style: z.string() }),
      execute: async ({ content, style }) => {
        const { text } = await writerAgent.generate({
          prompt: `Write in ${style} style: ${content}`,
        });
        return text;
      },
    }),
    delegateToReviewer: tool({
      description: "Delegate review tasks",
      inputSchema: z.object({ document: z.string() }),
      execute: async ({ document }) => {
        const { text } = await reviewerAgent.generate({ prompt: document });
        return text;
      },
    }),
  },
});
```

## 5. Evaluator-Optimizer Pattern

Iterate until output meets quality threshold.

### Basic Example

```typescript
async function optimizeContent(
  input: string,
  targetScore: number = 8,
  maxIterations: number = 3
) {
  let content = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    prompt: input,
  });

  for (let iteration = 0; iteration < maxIterations; iteration++) {
    // Evaluate
    const { output: evaluation } = await generateText({
      model: anthropic("claude-sonnet-4-5"),
      output: Output.object({
        schema: z.object({
          score: z.number().min(1).max(10),
          strengths: z.array(z.string()),
          weaknesses: z.array(z.string()),
          suggestions: z.array(z.string()),
        }),
      }),
      prompt: `Evaluate this content (1-10):\n\n${content.text}`,
    });

    console.log(`Iteration ${iteration + 1}: Score ${evaluation.score}/10`);

    // Check if target reached
    if (evaluation.score >= targetScore) {
      return {
        content: content.text,
        finalScore: evaluation.score,
        iterations: iteration + 1,
      };
    }

    // Optimize based on feedback
    content = await generateText({
      model: anthropic("claude-sonnet-4-5"),
      prompt: `Improve this content based on feedback:

Current content:
${content.text}

Weaknesses:
${evaluation.weaknesses.join("\n")}

Suggestions:
${evaluation.suggestions.join("\n")}

Create an improved version:`,
    });
  }

  // Return best effort after max iterations
  return {
    content: content.text,
    finalScore: null,
    iterations: maxIterations,
  };
}
```

### With Different Evaluators

```typescript
async function multiCriteriaOptimization(input: string) {
  let content = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    prompt: input,
  });

  const criteriaThresholds = {
    clarity: 8,
    accuracy: 9,
    engagement: 7,
  };

  for (let i = 0; i < 5; i++) {
    // Evaluate against all criteria in parallel
    const [clarity, accuracy, engagement] = await Promise.all([
      evaluateCriterion(content.text, "clarity"),
      evaluateCriterion(content.text, "accuracy"),
      evaluateCriterion(content.text, "engagement"),
    ]);

    // Check if all criteria met
    const allMet =
      clarity.score >= criteriaThresholds.clarity &&
      accuracy.score >= criteriaThresholds.accuracy &&
      engagement.score >= criteriaThresholds.engagement;

    if (allMet) {
      return {
        content: content.text,
        scores: { clarity, accuracy, engagement },
      };
    }

    // Identify weakest criterion
    const scores = { clarity, accuracy, engagement };
    const weakest = Object.entries(scores).sort(
      (a, b) => a[1].score - b[1].score
    )[0];

    // Focus improvement on weakest area
    content = await generateText({
      model: anthropic("claude-sonnet-4-5"),
      prompt: `Improve the ${weakest[0]} of this content (current score: ${weakest[1].score}/10):

${content.text}

Feedback: ${weakest[1].feedback}`,
    });
  }

  return { content: content.text, scores: null };
}

async function evaluateCriterion(text: string, criterion: string) {
  const { output } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    output: Output.object({
      schema: z.object({
        score: z.number().min(1).max(10),
        feedback: z.string(),
      }),
    }),
    prompt: `Evaluate the ${criterion} of this text (1-10):\n\n${text}`,
  });

  return output;
}
```

## Combining Patterns

### Parallel + Sequential

```typescript
async function hybridWorkflow(documents: string[]) {
  // Parallel: Process all documents
  const analyses = await Promise.all(
    documents.map((doc) =>
      generateText({
        model: anthropic("claude-sonnet-4-5"),
        prompt: `Analyze: ${doc}`,
      })
    )
  );

  // Sequential: Synthesize results
  const { text: synthesis } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    prompt: `Synthesize these analyses:\n\n${analyses.map((a) => a.text).join("\n\n---\n\n")}`,
  });

  return synthesis;
}
```

### Routing + Orchestrator

```typescript
async function smartWorkflowRouter(task: string) {
  // Route to appropriate workflow
  const { output: workflowType } = await generateText({
    model: anthropic("claude-sonnet-4-5"),
    output: Output.choice({
      choices: ["simple", "complex", "iterative"] as const,
    }),
    prompt: `What type of workflow is needed for: "${task}"`,
  });

  switch (workflowType) {
    case "simple":
      return simpleSequentialWorkflow(task);
    case "complex":
      return orchestratorWorkerWorkflow(task);
    case "iterative":
      return evaluatorOptimizerWorkflow(task);
  }
}
```

## Decision Framework

Choose your pattern based on:

| Factor          | Sequential | Parallel | Routing | Orchestrator | Evaluator |
| --------------- | ---------- | -------- | ------- | ------------ | --------- |
| Step dependency | High       | None     | Varies  | Low          | High      |
| Task complexity | Low-Med    | Low      | Low     | High         | Medium    |
| Quality control | Basic      | Basic    | Basic   | Medium       | High      |
| Latency         | Higher     | Lower    | Medium  | Medium       | Higher    |
| Cost            | Medium     | Higher   | Lower   | Higher       | Highest   |

## Best Practices

1. **Start simple** - Use sequential for prototypes, optimize later
2. **Parallelize when possible** - Independent tasks should run concurrently
3. **Use routing for diverse inputs** - Better than one-size-fits-all
4. **Orchestrate complex tasks** - Break into specialized sub-tasks
5. **Iterate for quality** - When output quality is critical
6. **Set iteration limits** - Prevent infinite loops in evaluator pattern
7. **Monitor costs** - Complex workflows can be expensive
8. **Log intermediate steps** - For debugging and optimization
