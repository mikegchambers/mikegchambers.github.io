---
title: "Nine Agent Frameworks, Compared with Data and Code"
date: 2026-03-11
categories: [AI, Agents]
tags: [ai, agents, frameworks, langgraph, crewai, openai, google-adk, autogen, strands, pydantic-ai, smolagents, llamaindex, python, comparison]
description: "Nine Python agent frameworks, compared honestly. Architecture, code samples, community sentiment, and what actually matters when you're picking one."
image: /assets/images/banner.jpg
---

I've been building with agent frameworks for a couple of years now. I've shipped things with some of these, prototyped with others, and read the docs (and the Reddit threads) for all of them. This post is the comparison I wish existed when I started. Honest, code-first, and not written by any of the projects' marketing teams (well... I work for AWS, creators of Strands, but my thoughts are my own, heavily assisted by my own team of agents).

> AI Used: The vast majority of the research for this post was assisted by AI that I have designed. The AI uses Claude, the [Tavily MCP server](https://docs.tavily.com/documentation/mcp), and many other MCP data sources.  The following prompt was used:
> _"init a new blog post. the post must be a contrast and compare of agent frameworks. it must include honest, fact based information, code samples for common things, and should represent a snapshot of the current situation. A sort of "state of the union" for agentic frameworks. The research should go wider than just relying on what is written by the project (or project sponsor) and should dig in and write a post that is of immense value to developers. Include top frameworks as of today. You must include Strands Agents SDK."_

This isn't a ranking. It's a snapshot of where things stand in March 2026, with enough detail for you to make your own call.

---

## The Field

Nine frameworks made this list. Not because they're the only ones, but because they're the ones developers are actually using, talking about, and building production systems with.

| Framework | Stars | Age (months) | Last 6 months | License | Primary Backer |
|---|---|---|---|---|---|
| AutoGen | 55.4K | 31 | +1,982 | MIT + CC-BY-4.0 | Microsoft |
| CrewAI | 45.7K | 28 | +2,540 | MIT | CrewAI Inc |
| Google ADK | 18.3K | 11 | +1,900 | Apache-2.0 | Google |
| LangGraph | 26.1K | 31 | +2,351 | MIT | LangChain |
| LlamaIndex | 47.6K | 40 | +1,183 | MIT | LlamaIndex Inc |
| OpenAI Agents SDK | 19.7K | 12 | +1,554 | MIT | OpenAI |
| Pydantic AI | 15.4K | 21 | +996 | MIT | Pydantic |
| Smolagents | 25.9K | 15 | +1,018 | Apache-2.0 | Hugging Face |
| Strands Agents | 5.3K | 10 | +618 | Apache-2.0 | AWS |

*Methodology: Stars and Age come from GitHub's API. "Age" is measured from the repo's first stargazer event, not its creation date. "Last 6 months" is calculated from monthly star history via the [OSS Insight API](https://ossinsight.io/). All data collected March 2026.*

Raw stars are a popularity contest, not a quality metric. The **last 6 months** column tells a more interesting story. CrewAI (+2,540) and LangGraph (+2,351) are still gaining the most stars in absolute terms, but Google ADK (+1,900) is close behind despite being less than a year old. AutoGen has the most total stars but its recent growth (+1,982 over 6 months) is slowing as it transitions into Microsoft's broader Agent Framework. Smolagents had an explosive launch (728 to 19,850 stars in its first nine months) but the last six months show it plateauing at +1,018. Strands has the smallest community (+618) partly because it's the youngest (May 2025) and partly because it grew through AWS adoption rather than viral open-source traction, but origins are already running inside AWS products like Kiro, Amazon Q, and AWS Glue.

Two charts tell the full story. First, cumulative stars over time:

![Cumulative GitHub Stars Over Time](/assets/images/agent-framework-stars-cumulative.png)

AutoGen and LlamaIndex dominate the top of the chart because they had a two-year head start. CrewAI's trajectory is the steepest sustained climb. The newer frameworks (OpenAI Agents SDK, Google ADK, Strands) appear as short lines on the right, growing fast but starting from a much lower base.

Now the same data shown as monthly activity, new stars added per month and look, there is actually a slight, overall, downward trend. (More thoughts on this later.)

![Monthly Star Activity Over Time](/assets/images/agent-framework-stars-activity.png)

This is where the cumulative chart's illusions break down. Every framework has a launch spike, some enormous. AutoGen hit nearly 12K new stars in October 2023. CrewAI burst onto the scene in January 2024 with 5K+. Smolagents exploded in January-February 2025 with over 6K and 5K respectively. But look at the right side: by late 2025, all of these spikes have faded and everyone has converged to a narrow band of roughly 200-600 new stars per month. The launch hype fades. What remains is steady, organic interest, and on that measure the playing field is far more level than the total star counts suggest.

---

## The Philosophies

These frameworks aren't interchangeable. They reflect different ideas about how agents should work, and those differences matter.

**Scaffold-heavy frameworks** (LangGraph, AutoGen) give you explicit control over execution flow. You define graphs, nodes, edges, state machines. You get predictability at the cost of boilerplate.

**Model-driven frameworks** (Strands Agents, Smolagents) take the opposite stance. Give the model tools, give it a goal, and get out of the way. Less scaffolding, more trust in the model's reasoning. This works better than it used to, because the models have gotten much better at tool use and planning.

**Role-based frameworks** (CrewAI) model the problem as a team of specialists with defined roles. It's intuitive for business workflows but can feel constraining when you need fine-grained control.

**Type-safe frameworks** (Pydantic AI) focus on structured, validated outputs. Less about orchestration, more about making sure the LLM returns exactly what your code expects.

**Vendor-optimized frameworks** (OpenAI Agents SDK, Google ADK) are tuned for a specific model provider's ecosystem but generally work with others.

---

## Show Me the Code

The best way to understand the difference is to see the same thing built nine ways. Here's the simplest possible pattern: create an agent with one tool, run it.

### Strands Agents

```python
from strands import Agent, tool
import random

@tool
def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides.

    Args:
        sides: Number of sides on the dice
    """
    return f"You rolled a {random.randint(1, sides)}"

agent = Agent(tools=[roll_dice])
response = agent("Roll a 20-sided dice for me")
print(response)
```

Three imports, a decorated function, two lines to run. The `@tool` decorator pulls the schema from the docstring and type hints. The agent uses Amazon Bedrock by default (Claude Sonnet), but you can swap models and providers:

```python
from strands.models import OpenAIModel
agent = Agent(model=OpenAIModel(model_id="gpt-4o"), tools=[roll_dice])
```

### LangGraph

```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
import random

def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

model = init_chat_model("anthropic:claude-sonnet-4-20250514")
agent = create_react_agent(model, tools=[roll_dice])

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Roll a 20-sided dice for me"}]}
)
print(result["messages"][-1].content)
```

LangGraph's prebuilt `create_react_agent` keeps it relatively simple for basic cases. The real power (and complexity) shows up when you build custom graphs with nodes and edges, which is what most production users end up doing.

### CrewAI

```python
from crewai import Agent, Task, Crew
from crewai.tools import tool
import random

@tool
def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

roller = Agent(
    role="Dice Roller",
    goal="Roll dice accurately when asked",
    backstory="You are a tabletop gaming assistant",
    tools=[roll_dice],
)

task = Task(
    description="Roll a 20-sided dice for me",
    expected_output="A dice roll result",
    agent=roller,
)

crew = Crew(agents=[roller], tasks=[task])
result = crew.kickoff()
print(result)
```

More ceremony than the others. You define an agent with a role, backstory, and goal, then wrap the interaction in a Task and a Crew. This makes more sense in multi-agent scenarios where you have a researcher, writer, and editor working together. For a single tool call, it's overhead.

### OpenAI Agents SDK

```python
from agents import Agent, Runner, function_tool
import random

@function_tool
def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

agent = Agent(
    name="Dice Agent",
    instructions="You help roll dice when asked.",
    tools=[roll_dice],
)

result = Runner.run_sync(agent, "Roll a 20-sided dice for me")
print(result.final_output)
```

Clean and minimal. The SDK works with OpenAI models natively and supports other providers through the Chat Completions API or LiteLLM. Built-in tracing is a nice touch. You get visibility into agent runs without extra instrumentation.

### Google ADK

```python
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
import random

def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

root_agent = Agent(
    name="dice_agent",
    model="gemini-2.5-flash",
    instruction="You help roll dice when asked.",
    tools=[roll_dice],
)

runner = InMemoryRunner(agent=root_agent, app_name="dice_app")
session = await runner.session_service.create_session(app_name="dice_app", user_id="user1")
response = runner.run(user_id="user1", session_id=session.id, new_message=Content(parts=[Part(text="Roll a 20-sided dice for me")]))
async for event in response:
    if event.content and event.content.parts:
        print(event.content.parts[0].text)
```

ADK's standout feature is multi-agent composition. It has `SequentialAgent`, `ParallelAgent`, and `LoopAgent` primitives baked in, plus a browser-based dev UI (`adk web`) for testing. The deployment story to Cloud Run and Vertex AI is smooth if you're in the Google ecosystem.

### Pydantic AI

```python
from pydantic_ai import Agent
import random

agent = Agent(
    "openai:gpt-4o",
    system_prompt="You help roll dice when asked.",
)

@agent.tool_plain
def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

result = agent.run_sync("Roll a 20-sided dice for me")
print(result.output)
```

Where Pydantic AI shines is structured output. Define a Pydantic model, and the framework guarantees the LLM's response validates against it, retrying with error context if it doesn't. This eliminates a whole class of production bugs around JSON parsing failures.

### Smolagents

```python
from smolagents import CodeAgent, InferenceClientModel, tool
import random

@tool
def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides.

    Args:
        sides: Number of sides on the dice
    """
    return f"You rolled a {random.randint(1, sides)}"

model = InferenceClientModel()
agent = CodeAgent(tools=[roll_dice], model=model)
agent.run("Roll a 20-sided dice for me")
```

Smolagents has a unique angle: its `CodeAgent` writes Python code to orchestrate tool calls instead of using JSON tool-calling. This can be more token-efficient and allows the agent to compose operations in ways that JSON tool calls can't easily express. There's also a `ToolCallingAgent` for the traditional approach.

### AutoGen

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
import random

def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

model = OpenAIChatCompletionClient(model="gpt-4o")
agent = AssistantAgent("dice_agent", model_client=model, tools=[roll_dice])

async def main():
    await Console(agent.run_stream(task="Roll a 20-sided dice for me"))

import asyncio
asyncio.run(main())
```

AutoGen is async-first and event-driven. The `Team` abstraction is where it gets interesting, with agents collaborating through an event system. The framework has been through a major rewrite (0.2 to 0.4), which improved the architecture but left a lot of outdated tutorials floating around online.

### LlamaIndex

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
import random

def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides."""
    return f"You rolled a {random.randint(1, sides)}"

tool = FunctionTool.from_defaults(fn=roll_dice)
agent = FunctionAgent(
    tools=[tool],
    llm=OpenAI(model="gpt-4o"),
    system_prompt="You help roll dice when asked.",
)

async def main():
    response = await agent.run("Roll a 20-sided dice for me")
    print(response.response.content)

import asyncio
asyncio.run(main())
```

LlamaIndex's strength isn't the agent loop itself. It's the 160+ data connectors, RAG pipeline, and evaluation modules. If your agent needs to query documents, databases, or APIs, LlamaIndex probably has a connector for it. The agent is the orchestration layer on top of that retrieval infrastructure.

---

## What Actually Matters

Stars and code samples only tell part of the story. These are the things I think actually matter when you're choosing a framework for real work.

### Model Lock-in

This is the single most important architectural decision. Some frameworks give you freedom, others push you toward a provider.

**Model-agnostic** (use any provider without friction): Strands Agents, LangGraph, Smolagents, Pydantic AI, LlamaIndex. Strands supports Bedrock, OpenAI, Anthropic, Gemini, Ollama, Mistral, LiteLLM, SageMaker, and more with dedicated provider classes. LangGraph inherits LangChain's broad integration layer.

**Provider-first but open**: Google ADK (Gemini-optimized, but connectors for Claude, Ollama, vLLM), OpenAI Agents SDK (works natively with OpenAI, supports others via Chat Completions API or LiteLLM), CrewAI (any LLM, but some community reports of issues with non-OpenAI models).

**Provider-locked**: None of the frameworks are truly locked, but the depth of integration varies enormously. Running Strands on Bedrock or ADK on Vertex will always be a smoother experience than fighting against the grain.

### MCP Support

The [Model Context Protocol](https://modelcontextprotocol.io/) has become the standard for connecting agents to external tools and data sources. Where each framework stands as of today.

- **First-class native**: Strands Agents, CrewAI, Smolagents, Pydantic AI
- **Built-in via integrations**: LangGraph (added in 1.0), OpenAI Agents SDK, Google ADK (via adapters)
- **Built-in**: AutoGen
- **Emerging/partial**: LlamaIndex

If you're building agents that need to connect to existing MCP servers (and there are a lot of them now), this matters. Strands in particular treats MCP as a first-class tool source, letting you connect to any MCP server and use its tools alongside native Python tools.

### Multi-Agent Patterns

Not every project needs multiple agents, but when you do, the approaches differ a lot.

**Strands Agents** offers three distinct patterns: **Graph** (developer-defined flowchart, LLM decides path at each node), **Swarm** (autonomous agent handoffs with shared context), and **Workflow** (deterministic DAG with parallel execution). It also supports the **A2A protocol** for cross-platform agent communication.

**Google ADK** has compositional primitives: `SequentialAgent`, `ParallelAgent`, `LoopAgent`, plus `LlmAgent` for dynamic routing. Clean and explicit.

**CrewAI** models everything as crews of role-playing agents. Intuitive for collaborative workflows, less flexible for graph-like execution.

**AutoGen** uses Team abstractions with event-driven collaboration. Strong for conversational multi-agent patterns.

**LangGraph** builds multi-agent systems through graph composition. Maximum control, maximum code.

**LlamaIndex** supports agent handoff and microservice-based deployments where agents run independently with message queues.

### The Deployment Gap

This is where the field really splits. Some frameworks are SDKs that stop at the Python process boundary. Others have a story for getting your agent into production.

**Full deployment story:**
- **Strands Agents**: Docker/Fargate, Lambda, and Amazon Bedrock AgentCore for managed runtime with scaling, isolation, and logging. The AgentCore integration is the deepest production deployment story of any framework here.
- **Google ADK**: Cloud Run and Vertex AI Agent Engine with IAM, VPC controls, and sandboxed code execution.
- **LangGraph**: Commercial platform with LangGraph Cloud, usage-based pricing (Deployment Runs per invocation + Deployment Uptime).

**SDK + guidance:**
- **Pydantic AI**: Documented serverless patterns for Lambda, Step Functions, DynamoDB. You build the infrastructure.
- **CrewAI**: Optional Agent Management Platform (AMP) with RBAC and encryption. Commercial offering.
- **OpenAI Agents SDK**: Production-ready SDK with tracing, but deployment is your responsibility.

**SDK only:**
- **Smolagents, AutoGen, LlamaIndex**: These are libraries. How you deploy them is up to you. Not a criticism; sometimes a library is what you want.

### Observability

You can't debug what you can't see, and agents are notoriously hard to debug.

- **LangGraph + LangSmith**: The most mature observability story. Tracing, evaluation, monitoring. SOC 2 Type II compliant. Commercial product.
- **Pydantic AI + Logfire**: Integrated structured logging and evaluation. Type-safe debugging.
- **OpenAI Agents SDK**: Built-in automatic tracing of agent runs. No extra setup.
- **Strands Agents**: OpenTelemetry-based tracing, integrates with AWS X-Ray and CloudWatch. Also works with any OpenTelemetry backend.
- **Others**: Varying degrees of logging. You'll likely bring your own observability stack.

---

## The Honest Take

Time to stop being diplomatic.

### LangGraph

**The good**: It's the Swiss Army knife. Broad integrations, mature tooling, LangSmith is actually useful, and the durable execution model handles long-running agents well. If you're building something complex and stateful, LangGraph is battle-tested.

**The honest**: It's heavy. The abstraction layers have abstraction layers. The documentation is extensive but scattered across LangChain and LangGraph, and it's not always clear which version you're reading about. The pricing for LangGraph Cloud (usage-based on Deployment Runs) can surprise you at scale. Community sentiment is mixed. Reddit threads and HN discussions regularly surface developers who stripped LangChain out and went back to raw Python, citing over-abstraction and rapid API churn. That doesn't mean it's bad, but the vocal developer backlash is hard to ignore.

**Use it if**: You need durable execution, complex stateful workflows, and you're willing to invest in learning the ecosystem. You want the most mature commercial platform.

### CrewAI

**The good**: Fastest path from idea to multi-agent prototype. The role/backstory/goal pattern clicks immediately. The community is massive and active. MCP and A2A support are first-class.

**The honest**: The abstraction can fight you when you need fine-grained control. Multiple teams report hitting a ceiling at the 6-12 month mark, with some rewriting to LangGraph or custom orchestration. Infinite loops and lack of built-in observability are recurring complaints. Some developers report issues with non-OpenAI models. The Agent Management Platform needs SOC 2 certification if you're in a regulated environment. The "crew" metaphor works great for content pipelines and less great for complex branching logic.

**Use it if**: You're building collaborative multi-agent workflows, want fast prototyping, and the crew metaphor fits your problem.

### OpenAI Agents SDK

**The good**: Dead simple. You can go from zero to working agent in under an hour. Built-in tracing, session persistence (SQLite), and guardrails as first-class primitives. Massive adoption in terms of PyPI downloads.

**The honest**: Works best with OpenAI models, though it supports other providers via Chat Completions API and LiteLLM. No built-in semantic memory layer. The "handoff" pattern for multi-agent is simple but limited compared to graph-based approaches.

**Use it if**: You're an OpenAI shop and want the path of least resistance. Great for getting started and for simpler agent architectures.

### Google ADK

**The good**: Clean multi-agent composition primitives. The dev UI (`adk web`) is excellent for testing. Tight integration with Vertex AI and Cloud Run. Available in Python, TypeScript, Go, and Java, which is more language breadth than any other framework here.

**The honest**: Gemini-first. The connectors for other providers exist but aren't as polished. The documentation is Google-quality (thorough but sometimes overwhelming). Session state management and async complexity felt rough when I tried it. And I'll say what some are thinking: Google's reputation for sunsetting products makes some developers cautious about deep investment. You'll get the best experience on Google Cloud, and it will feel like a second-class citizen elsewhere.

**Use it if**: You're in the Google ecosystem, want multi-language support, or the SequentialAgent/ParallelAgent/LoopAgent composition model fits your architecture.

### AutoGen

**The good**: Strong academic backing, interesting Team abstraction for conversational multi-agent patterns. Built-in code execution. The event-driven architecture is well-designed.

**The honest**: The 0.2-to-0.4 rewrite created a documentation and tutorial minefield. Search results are full of outdated code for a version that no longer works. More importantly, Microsoft is steering new users toward the Microsoft Agent Framework (via Semantic Kernel), and while AutoGen remains maintained, it's unclear how much standalone investment it will receive going forward. Token consumption and circular conversations were persistent complaints from the community. If you're starting fresh today, consider whether you're building on a foundation that's actively moving under your feet.

**Use it if**: You need conversational multi-agent systems, code execution as a core capability, or you're already in the Microsoft ecosystem.

### Strands Agents

**The good**: The model-driven philosophy actually works. Minimal boilerplate, broad provider support (12+ providers with dedicated classes), first-class MCP integration, three distinct multi-agent patterns (Graph, Swarm, Workflow), A2A protocol support, and the deepest AWS deployment story through Bedrock AgentCore. The `@tool` decorator is dead simple. The hook system gives you interception points without fighting the framework. It's not just a side project: the model-driven approach behind Strands emerged from building agents for products like Kiro, Amazon Q, and AWS Glue, and the SDK has hit 14 million downloads.

**The honest**: It's newer than most frameworks on this list, so the community is smaller. The documentation is good but still growing. Some features (bidirectional streaming) are experimental. Lambda deployments don't support streaming, so you need AgentCore Runtime or Fargate for that use case. If you're not on AWS, you miss the deployment story advantage, though the SDK works fine with any provider.

**Use it if**: You want a lightweight, model-driven approach. You're on AWS (or plan to be). You want to go from prototype to production without switching frameworks. You trust the model to drive decisions and want minimal scaffolding.

### Pydantic AI

**The good**: If structured output matters to you (and it should), nothing else comes close. The type-safe approach catches errors that would otherwise surface in production. The graph-based multi-agent system with durable execution is well-designed. Logfire integration provides solid observability.

**The honest**: It's increasingly used as a validation layer alongside other frameworks rather than a standalone solution. Developers combine Pydantic AI with LangChain for vector stores or CrewAI for orchestration. That's actually a strength (low lock-in), but it means Pydantic AI alone won't solve your full agent architecture. The multi-agent graph system is powerful but newer and less battle-tested than LangGraph's. Community is smaller.

**Use it if**: Output structure is critical to your application. You're building API-driven agents. Your team already uses Pydantic and wants a familiar mental model.

### Smolagents

**The good**: True to its name. Minimal code surface, the CodeAgent approach is interesting (writing Python instead of JSON tool calls), and it's model-agnostic down to its bones. Push-to-Hub lets you share agents as easily as models. The Hugging Face community gives it momentum.

**The honest**: A CVE (CVE-2025-9959) exposed a sandbox escape in versions before 1.21.0. It's fixed, but it's a reminder that code-executing agents need serious sandboxing. Production deployment requires careful configuration of import whitelisting and sandbox environments (Docker, E2B, Modal). The framework is more experimental than production-hardened.

**Use it if**: You want a small, code-first agent library. You're doing research or prototyping. You want the CodeAgent pattern for token-efficient tool orchestration. You're comfortable managing your own sandboxing.

### LlamaIndex

**The good**: Unmatched retrieval infrastructure. 160+ data connectors, evaluation modules, and the RAG pipeline that most agent frameworks wish they had. The CLI tooling (`llamactl`) for deployment is convenient. If your agent's primary job is querying documents and data sources, this is the most complete solution.

**The honest**: The agent loop itself is less sophisticated than dedicated agent frameworks. You're really buying the retrieval stack and getting an agent as the orchestration layer on top. For pure agentic workflows (tool calling, multi-step reasoning, multi-agent coordination), other frameworks are stronger.

**Use it if**: Your agent is fundamentally a retrieval/RAG system. You need to connect to many data sources. You want evaluation and testing baked in.

---

## The Decision Matrix

If you're still reading, here's the cheat sheet.

**"I need complex, stateful workflows with maximum control"**: LangGraph.

**"I need a multi-agent crew for a content/research pipeline"**: CrewAI.

**"I need the simplest possible thing that works"**: OpenAI Agents SDK.

**"I need structured, validated outputs from my agents"**: Pydantic AI.

**"I need to query documents and data sources"**: LlamaIndex.

**"I'm in the Google ecosystem"**: Google ADK.

**"I want code-generating agents for research"**: Smolagents.

**"I need conversational multi-agent teams"**: AutoGen.

**"I want model-driven agents with minimal scaffolding"**: Strands Agents.

**"I need something in production on AWS next month"**: Strands Agents + Bedrock AgentCore.

---

## Where This Is All Going

A year ago the question was "which framework should I learn?" Now it's "do I even need a framework at all?" That Reddit thread, "Are we still using LangChain in 2026 or have you guys moved to custom orchestration?", captures a real tension. There's a growing "no framework" movement, just look at the "Monthly Star Activity Over Time" above, it's not wrong. Models have gotten good enough at tool use that a raw Python loop with the provider's API can get you surprisingly far. Vendor lock-in anxiety is real enough that major players formed the Agentic AI Foundation (AAIF) to promote interoperability and open standards.

The frameworks that will survive are the ones that provide genuine value beyond what you'd write yourself. Durable execution, managed deployment, observability, multi-agent coordination, structured outputs. These are hard problems worth depending on a library to solve. Everything else is scaffolding around a model that's increasingly capable of scaffolding itself.

The trend is clear. Less framework, more model. The best frameworks in this list already know that. They're getting thinner, not thicker. They're trusting the model more and engineering the prompt less. Strands calls this "model-driven." Smolagents calls it "barebones." Pydantic AI calls it "the Pydantic way." The label doesn't matter. The direction does.

Pick the one that fits your cloud, your team, and your problem. Don't pick the one with the most stars.

Connect with me on [LinkedIn - linkedin.com/in/mikegchambers](https://linkedin.com/in/mikegchambers), and tell me what you think.
