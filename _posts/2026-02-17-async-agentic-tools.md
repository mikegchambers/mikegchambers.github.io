---
title: "Async Agentic Tools: Breaking Free from the Request-Response Loop"
date: 2026-02-17
categories: [AI, Agents]
tags: [agents, async, tools, amazon-bedrock, strands, python]
description: "Every agent framework blocks while tools run. This post walks through an experimental approach to true async agentic tools — where the model stays responsive while tools complete in the background."
---

Every AI agent framework today follows the same basic loop: the model thinks, it calls some tools, it waits for all the tools to finish, and then it thinks again. On one hand that loop works fine when your tools return in seconds or when your agent is headless, but on the other it causes millions of people every day to stare blankly for hours (in total) at a "thinking" message. Where's the productivity gain in that? :)

**Skip to the code: [here](#how-it-works-the-code).**

[![Watch the video](https://img.youtube.com/vi/VYLBCoxbPE8/maxresdefault.jpg)](https://youtu.be/VYLBCoxbPE8)

If you've used (or built) agents that call APIs with variable latency, run database queries, kick off web searches, or - of course - used agents as tools, you've felt this. The model sits idle, the user sits idle, and a 30-second tool call holds up the response to a 3-second one that could have finished ages ago. The agent can't talk to the user, can't start processing partial results, can't do anything.

Modern frontier models now have the ability to start experimenting with genuine asynchronous tool calls. This post walks through my experimental approach: true asynchronous agentic tools. The demo is built on the [Strands Agents SDK](https://github.com/strands-agents/sdk-python), but the pattern should apply to any agent framework with a tool-calling loop. The code is open, the approach is simple, and it requires zero changes to how you write your tools.

## Async vs Async

First, before you write your comment on this post... let's be precise about terminology.

Many agent frameworks already support parallel tool calling — when a model returns multiple tool calls in a single response, the framework can execute them concurrently. Strands Agents, which I'm using for this demo, [supports this natively](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/executors/). That's good. But the agent loop is still blocked until every tool in that batch has responded. If you dispatch three tools and two finish in 1 second but one takes 45 seconds, the model cannot respond, cannot think, and cannot act for those 44 seconds of dead air. It's the same as `Promise.all()` or `asyncio.gather()` — you get concurrency in the execution, but you still wait for the slowest one before anything else can happen.

True async agentic tool calling is different. The model dispatches a tool, gets back an acknowledgement immediately ("task started, here's an ID"), and moves on. It can talk to the user, call other tools, or just wait. When the result arrives — seconds, minutes, hours or days later — it gets delivered to the model as a new message, and the model processes it then. The model stays responsive. Results stream in as they complete. The user experience is fundamentally different. And I have to say, I like it!

## Why This Wasn't Possible Until Recently

This architecture puts real demands on a model's intelligence, its context size, and its propensity for 'lost in the middle' issues. It needs to understand that a tool call won't return a real result. It needs to avoid fabricating data while waiting. It needs to handle results arriving out-of-order, potentially many turns after the original request. And it needs to keep track of multiple pending tasks across a growing conversation context.

One solution to this could be to provide the agent with even more tools to manage its own execution flow. But this just makes the flow even more complex for the poor model. 

The (current) solution is much simpler, ironicaly we just needed to wait for the frontier models to get good enough. The problem you couldn't solve 6 months ago, now works just like you through it would, now that Opus 4.6 is here. (Is there a name for this progression? Like Moores Law just for LLM improvment? Please let me know.)

As recently as mid-2025, asynchronous tool calling didn't work reliably. Models would hallucinate results instead of waiting, lose track of pending task IDs, or get confused when results arrived in a later turn. The instruction-following just wasn't precise enough.

Newer, more capable models handle kinda okay. They follow the "do not fabricate" instruction in the tool description, they correctly associate arriving results with their task IDs, and they maintain coherent multi-turn conversations while tasks are in flight. This is one of those capabilities that seems to have emerged from generally smarter models rather than from any async-specific training. Is it perfect, no, but no agwet is perfect, and I am sure it will improve.

## How It Works (The Code)

My implementation is three small components — about 320 lines of code total — that layer on top of a standard Strands Agent without modifying it. The code is linked here: [repo](https://github.com/mikegc-aws/async-agentic-tools)

### 1. The Decorator: `@tool_async`

You write your tool exactly the way you'd write any tool function. A function with a docstring and type hints. Then you wrap it with `@tool_async(manager)`:

```python
from strands_async_tools import AsyncToolManager, tool_async

manager = AsyncToolManager(max_workers=4)

@tool_async(manager)
def research_topic(topic: str) -> str:
    """Research a topic thoroughly and return detailed findings."""
    time.sleep(15)  # simulate slow API call
    return f"Findings about {topic}..."
```

So that's it for the tool, your function doesn't change. It's still synchronous. It still returns a string. The decorator handles everything for you.

What it does behind the scenes:

1. When the model calls `research_topic`, the decorator submits the original function to a `ThreadPoolExecutor` for background execution.
2. It immediately returns a structured message to the model: task ID, tool name, arguments, and a clear instruction not to fabricate the result.
3. It appends an async notice to the tool's docstring so the model knows, from the schema alone, that this tool is asynchronous, and how to expect it to work.

The model sees the immediate response and might tell the user "I've started the research." Meanwhile, the real function is running on a background thread.

### 2. The Manager: `AsyncToolManager`

The manager is a thin wrapper around Python's `ThreadPoolExecutor` that adds task tracking and completion callbacks:

```python
class AsyncToolManager:
    def submit(self, tool_name, fn, **kwargs) -> str:
        """Submit a function for background execution. Returns a task ID."""
        task_id = uuid.uuid4().hex[:8]
        future = self._executor.submit(run)
        future.add_done_callback(on_done)
        return task_id
```

When a background task finishes, the manager fires an `on_complete` callback with an `AsyncTaskResult` containing the task ID, tool name, arguments, result (or error), and elapsed time. The manager doesn't know or care what happens next — it just reports completion.

### 3. The Agent Wrapper: `AsyncAgent`

This is the orchestration layer. `AsyncAgent` wraps a standard `Agent` and manages the lifecycle of delivering async results back to the model:

```python
agent = Agent(
    model=model_id,
    system_prompt=SYSTEM_PROMPT,
    tools=[research_topic, analyze_sentiment, fetch_weather, calculator],
)
async_agent = AsyncAgent(agent=agent, manager=manager)
async_agent.send("Research quantum computing and check the weather in Paris")
```

I wrap the agent like this rather than subclass it as the agent is a complex thing, and this method should more easliy extend to other frameworks. AsyncAgent doesn't change how the Agent works — it just manages when and how it gets invoked.

`AsyncAgent` registers itself as the manager's completion callback and maintains a simple state machine:

- **Agent is idle, result arrives**: Invoke the agent immediately with the formatted result. The model processes it and responds.
- **Agent is busy (already processing something), result arrives**: Queue the result. When the current invocation finishes, drain the queue — deliver each queued result to the agent one at a time.
- **Multiple results arrive while busy**: They all queue up and get delivered sequentially in a draining phase after the agent finishes.

(I have OpenClaw to thank for this - sorta. As I was digging through it's code, I then fell in to looking at [Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md) interrupt semantics that does something simialr.)

The result is delivered to the model as a plain text message:

```
[ASYNC RESULT]
Task ID: abc123
Tool: research_topic(topic='quantum computing')
Result:
Key finding: quantum computing has seen 340% growth in the last 2 years.
Experts predict the quantum computing market will reach $50B by 2028.
Elapsed: 15234ms
```

The model treats this like any other user message and responds naturally.

Thread safety matters here. The completion callback fires from the thread pool, but agent invocations must be serialized (you can't call a Strands Agent from two threads simultaneously). `AsyncAgent` uses a lock to protect its busy flag and result queue, ensuring that results are always delivered one at a time in a safe order.

## The Demo

In the repo `demo.py` is my minimal CLI that shows the whole thing working end-to-end with mock tools (with made up data!) that wait for random times. It should look something like this:

```
$ uv run python demo.py

You: Research quantum computing and check the weather in London

  [thinking] processing...
I've started both tasks for you:
1. Researching quantum computing (Task abc123)
2. Fetching weather for London (Task def456)

Results will come in as they complete.

  [callback] fetch_weather (def456) completed in 11234ms — delivering to agent now
  [thinking] processing...
The weather in London just came in: partly cloudy, 18C, humidity at 65%.

Still waiting on the research results.

  [callback] research_topic (abc123) completed in 17891ms — delivering to agent now
  [thinking] processing...
The research on quantum computing is done. Here are the key findings:
- 340% growth in the last 2 years
- Major players include Acme Corp, Nexus Labs, and Orion Systems
- Market predicted to reach $50B by 2028

You:
```

There's three async tools (with simulated 10-20 second delays) and two synchronous tools (calculator and current_time) running side by side. The sync tools return instantly as usual. The async tools dispatch to background threads and deliver results via callbacks. The model stays conversational throughout.

Try this: 

```
You: Research Paris

  [thinking] processing...
I've started researching Paris for you (Task a1b2c3).
I'll let you know as soon as the results come in.

You: What time is it there?

  [thinking] processing...
It's currently 15:32 in Paris (CET, UTC+1).

  [callback] research_topic (a1b2c3) completed in 16482ms — delivering to agent now
  [thinking] processing...
The Paris research just came back! Here are some highlights:
- ...
```

## What the System Prompt Does

In the demo script the system prompt is explicit about the contract. Over time I would like to simplify this or remove it all together, and I suspect that will happen:

```
When you call an async tool it returns a task ID immediately.
The actual result will arrive in a future message tagged [ASYNC RESULT].
Rules:
  - Do NOT guess or fabricate async results. Wait for [ASYNC RESULT].
  - Tell the user each task has been started.
  - You CAN dispatch multiple async tools at once — they run in parallel.
```

The system prompt, combined with the async notice appended to each tool's docstring by the decorator, gives the model enough context to behave correctly. It's prompt engineering, not framework magic — and it works because current models are good enough at following these instructions reliably.

## When to Use This (and Probably When Not To)

Let's be honest: **this is an experiment.** It's not for everyone, and it's not for every situation.

It works well when (in no particular order):

- **Tools have high, variable latency** — web searches, API calls, document processing, anything where one tool might take 2 seconds and another might take 30.
- **You want the agent to stay conversational** — the user shouldn't have to stare at a spinner while a slow tool runs.
- **You're building voice interfaces** — This is a huge one! Dead air is death for voice UX. Async tools work especially well for voice agents: the agent can keep talking and answering follow-up questions while sub-tasks run in the background. This demo actually includes experimental (scrappy) code for testing this with [Amazon Nova Sonic 2](https://github.com/mikegc-aws/async-agentic-tools/tree/main/voice) as a voice chat — worth a look if you want to try async tools in a real voice flow. (See the readme for the details of how to run the voice code.)
- **Tasks are independent** — async shines when tool calls don't have a hard dependancy on each other's results, and the agent can stil combine the data when multiple tools return.
- **Tools are themselves agents (or sub-agents)** — Another big one! Agent-as-tool is one of the main candidates for long-running processes; those tools often take seconds or minutes and benefit from the model staying responsive while they run.

## Try It

The code is in the [async-agentic-tools](https://github.com/mikegc-aws/async-agentic-tools) repository. The demo uses [Strands Agents](https://github.com/strands-agents/sdk-python) with Claude Sonnet on Amazon Bedrock. You'll need AWS credentials for Bedrock and Python 3.14+.

```bash
git clone https://github.com/mikegc-aws/async-agentic-tools
cd async-agentic-tools
uv run python demo.py
```

The three files that matter are in `strands_async_tools/`: `manager.py` (87 lines), `decorator.py` (68 lines), and `agent.py` (166 lines). The whole thing is about 320 lines of Python. Read it, fork it, break it. If this approach is useful to you, consider giving the [repo](https://github.com/mikegc-aws/async-agentic-tools) a star — it helps others find it and makes everyone smile.

This is my experiment in what becomes possible when models get smart enough to handle architectural patterns that would have confused them a year ago. The request-response loop served us well. But tools are getting slower and more powerful, conversations are getting longer and more complex, and users shouldn't have to wait in silence while the interesting work happens in the background.
