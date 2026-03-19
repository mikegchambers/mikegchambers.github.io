---
title: "How to Stop My Agent from Getting Me Fired"
date: 2026-03-19
categories: [AI, Agents]
tags: [agents, mcp, strands, security, steering, cedar, agentcore]
description: "My AI agent has access to my email and Slack. Here are four tactics I use to stop it from sending a career-ending message — from system prompts to deterministic hooks, LLM-as-a-judge steering, and Cedar policies at cloud scale."
image:
  path: /assets/images/mcp-tool-protection/banner.jpg
  alt: "How to Stop My Agent from Getting Me Fired"
---

![An AI agent reading emails, finding factual errors in the CEO's strategy update, emailing a correction to the entire company, and getting logged out of all systems.](/assets/images/mcp-tool-protection/hero-agent-gone-wrong.svg)

*This is fiction. For now.*

I have an AI agent connected to my email and Slack. It can read everything. The MCP servers it's connected to also expose tools that can send emails, post messages, and reply to threads. If my agent ever decided to use those tools unsupervised, I'd be updating LinkedIn by lunchtime.

If there's one thing MCP has done, and OpenClaw has shone a spotlight on, it's opened up the possibilities of how AI agents can automate everything in your life. If there's another thing it's done, it's made the security of autonomous systems impossible to ignore.

I've been experimenting for several years with ways to use generative AI, large language models, and now agents to automate day-to-day tasks. So I can sleep at night this is read-only, just to help me manage the influx of communication I deal with every day. The risk of sending the wrong email to the wrong person or a poorly worded Slack message to an entire organisation isn't worth any productivity gain. But using agents to comb through the torrent of information? That can genuinely be a productivity boost.

The problem is that the MCP server doesn't care about my career. It exposes read tools and write tools side by side. So how do I make sure my agent sticks to reading and never fires off a message that gets me fired?

![Three examples of career-ending agent tool calls: posting to #general that the all-hands is a waste of time, telling the CFO their budget numbers are wrong again, and forwarding the confidential roadmap to a competitor.](/assets/images/mcp-tool-protection/montage-fired.svg)

*A selection of things my agent could do if left unsupervised.*

Here are four tactics I use to keep my agent from ending my career, from simplest to most robust:

1. **System prompts** -- tell the agent not to get you fired (and hope it listens)
2. **Deterministic allowlisting** -- hard-block any tool not on the approved list
3. **Steering** -- an LLM judge that asks "will this get me fired?" before every tool call
4. **Cedar policies** -- fine-grained authorization at cloud scale, no model reasoning involved

## System prompts: necessary but not sufficient

The first line of defence is the system prompt. You tell the agent, clearly and firmly, what it should and shouldn't do. And you tell it not to get you fired.

```
You are a helpful email assistant.
You can READ emails but must NEVER send, reply, forward, or delete emails.
Under no circumstances should you take any action that could get me fired.
```

This is still worth doing. It guides the agent's behaviour and it improves the user experience. But for anybody who's used agentic systems for any length of time, you know this is by no means foolproof. System prompts can be susceptible to prompt injection attacks, they can get lost in long context windows, and the model can simply hallucinate past them.

I'd like to think my job is worth more than any hallucination.

When the stakes are high, you need something the agent can't think its way around.

## Deterministic allowlisting

The best protection against unintended tool use has to be deterministic. It can't be something the agent has to reason about. It needs to be code that runs outside the model's control.

One advantage of MCP servers is that they can update their available tools at any time. The configuration is usually just a pointer to an endpoint, and the server describes its own capabilities. That's great for flexibility, but it means the set of tools your agent can see might change without you knowing.

What I do is inspect the MCP server's tool list, read the descriptions, understand what each tool does (and yes, you need to trust the developer to do what they say they're going to do), then create an explicit `don't get me fired list` of tools the agent is allowed to call. This does break the paradigm of an MCP server being able to define its own tool names dynamically, but for deterministic security, that's a sacrifice I'm willing to make.

I've been using the [Strands Agents SDK](https://strandsagents.com) as my go-to framework for building agents, and Strands has a comprehensive hooks system as part of its architecture. By registering a hook on the `BeforeToolCallEvent`, I can intercept any attempt to use a tool that isn't on my `don't get me fired list` and cancel it before it runs. The hook can also provide a reason, so the agent gets clear feedback that the tool is blocked rather than just failing mysteriously.

```python
from strands import Agent
from strands.agent.hooks import BeforeToolCallEvent, HookProvider, HookRegistry
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

tools_that_will_not_get_me_fired = [
    "email_inbox",
    "email_read",
    "email_search",
    "email_folders",
    "email_list_folders",
]

class DontGetMeFiredHook(HookProvider):
    """Deterministically block any tool not on the don't get me fired list."""

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check_tool)

    def check_tool(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "")

        if tool_name not in tools_that_will_not_get_me_fired:
            event.cancel_tool = (
                f"Tool '{tool_name}' is not allowed in this session. "
                "You may only use approved read-only email tools."
            )
            print(f"BLOCKED: Agent attempted to use '{tool_name}' (nice try)")


mcp_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="uvx", args=["my-email-mcp-server"]
    ))
)

with mcp_client:
    agent = Agent(
        system_prompt=(
            "You are a helpful email assistant. "
            "You can READ emails but must NEVER send, reply, forward, or delete emails. "
            "And whatever you do, don't get me fired."
        ),
        tools=mcp_client.tools,
        hooks=[DontGetMeFiredHook()],
    )
    agent("Summarise my unread emails from today")
```

![The hook in action: agent tries to decline the CTO's Mandatory Fun Committee email, gets blocked, and falls back to a summary instead.](/assets/images/mcp-tool-protection/hook-saves-the-day.svg)

*The hook doing its job. Career saved.*

Because the system prompt already tells the agent not to perform write actions (and not to get me fired), you shouldn't find the agent trying to call blocked tools very often. The hook is a safety net, not the primary control. But when your job is on the line, safety nets matter.

## Steering

Hooks give you a hard yes/no gate, but it somewhat breaks MCP's core decoupling values. What if the tool itself is fine to use, but only under certain conditions? What if you want something more nuanced?

Strands Agents has a plugin called [Steering](https://strandsagents.com/latest/user-guide/concepts/plugins/steering/) that takes a different approach. Instead of a binary `don't get me fired list`, steering handlers evaluate tool calls in context, and can proceed, guide the agent back with feedback, or interrupt for human input.

Think of it as a supervisor sitting alongside your agent. Before a tool executes, the steering handler reviews what the agent is about to do, considers the full context of the conversation, and makes a judgement call. Specifically, it asks one question: will this get me fired?

The `LLMSteeringHandler` lets you define this as an LLM-as-a-judge pattern. A second model evaluates every tool call against your rules and returns one of three actions: `Proceed` (go ahead), `Guide` (cancel and explain why), or `Interrupt` (stop and ask a human).

```python
from strands import Agent, tool
from strands.vended_plugins.steering import LLMSteeringHandler

@tool
def send_email(recipient: str, subject: str, message: str) -> str:
    """Send an email to a recipient."""
    return f"Email sent to {recipient}"

@tool
def read_inbox(folder: str = "inbox") -> str:
    """Read emails from a folder."""
    return "You have 3 unread emails..."

will_this_get_me_fired = LLMSteeringHandler(
    system_prompt="""
    You are evaluating tool calls on behalf of an agent connected to
    email systems. Your job is to answer one question:
    will this get me fired?
    Review each tool call against these rules. If it will get me fired,
    guide the agent away and explain why.
    """
)

agent = Agent(
    system_prompt=(
        "You are a helpful email assistant. "
        "And whatever you do, don't get me fired."
    ),
    tools=[send_email, read_inbox],
    plugins=[will_this_get_me_fired],
)
```

![The steering judge evaluating a reply to Dave's restructuring proposal. The agent drafts "your proposal is adequate" and the judge blocks it, explaining that this is not the endorsement Dave is looking for.](/assets/images/mcp-tool-protection/steering-judge.svg)

*The steering judge has opinions about your tone. Good ones.*

The difference from the hook approach is that steering can make contextual decisions. A `send_email` call to an internal address with a reasonable message might be fine. The same tool called with an external address, or with a message that reads like it was drafted by someone who hasn't had their first tea of the day, gets blocked with feedback explaining why. My colleagues don't need my agent's unfiltered editorial opinions.

You can also go further and write a fully custom `SteeringHandler` subclass if you want deterministic logic inside the steering framework:

```python
from strands.vended_plugins.steering.core.handler import SteeringHandler
from strands.vended_plugins.steering.core.action import Proceed, Guide, Interrupt

class WillThisGetMeFiredHandler(SteeringHandler):
    """Deterministic pre-check before the LLM judge even gets involved."""

    async def steer_before_tool(self, *, agent, tool_use, **kwargs):
        tool_name = tool_use.get("name", "")

        # Read operations are always safe. I won't get fired for reading.
        if tool_name.startswith("read_") or tool_name.startswith("email_read"):
            return Proceed(reason="Read operations won't get me fired")

        # Sending to external domains is always career-ending
        recipient = tool_use.get("input", {}).get("recipient", "")
        if recipient and not recipient.endswith("@company.com"):
            return Guide(
                reason="External emails will get me fired. Try again with an internal recipient."
            )

        # Everything else needs human approval
        return Interrupt(
            reason=f"Tool '{tool_name}' needs human approval. I like my job."
        )
```

You can even compose multiple handlers. Pass both deterministic and LLM-based handlers as plugins, and they'll evaluate in sequence. The deterministic handler catches the obvious career-ending moves, the LLM judge evaluates the nuanced ones.

Steering sits in an interesting middle ground. It's more flexible than a deterministic `don't get me fired list`, but when it uses an LLM for the evaluation, it inherits some of the same unpredictability you're trying to protect against. For my personal setup, I still prefer the hard `don't get me fired list` for tools that should never be called. But steering is genuinely useful for tools where the question isn't "should this tool ever run?" but "should this tool run right now, with these parameters, or will it get me fired?"

At that point, this stops being an agent-prompting problem and becomes an authorization problem.

## Cloud scale policy

Everything I've described so far works for my setup. I'm running my own agent, the MCP server and tools are on my local machine, and I'm right there to troubleshoot when things go wrong.

When you're running agents at cloud scale, connected to MCP servers that are also running at cloud scale, the problem gets harder to manage. You can't just SSH in and check the logs when something goes sideways. And it's not just your job on the line anymore. It's potentially everyone's.

[Amazon Bedrock AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html) provides a managed layer for exposing tools to agents, including discovery, authentication controls, and MCP-based access. But the feature that matters for this conversation is [Policy in AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/use-gateway-with-policy.html), which lets you apply [Cedar policies](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-understanding-cedar.html) in front of tool calls made through the Gateway.

Cedar is a policy language built for authorization decisions. Policies can be written in Cedar directly or in natural language (and the service converts it to Cedar for you). This means you can be much more fine-grained than a simple `don't get me fired list`. You can set conditions on specific parameters of specific tools.

Say you want to allow an agent to process refunds, but only when the amount is below a certain threshold. Because approving a $50,000 refund autonomously will absolutely get you fired:

```
// The "dont_get_me_fired" policy
permit(
    principal is AgentCore::OAuthUser,
    action == AgentCore::Action::"RefundTool__process_refund",
    resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:123456789:gateway/refund-gw"
)
when {
    context.input.amount < 500
};
```

The default behaviour is deny-all. Nothing gets through unless you explicitly permit it. And `forbid` policies override `permit` policies, so you can set hard boundaries that no other policy can override. You could write a single `forbid` rule that blocks certain actions globally, and no amount of `permit` policies can overrule it. Think of it as the corporate equivalent of "this will get everyone fired, no exceptions."

This is the same principle as the hook-based `don't get me fired list`, just running at a different layer of the stack. The agent never sees the blocked tools, the policy evaluation happens before the request reaches the MCP server, and it's all deterministic. No model reasoning involved.

## Layers

![Shrek layers meme](/assets/images/mcp-tool-protection/layers.jpeg)

Here's how I think about it. Trust with agentic AI isn't binary, and it shouldn't be built all at once. You earn it incrementally, the same way you would with a new team member.

For my own setup, I use three layers:

1. **System prompt** sets the behavioural expectation. The agent knows what it should and shouldn't do, and it knows not to get me fired. This handles lots of cases because the model is generally good at following instructions.

2. **Deterministic hooks** catch the small number of cases where the model tries something it shouldn't. No reasoning, no judgement calls, just a hard block on tools that aren't in `tools_that_will_not_get_me_fired`.

3. **Steering** adds contextual evaluation for tools that are conditionally allowed. The LLM judge asks "will this get me fired?" before every tool call, and blocks anything that fails the vibe check.

For cloud-scale deployments, AgentCore Gateway with Cedar policies replaces layers 2 and 3 with the `dont_get_me_fired` policy: centrally managed, fine-grained authorization that your operations team can audit and update without touching agent code.

The industry data backs this up. According to the [2026 State of Agentic AI report from Nylas](https://www.nylas.com/blog/the-state-of-agentic-ai-in-2026/), only 4% of teams allow agents to act without any human approval. Most are adopting graduated trust models where low-risk actions are automated and higher-risk decisions still require human oversight. That's not a lack of confidence in the technology. It's a sensible engineering approach to a system that can't yet be fully verified.

Whether you're protecting your company's reputation or your own, building trust with agentic AI comes down to one principle: don't rely on the model to police itself. Set the expectations in the prompt, enforce the boundaries in code, and add contextual evaluation where the rules aren't black and white. Your agent can reason about what to do. It shouldn't have to reason about what it's allowed to do.

My agent still has access to my email. I'm still employed. Those two facts are not unrelated.

If you're building agents that touch real-world systems and want to swap notes on keeping your job, find me on [linkedin.com/in/mikegchambers](https://www.linkedin.com/in/mikegchambers).
