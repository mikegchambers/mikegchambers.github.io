---
title: "Podcast: From MCP to Multi-Agents — The Evolution of Agentic AI (and What's Next)"
date: 2026-02-11
categories: [AI, Agents]
tags: [podcast, agents, mcp, strands, kiro, frameworks, security, video]
description: "I joined Romain Jourdan on the AWS Developers Podcast to discuss MCP's rocky launch, agent security, context overloading, the rise of lightweight frameworks, AI coding assistants, and where agentic AI is heading next."
---

{% include embed/youtube.html id='G4FDZlcfCBk' %}

I joined Romain Jourdan on the AWS Developers Podcast for a wide-ranging conversation about the state of agentic AI. Just over an hour covering what actually happened in 2025 -- I'd predicted it would be "the year of agents," and it was, just not in the way anyone expected. We talked through MCP's rocky launch and surprising pivot, the security realities of giving agents access to your machine, why context overloading is the silent killer in production, the framework evolution that led me to Strands, and why AI coding assistants turned out to be the real agent success story.

Here's a summary of what we covered.

## 2025: The Year of Agents (Sort Of)

I'd been saying for a while that 2025 would be the year of agents. And in a sense it was -- but not in the way I imagined. I was expecting agents embedded in production business applications, handling workflows end to end. What actually happened was more sideways: the biggest agent success story turned out to be AI coding assistants. Tools like [Kiro](https://kiro.dev) and Claude Code didn't just write code -- they expanded into broader development workflows, planning, debugging, deploying. That's where agents actually landed in people's daily work.

The lesson I took from this: agents found traction where the human-in-the-loop was already sitting at a keyboard. The feedback cycle was tight, trust was easier to build incrementally, and the cost of mistakes was low. Production business agents, with their longer feedback loops and higher stakes, are still coming -- but they needed more infrastructure than we had.

## MCP: From Rocky Launch to IDE Plugin Ecosystem

