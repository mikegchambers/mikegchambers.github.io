---
title: "When the Model Is the Machine"
date: 2026-03-03
categories: [AI, Agents]
tags: [ai, software-development, strands, python, ai-functions, agents]
description: "AI agents, runtime software, and what comes after SaaS."
---

I want to show you something. A translation app. Clean interface, language selector, input field, a translate button. You type a phrase, pick a target language, hit translate, and the result appears. It works. It feels like an app.

![Translation App](/assets/images/www4-translation-app.jpg)

So... thirty seconds before I took this screenshot, the app didn't exist. In fact... There was no codebase. No repository. No designer mocked it up, no developer wrote it, no CI pipeline deployed it. Yes, you guessed right... An AI agent generated it — the layout, the styling, the interaction logic — at runtime, in response to a single prompt typed into a URL bar.

The agent that built this has exactly two tools. One generates an HTML page. The other tells the browser to swap out pieces of the DOM. That's it. There is no framework underneath, no component library, no state management system. The model holds the state. The model decides what to render. The model *is* the application... or maybe it *is* the execution environment?

Yes, this ultimate **everything** app is a party trick, and I want to be upfront about that. It's slow. It's a concept. But I think it points at something real, and I've spent the last few weeks trying to articulate what that something is.

---

## A Trillion Dollars of Doubt

Some numbers first.

