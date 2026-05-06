---
title: "Pydantic Monty: The LLM is powerful now, get the harness out of the way!"
date: 2026-05-05
categories: [AI, Agents]
tags: [pydantic, monty, code-mode, tool-calling, sandboxing, agents]
description: "Let LLMs write Python that orchestrates parallel tool calls in a single invocation — Pydantic Monty is the sandboxed interpreter that makes it safe and fast."
image: /assets/images/pydantic-monty/monty.jpg
---

I was at AgentCon Silicon Valley today and aside from it being hosted in the famous Computer History Museum (a place I have always wanted to visit!), I also caught a presentation by Pydantic creator Samuel Colvin. Samuel was presenting on Monty, a minimal and secure Python interpreter written in Rust for agentic workloads. So afterwards I found a quiet spot and had a play.

The idea behind Monty Python (it's pining for the fjords) is another step in the direction of giving LLMs the ability to flex their capability and not restrict them through the harness. If you've built agents with tool_use, you know the loop. The model picks a tool, calls it, reads the result, picks the next tool, calls it, reads the result. Each cycle is a full model invocation. Ask it to check the weather in five cities and, even with parallel tool calling, you still have the model/tool/model loop: the tool results have to come back into model context, and dependent chains still require another model turn before the next step can happen. With MCP, those tool schemas and responses get large fast. A task that should feel instant starts to drag. We do this because it's how tool_use was designed, back when models were a little simpler, or less capable. And a task that should take two seconds takes twenty.

The alternative is to let modern and capable models write code that calls all the tools it needs in one go. One model invocation produces a Python script. That script fires off five weather lookups in parallel with `asyncio.gather()`. The results come back, the script processes them, done. One round-trip instead of five. Or ten. Or twenty.

You don't want to just execute LLM-generated Python on your infrastructure though. That's what Monty is for.

## What the model actually writes

In a traditional agent loop, the model returns structured tool_use blocks, one per turn, one tool at a time. But if you let the model write Python instead, it returns something like this:

```python
paris, tokyo = await asyncio.gather(
    get_weather(city='Paris'),
    get_weather(city='Tokyo'),
)
paris_c = await convert_temp(fahrenheit=paris['temp_f'])
tokyo_c = await convert_temp(fahrenheit=tokyo['temp_f'])
{'paris': paris_c, 'tokyo': tokyo_c}
```

That's four tool calls orchestrated in a single invocation. The model worked out the dependency graph on its own, parallelised what it could, and sequenced what it had to. You didn't tell it to do that. It just figured out the efficient path because that's what capable models do when you give them room.

The pattern is called "code mode" and it's shipping in multiple places already. Pydantic AI has `CodeMode`, Cloudflare built it for MCP servers, and Anthropic calls it "Programmatic Tool Calling" in their advanced tool use platform. In his talk, Samuel mentioned seeing tasks taking far less time and tokens. MCP responses are enormous, and each round-trip means loading all those tokens into context just to extract an ID for the next request. Let the model write code and a lot of that overhead disappears.

## The sandbox problem

Of course you need somewhere safe to run it.

One option is a managed runtime environment. Amazon Bedrock AgentCore has a Code Interpreter tool that lets agents write, execute, and debug code securely in an isolated, containerized sandbox environment. It supports multiple languages, pre-built runtimes, large files, session storage, and configurable networking. If you're running in AgentCore Runtime/Harness, your application can also use `InvokeAgentRuntimeCommand` to run deterministic shell commands inside the same running session and filesystem at zero token cost, without routing that work through the model.

Those environments are powerful, but that's also the trade-off. They're designed for general-purpose code execution: data analysis, filesystem work, debugging, tests, dependency setup, and longer-running computation. For simple tool orchestration, that may be more environment than you need, and more surface area than you want.

Monty takes a completely different approach. It's a Python interpreter written from scratch in Rust. Not a CPython fork, not Python compiled to WASM, but a new bytecode VM that understands Python syntax and enforces a strict subset of the language. It starts in microseconds. By default there's no filesystem access, no network, no environment variables. You can opt in to an in-memory virtual filesystem or even mount real host directories if you need to, but out of the box the interpreter simply doesn't have those capabilities. The model gets exactly the power it needs for orchestration and nothing more.

## External functions are the entire API surface

The only way Monty code can reach the outside world is through external functions you explicitly inject at runtime:

```python
import pydantic_monty

code = """
paris, tokyo = await asyncio.gather(
    get_weather(city='Paris'),
    get_weather(city='Tokyo'),
)
{'paris': paris['temp'], 'tokyo': tokyo['temp']}
"""

m = pydantic_monty.Monty(code, inputs=[])

result = await pydantic_monty.run_monty_async(
    m,
    inputs={},
    external_functions={
        'get_weather': get_weather_impl
    }
)
```

The model wrote code that calls `get_weather`, and Monty runs it. When execution hits that function call, it pauses. Control returns to your application, you perform the real API call however you want, and hand the result back. The sandboxed code never touches your network, your secrets, or your filesystem. It just orchestrates.

It's not a security layer bolted onto Python. It's a purpose-built environment that lets the model coordinate complex workflows freely, while physically preventing it from reaching anything you haven't handed to it. Maximum flexibility for the model, maximum control for you.

## What you gain and what you lose

Monty supports the subset of Python that LLMs actually use when orchestrating tools. Functions, async/await, loops, conditionals, comprehensions, f-strings, data structures. It deliberately excludes things LLMs don't need for this job. No class definitions yet, no match statements yet, limited standard library, and no third-party imports.

As Samuel put it in his talk, "We are not trying to build another Python interpreter that you might credibly move your application across. We're using Python as a syntax for a very specific thing where LLMs write code."

The constraints mean the sandbox surface area is tiny. The Pydantic team ran a public bounty, offering $5,000 to anyone who could escape the sandbox and read a file or environment-variable secret from the host. According to Samuel's talk, vulnerabilities were found and patched — which is exactly how a bounty is supposed to work.

## How the options compare

Per Pydantic's own benchmarks:

| Approach | Start latency | Security | Python support |
|----------|--------------|----------|----------------|
| Monty | ~0.004ms | Strict (deny-by-default) | Python subset |
| Docker | ~195ms | Good (container isolation) | Full |
| Pyodide (WASM) | ~2800ms | Depends on embedding | Full |
| WASI/Wasmer | ~66ms | Strict (capability-based) | Almost full |
| No sandbox | ~0.1ms | None | Full |

At microsecond-level startup, Monty adds negligible overhead to your tool-calling latency. You're not paying for container orchestration at agent-call frequency. The sandbox is effectively free.

## Two layers of isolation

So I tried running this combination on AgentCore. The Harness gives me an isolated runtime environment with Code Interpreter and shell access when I need it. But for tool orchestration specifically, I run Monty inside that same environment. The runtime isolation keeps sessions apart. Monty keeps LLM-generated orchestration code away from the session's own resources. The model can write arbitrarily complex coordination logic, but that logic can only call the functions I've explicitly made available.

Belt and braces. The runtime handles infrastructure isolation, Monty handles code-level sandboxing. They complement each other nicely.

## What this changes about agent design

The sequential tool-calling loop isn't just slow, it warps how you design agents. You end up building mega-tools that do too much in a single call because each round-trip is expensive. Or you accept the latency and let simple tasks take thirty seconds. Either way, you're working around the model's constraints instead of letting it work for you.

Code mode removes that. Your tools can be small and composable because the model can call twenty of them in a single invocation without twenty round-trips. You define what's callable and the model figures out the rest.

It's early. Monty is at v0.0.17, still labelled experimental, and the Python subset is deliberately limited. But the pattern (LLM writes code, sandbox executes it, external functions are the only escape hatch) is showing up everywhere. Pydantic, Cloudflare, Anthropic, and others are all arriving at the same architecture because sequential tool calling at scale simply doesn't work economically.

Models are capable enough to orchestrate their own workflows now. We just needed a safe way to let them. Monty is that.

If you're building agents and want to compare notes on code mode patterns, connect with me on [LinkedIn](https://www.linkedin.com/in/mikegchambers).