We spent a good chunk of time on the [Model Context Protocol](https://modelcontextprotocol.io/). MCP had a rough start. The original standard IO transport was limiting, there were interoperability issues between implementations, and the developer experience was inconsistent. I'd [written about using MCP with Amazon Bedrock](https://blog.mikegchambers.com/posts/will-anthropics-mcp-work-with-other-llms-yes-with-amazon-bed/) early on, and later about [running MCP over Streamable HTTP in Lambda](https://blog.mikegchambers.com/posts/mcp-can-lambda-do-it-streamable-http-model-context-protocol/), but the production story was still shaky.

What actually happened is that MCP found its niche as the plugin ecosystem for IDEs. Coding assistants needed a standard way to connect to external tools and data sources, and MCP fit that gap. It became less about agent-to-service communication in production and more about extending the capabilities of the development environment you're already working in. That wasn't the original vision, but it worked.

## Security: The Cost of Giving Agents Access

This was a topic I felt strongly about. As agents get more capable, the natural next step is giving them access to your filesystem and command line. That's where real productivity comes from -- but it's also where real risk lives. We talked through the threat model: an agent with shell access can read credentials, exfiltrate data, or modify files in ways that are hard to audit after the fact.

The uncomfortable truth is that most developers running agents locally aren't thinking about this. They're focused on what the agent can do, not what it *could* do. I think this is one of the reasons we haven't seen wider production deployment -- the security story for agents with broad system access is still immature. Sandboxing, permission models, audit logging -- all of this needs to be solved before enterprises are comfortable.

## Context Overloading: The Production Bottleneck

Context overloading came up as a practical challenge that doesn't get enough attention. When you give an agent access to dozens of tools, the tool definitions alone can consume a significant portion of the context window. Add in conversation history, retrieved documents, and multi-turn reasoning, and you're pushing limits fast.

The result is degraded performance: the model starts losing track of earlier instructions, tool selection becomes unreliable, and you get subtle failures that are hard to debug. In production, this is worse than a hard failure because the agent *appears* to be working but is making poor decisions. I've been thinking about this in terms of progressive disclosure -- not loading every tool definition upfront, but surfacing them based on what the agent actually needs at each step.

## The Framework Evolution: From Prompt Engineering to Model-Centric

We walked through the evolution of agent frameworks over the past couple of years. Early on, frameworks were heavy on prompt engineering -- elaborate system prompts, chain-of-thought templates, tool-use wrappers. They worked, but they were brittle and model-specific.

I'd been building my own framework for a while, but eventually abandoned it in favour of [Strands Agents](https://github.com/strands-agents/sdk-python). The reason: the newer generation of models (Claude, Nova) are good enough at tool use and reasoning that you don't need to engineer around their limitations as much. Strands takes a model-centric approach -- minimal prompting, let the model drive decisions, keep the framework lightweight. ADK, Spring AI, and others are moving in a similar direction. The trend is clear: less scaffolding, more trust in the model.

I've written more about this shift in my posts on [Strands Agents](https://blog.mikegchambers.com/posts/model-driven-agents-strands-agents-a-new-open-source-model-f/) and [building custom tools](https://blog.mikegchambers.com/posts/strands-tools-building-custom-ai-agents-with-python/).

## AI Coding Assistants: The Real Agent Success Story

This might have been the most interesting part of the conversation. If you'd asked me at the start of 2025 what the breakout agent application would be, I wouldn't have said "coding assistants." But that's what happened. [Kiro](https://kiro.dev), Claude Code, and similar tools went beyond autocomplete and code generation into genuine agentic behaviour -- planning multi-file changes, running tests, debugging failures, interacting with version control.

The reason this worked where other agent applications struggled: developers are already comfortable with tools that operate on their behalf, the environment is well-structured (files, tests, linters), and there's a fast feedback loop. You can see immediately if the agent did something wrong. That tight loop built trust in a way that longer-running business process agents haven't managed yet.

## Agent Skills and Progressive Disclosure

We touched on the distinction between agent skills and agent memory, and when to use each. Skills are about what an agent *can do* -- the tools and capabilities available to it. Memory is about what it *knows* -- context carried across sessions.

The progressive disclosure idea came up again here. Rather than giving an agent every possible skill from the start, you surface skills contextually based on the task at hand. This helps with context overloading (fewer tool definitions in the window), but it also helps with reliability -- the agent is less likely to pick the wrong tool when there are fewer to choose from. It's a design pattern I think we'll see more of as agent applications get more sophisticated.

## What's Next: Multi-Agent Systems and Production Scale

We ended by looking ahead. Long-running multi-agent systems are where I think things are going -- not just a single agent handling a task, but multiple agents coordinating across longer time horizons. The challenges here are real: state management, error recovery, cost control, and the coordination overhead of agents communicating with each other.

The bigger shift is moving from laptop-scale experiments to production-scale deployment. Most agent development today happens on someone's local machine. Getting that to production means solving for reliability, observability, cost management, and trust. It's less about the models getting better (they're already good enough for many tasks) and more about the infrastructure and operational practices catching up.

## Links & Resources

- [AWS Developers Podcast -- Episode 195](https://developers.podcast.go-aws.com/web/episodes/195/index.html)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [Kiro IDE](https://kiro.dev)
- [Will Anthropic's MCP work with other LLMs? -- blog post](https://blog.mikegchambers.com/posts/will-anthropics-mcp-work-with-other-llms-yes-with-amazon-bed/)
- [MCP - Can Lambda do it? -- blog post](https://blog.mikegchambers.com/posts/mcp-can-lambda-do-it-streamable-http-model-context-protocol/)
- [Model Driven Agents - Strands Agents -- blog post](https://blog.mikegchambers.com/posts/model-driven-agents-strands-agents-a-new-open-source-model-f/)
- [Strands Tools -- blog post](https://blog.mikegchambers.com/posts/strands-tools-building-custom-ai-agents-with-python/)