In early 2026, the broader software sector fell roughly 29 percent. A [Reuters analysis](https://www.reuters.com/business/media-telecom/global-software-stocks-hit-by-anthropic-wake-up-call-ai-disruption-2026-02-04/) put the total market value lost at nearly a trillion dollars. Salesforce dropped about 27 percent year-to-date; Workday fell roughly 40 percent after issuing a sluggish revenue outlook ([Reuters](https://www.reuters.com/business/workday-tumbles-dour-revenue-outlook-amid-ai-threat-2026-02-25/)). Forbes ran the headline "[The SaaS-Pocalypse Has Begun](https://www.forbes.com/sites/donmuir/2026/02/04/300-billion-evaporated-the-saaspocalypse-has-begun/)." The Guardian asked whether the market was headed toward a "[SaaS-pocalypse](https://www.theguardian.com/australia-news/2026/feb/21/what-would-share-stock-market-saaspocalypse-mean-saas-apocalypse-meaning)." Private equity firms started circling, [buying up SaaS companies](https://m.economictimes.com/tech/technology/pe-firms-up-saas-buyouts-as-ai-resets-valuations-biz-models/articleshow/128922439.cms) at reset valuations.

The dominant narrative was that AI is about to eat traditional SaaS. Anthropic launched tools aimed at legal workflows, and [RELX lost over six billion pounds in value](https://www.thetimes.com/business/companies-markets/article/relx-loses-over-6bn-in-value-as-anthropic-launches-legal-work-ai-t9w2k0j58) in a single session. Business Insider declared that "[Software ate the world. Now AI is eating software.](https://www.businessinsider.com/software-ate-world-now-ai-eating-software-saas-anthropic-2026-2)" The fear was specific: if AI agents can orchestrate workflows directly, seat-based subscriptions lose their logic. Why pay per-user for five tools when one agent delivers the outcome?

> Note: Markets overshoot on fear the same way they overshoot on hype, and there were plenty of non-AI factors in the mix — enterprise budgets tightening, years of inflated valuations correcting, subscription growth already slowing before any agent entered the picture. Salesforce's CEO [publicly dismissed](https://www.ft.com/content/b74b8227-d7cb-4976-ba95-a3a27b79cbdd) the "SaaSpocalypse" framing. Bank of America called the selloff "[overblown](https://fortune.com/2026/02/04/why-saas-stocks-tech-selloff-freefall-like-deepseek-2025-overblown-paradox-irrational/)." A [Bain analysis](https://www.bain.com/insights/why-saas-stocks-have-dropped-and-what-it-signals-for-softwares-next-chapter/) argued that the drop signals a transition, not an extinction.

I don't think the selloff proves that AI will displace SaaS. But I think it surfaces a question worth taking seriously: *what happens to the value of prebuilt software when the effecacy of generated software keeps rising?*

That question has two dimensions, and they're often conflated.

### Where SaaS Goes From Here

The first dimension is **AI-assisted development**. Developers using coding assistants ship faster — [85 percent now use some form of AI tooling](https://www.itransition.com/software-development/statistics). This makes software cheaper to produce, which puts pressure on vendors who charge premium prices for what is, at its core, code running on servers. If the cost of building software falls, the price customers will pay for it falls too. This is deflationary, but it's evolutionary. It's the same dynamic that played out when cloud infrastructure commoditized hosting, or maybe when open-source commoditized databases. SaaS companies adapted before. Many will adapt again.

The second dimension is different in kind. **AI agents don't just help build software — they can replace the need for it.** If a sales team uses an agent that can pull data from a CRM, draft an email, update a pipeline, and generate a forecast, the question stops being "which SaaS tool should we buy?" and becomes "do we need the tool at all?" The value shifts from the software to the outcome. From the seat to the result. Pricing models are already following — [PYMNTS reports](https://www.pymnts.com/news/artificial-intelligence/2026/ai-moves-saas-subscriptions-consumption/) a shift from subscription to usage-based pricing, and IT Pro has coined "[Outcome as Agentic Solution](https://www.itpro.com/technology/artificial-intelligence/what-is-outcome-as-agentic-solution-oaas)" as a category.

This second dimension is the one the market is pricing in. Not because it's happening everywhere today, but because the trajectory raises the question. And my little party trick demo — an application that didn't exist until someone asked for it — is a small, imperfect illustration of what that trajectory might look like at the limit.

Project this forward five years. Bain's read — transition, not extinction — is probably closer to right. But I'd expect the restructuring to be significant. The companies that thrive will be those that embed AI deeply enough to become platforms for agent-driven workflows rather than destinations for human users clicking through interfaces. The ones that don't will face the same pressure the on-premise vendors felt a decade ago: not a sudden death, but a slow loss of relevance as the world builds around them.

---

## Inside the Machine

Let's go back to my party trick translation app. I want to walk through what actually happens when you load that page, because the architecture is much simpler than you might expect, and herein reveals something about where software might be going.

![www4 Architecture](/assets/images/www4.drawio.png)

It's a single Python file — about 550 lines — running a standard library HTTP server. When you visit the URL with a prompt (say, `/?prompt=language+translation+app`), the server does three things:

1. It creates a unique session and assigns it an AI agent — specifically an agent built with [Strands Agents SDK](https://strandsagents.com/latest/) and Claude Opus 4.6 running via Amazon Bedrock. (I work for AWS, and that's the way I roll.)
2. It serves a lightweight shell page: an empty `<div>`, a loading spinner, and a block of vanilla JavaScript that knows how to receive and render content.
3. The shell page immediately fires a POST request back to the server with the session ID and the prompt.

The agent then does what it does. It reads the prompt — "Generate a page for: languga e translation app" — and calls its first tool: `render_page`. This tool takes three arguments: a title, HTML body content, and CSS. The agent generates all three. The server returns them as JSON. The shell page injects the HTML into the DOM and the CSS into a style tag. The spinner fades out. The app appears.

Here is the `render_page` tool in its entirety:

```python
@tool(context=True)
def render_page(title: str, html: str, css: str, tool_context: ToolContext) -> str:
    tool_context.invocation_state["response"] = {
        "type": "render",
        "title": title,
        "html": html,
        "css": css,
    }
    return "Page rendered successfully."
```

That's it. Nothing else. There is no template engine, no component tree, no virtual DOM. The model produces the markup directly.

Now you interact. You type a phrase, select a language, click translate. The shell page captures that event through plain event delegation — it listens for form submissions, button clicks, link clicks, checkbox toggles, select changes, and enter keypresses. It formats the event into a structured message (e.g., `FORM SUBMIT [translate-form]: {"text": "hello", "language": "Spanish"}`) and sends it back to the server.

The agent receives this message as the next turn in its conversation. It has full context — it knows what page it generated, what elements exist, what IDs they have. It decides how to respond. For a translation result, it probably calls the second tool: `update_elements`.

```python
@tool(context=True)
def update_elements(updates: list[dict[str, str]], tool_context: ToolContext) -> str:
    tool_context.invocation_state["response"] = {
        "type": "update",
        "updates": updates,
    }
    return "Elements updated successfully."
```

This tool takes a list of `{id, html}` pairs and tells the frontend to replace the innerHTML of each element by ID. The result area updates. The rest of the page stays put. It's a targeted DOM patch, decided entirely by the model.

So... **there is no application state anywhere except inside the model's context window.** The agent doesn't write to a database. It doesn't set session variables. It doesn't maintain a state object. The conversation *is* the state. Every interaction adds a turn, and the model reasons over the full history to decide what to render next.

### What Would Make It Better

Its limitations with todays models are obvious. Every interaction requires a full round trip to the model, which means latency measured in seconds rather than milliseconds. The agent regenerates its understanding of the page from conversation context on every turn, which is wasteful. There's no persistence — close the tab and the session is gone.

Some of its issues are solvable these problems are within the same paradigm. Point being that this isn't even as good as it could be:

**Server-side DOM cache.** The most obvious improvement. Instead of relying entirely on the model's context to remember the current page state, the server could maintain a representation of the DOM. The agent could diff against it, and the server could validate that element IDs in `update_elements` calls actually exist. This would reduce errors and allow the model to work with a smaller context.

**Streaming generation.** Right now the agent generates the full HTML payload, then the server sends it. A streaming approach — where HTML is sent to the browser as the model produces it — would dramatically improve perceived performance. The page could progressively render, much like a server-side rendered page loading over a slow connection.

**Hybrid rendering.** Some interactions don't need the model at all. A dropdown menu opening, a tab switching between already-generated content, a tooltip appearing — these could be handled by lightweight generated client-side JavaScript, with the agent only invoked for decisions that require reasoning. The system prompt could instruct the agent to include specific interaction patterns that the shell page handles natively.

**Prompt caching and prefills.** For common application patterns — a form, a data table, a navigation layout — the agent could work from cached partial outputs rather than generating from scratch every time. The model is doing redundant work if it invents a fresh CSS reset for every page.

None of these improvements change the fundamental architecture. The model remains the runtime. The application remains ephemeral. But the experience moves from "party trick" to something you could genuinely use.

---

## The Real World Is Already Moving

My demo is a solo experiment, but the ideas behind it are showing up in serious, projects. Two in particular are worth watching.

### AG-UI: A Protocol for Agent-Driven Interfaces

The [AG-UI protocol](https://github.com/ag-ui-protocol/ag-ui) emerged from CopilotKit's work and has since attracted first-party support from Microsoft, Google, AWS, and others. It's an open, event-based protocol that standardizes how AI agents connect to frontend applications.

![AG-UI Protocol Architecture](/assets/images/ag-ui-diag.png)
*Image source: [AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui)*

The core insight is that agents need a structured way to communicate with UIs that goes beyond dumping text into a chat window. AG-UI defines roughly 16 event types that an agent backend can emit — events that represent things like "update this piece of state," "render this component," or "request human input before proceeding." The frontend listens for these events and renders accordingly.

This is the same pattern as my demo, but formalized and generalized. Where www4 has two hand-rolled tools and a bespoke shell page, AG-UI provides a protocol layer that lets any agent framework talk to any frontend. It supports SSE, WebSockets, and webhooks for transport. It includes middleware for loose format matching, so that agents built in different frameworks can connect without perfect specification compliance.

AG-UI sits in a deliberate position in an emerging stack. MCP (Model Context Protocol) gives agents access to tools. A2A (Agent-to-Agent) lets agents communicate with each other. AG-UI brings agents into the user interface. And now MCP itself is moving toward UI as a first-class concept — the [MCP Apps specification](https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/) defines a standard for tools to declare UI resources alongside their capabilities, rendered in sandboxed iframes with structured communication back to the host. The specification's own language is telling: it describes an "agentic app runtime." Together, these protocols describe a world where applications are assembled from agent capabilities rather than compiled from source code.

### MCP-Use: From Protocol to Interface

The [mcp-use-ts](https://github.com/mcp-use/mcp-use-ts) project takes a different but complementary approach — and is emerging as one of the first concrete implementations of the [MCP Apps extension](https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/). Where AG-UI standardizes the protocol between agents and UIs, mcp-use-ts focuses on making it trivially easy to build interfaces on top of MCP servers.

![mcp-use-ts](/assets/images/mcp-use-ts.png)
*Image source: [mcp-use-ts](https://github.com/mcp-use/mcp-use-ts/tree/main)*

Its most interesting feature is automatic UI generation from tool definitions. You define an MCP tool with a Zod schema — say, a tool that queries a database with parameters for table name, date range, and output format — and the framework generates an interactive form for that tool automatically. No frontend code needed.

But it goes further than auto-generated forms. Developers can build custom React widgets that are served alongside MCP tools as resources. This means an MCP server can expose not just capabilities but also the interfaces for using those capabilities. A database MCP server could come with a query builder UI. A monitoring MCP server could include a dashboard.

The `create-mcp-use-app` scaffolding tool lets you go from zero to a working application with an MCP backend and an auto-generated frontend in under a minute. The development server includes hot reload for both tools and widgets, and a built-in inspector that functions as both a debugging tool and a prototype UI.

This is relevant because it represents a concrete, usable step toward the architecture my demo illustrates. Instead of hand-writing a frontend and a backend and the glue between them, you define capabilities and let the tooling generate the interface. The "application" is a thin layer over agent capabilities, generated rather than authored.

---

## The Frontier

Is this post long enough for a conclusion?? Let me pull these threads together.

My demo shows an agent that generates a complete, interactive application at runtime from a single prompt. It's slow and it's limited, but it works. The model acts as the runtime, the state engine, and the decision-maker. There is no application until someone asks for one, and then there is exactly the application they asked for.

The SaaS selloff shows a market waking up to the possibility that static, prebuilt software is losing its premium. When agents can orchestrate outcomes directly, the value of the intermediary tools drops. The companies that survive will be those that become platforms for agent-driven work, not destinations for human-driven workflows.

AG-UI shows the infrastructure layer forming — a standardized way for agents to control user interfaces, backed by the biggest names in the industry. MCP-Use shows the developer experience becoming real — tools that let you go from capability definition to working UI without writing frontend code.

These are all points on the same line. And the line points toward a future where software is generated, not built. Where applications are ephemeral, not persistent. Where the currency is the idea — "I need a translation app," "show me a sales dashboard," "build me a tool that tracks my inventory" — and the execution of that idea is handled in real time by models that understand what you want and can produce it on demand.

This isn't a prediction about next quarter. The models are still too slow for production use in this mode. Context windows, while generous, still impose limits on session complexity. The quality of generated interfaces, while impressive, isn't yet reliable enough for mission-critical work. These are real constraints.

But every one of them is improving on a curve that software engineers will recognize. Models are getting faster. Context windows are growing. Output quality is climbing. The gap between "interesting demo" and "production system" is closing on a timeline measured in years, not decades.

### What This Means for Builders

I want to be clear: this is not a story about developers becoming obsolete. It's a story about what developers *do* shifting.

If the value of writing code is falling — and it is, by every measure — then the value of knowing *what to build* is rising. Architecture, domain expertise, problem framing, verification, orchestration. These are the skills that appreciate as the cost of execution drops toward zero.

The developers who thrive in this landscape will be the ones who stop thinking of themselves as people who write software and start thinking of themselves as people who *define intent and verify outcomes*. The code becomes the cheapest part. The thinking becomes the most expensive.

And there's a broader opportunity here, one that goes beyond the software industry. If generating an application becomes as easy as describing what you want, then the bottleneck on innovation moves from "can we build it?" to "can we imagine it?" The currency becomes ideas. Good ones, specific ones, ones grounded in real problems and real domain knowledge.

That's not a future to fear. It's a future to build toward.

---

*The www4 project referenced in this post is available at [github.com/mikegc-aws/www4](https://github.com/mikegc-aws/www4). The AG-UI protocol is at [github.com/ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui). MCP-Use is at [github.com/mcp-use/mcp-use-ts](https://github.com/mcp-use/mcp-use-ts).*
