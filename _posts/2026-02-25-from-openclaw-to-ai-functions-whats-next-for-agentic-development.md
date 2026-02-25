---
title: "Podcast: From OpenClaw to AI Functions — What's Next for Agentic Development"
date: 2026-02-25
categories: [AI, Agents]
tags: [podcast, agents, strands, ai-functions, openclaw, async, video]
description: "I joined Romain Jourdan on the AWS Developers Podcast to discuss OpenClaw, async agentic tools, Strands Labs, AI Functions, and the future of software development."
---

{% include embed/youtube.html id='oWWHwquGuVE' %}

I was back on the AWS Developers Podcast with Romain Jourdan, and this time we went deep. Almost 80 minutes of conversation covering some of the topics I've been most excited about recently: OpenClaw, asynchronous tool calling, Strands Labs, AI Functions, and where all of this might be heading.

Here's a summary of what we covered.

## Why OpenClaw Happened Now

We kicked off with OpenClaw and rather than just talking about what it is, we dug into *why* it happened when it did. My take: developers had already been building personal agents throughout 2025 -- ordering pizzas, making personal assistants, messing around with wearable devices -- but they were all stuck in the terminal. OpenClaw essentially provided the missing piece: a UI layer that connected those experiments to real communication channels like WhatsApp, iMessage, and email. All of a sudden, that agent you built is in your pocket and actually doing something practical. That's why it blew up.

## Async Agentic Tools: It Finally Works

I've [written about this already](https://blog.mikegchambers.com/posts/async-agentic-tools/), but the podcast was a chance to tell the full story. Mid-2025, a colleague and I tried to build true asynchronous tool calling -- where a model dispatches a tool, gets an acknowledgement, and moves on while the tool runs in the background. It didn't work. The models would hallucinate results instead of waiting, or lose track of task IDs across turns.

Digging through OpenClaw's code led me to [Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md), the underlying framework it uses, which has interrupt semantics for handling sub-agent responses. That inspired me to revisit the problem using Strands Agents. With current-generation models (notably Claude Opus 4.6), the pattern now works reliably. The model waits for results, doesn't fabricate data, and handles out-of-order responses across turns.

The practical upshot: you can have a natural conversation with an agent while long-running tasks complete in the background. Research something, ask follow-up questions about something else, get results as they arrive. It works especially well for voice interfaces where dead air kills the experience.

## Strands Labs and AI Functions

We then talked about [Strands Labs](https://github.com/strands-labs), a new GitHub organization from the Strands team for experimental projects. The standout for me is [AI Functions](https://github.com/strands-labs/ai-functions).

The concept: write a Python function with a name, typed inputs, a Pydantic output model, and instead of code in the body, you write a natural language docstring describing what the function should do. At runtime, a Strands agent generates and executes the code to fulfill that description, validating against output conditions you define.

What makes this more than a toy: the return value is a native Python object -- a Pandas DataFrame, a database connection, structured data -- not a JSON blob from an API call. And you can specify post-conditions that the generated code must satisfy, with retry logic if they're not met.

I explored this more in my post [Software 3.1? - AI Functions](https://blog.mikegchambers.com/posts/software-31-ai-functions/), riffing on Karpathy's Software 1.0/2.0/3.0 framework. The question I keep coming back to: as models get more reliable at code generation, at what point does writing instructions become more productive than writing code?

## The Model as Execution Environment

We went a bit philosophical toward the end. I've been experimenting with agents that act as web servers -- you type a description of software you want, and a fully functional web application appears (an English-to-German translator, for example), all running through the model with no traditional application code behind it. The compute *is* the LLM.

This connects back to an idea from around 2018: what if the execution environment of the future is a model? With current frontier models, that's starting to feel less speculative than it once did.

## What's Next: Agent Trust and Observability

I ended with what I'll be focusing on next: agent trust. I think the reason we haven't seen agents widely deployed in line-of-business applications is that we don't trust them enough yet -- and that's also why so many people are running local models for their experimental agents.

The path forward is observability and evaluation: OpenTelemetry instrumentation for agents, dashboards, alerts on token usage and accuracy drift. I'll admit, last year I thought this was the boring part. Now I think it's the most important part if we want to move agents from experiments to production.

## Links & Resources

- [Async Agentic Tools -- blog post](https://blog.mikegchambers.com/posts/async-agentic-tools/)
- [Software 3.1 & AI Functions -- blog post](https://blog.mikegchambers.com/posts/software-31-ai-functions/)
- [Strands Labs GitHub](https://github.com/strands-labs)
- [AI Functions repo](https://github.com/strands-labs/ai-functions)
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [Morgan Willis -- Deploying Secure, Production-Ready Agents](https://youtu.be/jI4AYvvA7ck?si=2RtoDkwiHIaUN4AJ)
