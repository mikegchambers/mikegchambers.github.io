---
title: "Streaming Agents on AWS"
date: 2025-12-09
categories: [AI, Agents]
tags: [agents, streaming, amazon-bedrock, api-gateway, cognito, cdk, security]
description: "Deploy streaming AI agents on AWS with API Gateway, Cognito auth, and AgentCore Runtime for real-time responses with enterprise-grade security."
---

> This article was originally published on the [AWS Builder Center](https://builder.aws.com/content/34MfVfB260mYD9XCqluhtT0bGZD/streaming-agents-on-aws).

![Streaming Agents](https://prod-assets.cosmic.aws.dev/a/36bldK3ZPhPrxZbXxgJ4BeNJPpO/Gemi.webp?imgSize=1000x376)

You've built an agent that streams responses beautifully in development. Now you're ready to deploy to production, and you're thinking about security, rate limiting, and authentication.

Just like you'd put your website behind a CDN or gateway, your agent deserves the same protection. Here's how to deploy streaming agents with API Gateway while maintaining that smooth, real-time user experience.

**This is Part 1 of a two-part series.** This post covers the architecture and key concepts. For the complete implementation with CDK code and deployment steps, see [Part 2: Complete Tutorial](https://builder.aws.com/content/34MfVfB260mYD9XCqluhtT0bGZD/api-gateway-streaming-runtime-tutorial.md)[.](https://builder.aws.com/content/36blrJj0hEhsyPWbrxJdmpOIaCu/complete-tutorial-streaming-agents-on-aws)

* * *

The Challenge
-------------

Production agents need robust protection: rate limiting to prevent abuse, WAF to block attacks, authentication to validate users, and API keys for access control. API Gateway provides all of this.

The traditional approach has been to choose between two options:

1.   **Expose Runtime directly** — This works but requires building security logic into your agent code, and you're vulnerable if a bad actor connects.
2.   **Skip streaming entirely** — This is fine for background tasks, but for interactive chatbots where users are waiting, a 30+ second delay creates a poor experience.

The good news? [API Gateway now supports response streaming](https://aws.amazon.com/about-aws/whats-new/2025/11/api-gateway-response-streaming-rest-apis/), so you can have both enterprise-grade protection and real-time streaming. This post shows you how to set it up.

* * *

The Right Architecture
----------------------

Here's what you need:

1.   **Cognito User Pool** for OAuth2/JWT authentication
2.   **AgentCore Runtime** with JWT authorizer (using Cognito)
3.   **API Gateway** with streaming enabled (pointing to Runtime, using Cognito for auth)
4.   **ResponseTransferMode: STREAM** (the key configuration that enables streaming)

The flow looks like this:

`12345User → Cognito (get ID token)      → API Gateway (validate token, stream enabled)     → Runtime /invocations endpoint (validate token again, stream response)     → Agent (async generator)     → Stream back through the chain`

* * *

The Four Critical Pieces
------------------------

### 1. Use ID Tokens, Not Access Tokens

API Gateway Cognito authorizers expect **ID tokens** (which contain user identity claims like `sub`), not access tokens. Your client needs to send:

`1Authorization: Bearer <id_token>`

Both API Gateway and AgentCore Runtime will validate this token. Defense in depth.

### 2. Use the /invocations Endpoint

The `/invocations` endpoint is the OAuth2 endpoint on AgentCore Runtime. It's specifically designed to:

*   Accept JWT ID tokens in the Authorization header
*   Validate tokens using the authorizer you configured
*   Stream responses using the async generator pattern
*   Handle long-running operations with extended timeouts

The endpoint looks like this:

`1https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{runtime_id}/invocations?qualifier=DEFAULT&accountId={account}`

Other endpoints might not support streaming or might require different authentication. This is the one that works.

### 3. Enable ResponseTransferMode: STREAM

API Gateway buffers responses by default, so you need to explicitly enable streaming mode:

`123# The escape hatch (CDK doesn't expose this directly yet)cfn_method = post_method.node.default_childcfn_method.add_property_override("Integration.ResponseTransferMode", "STREAM")`

Without this configuration, API Gateway will buffer the entire response before sending it to the client, which prevents streaming from working.

### 4. Return an Async Generator

Your agent code needs to return an async generator, not a complete response:

`123456@app.entrypointasync def invoke(payload, context):    async def generate_stream():        async for chunk in agent.stream_async(prompt):            yield chunk    return generate_stream()`

The runtime detects the async generator and handles the streaming protocol automatically.

* * *

Why This Architecture Works
---------------------------

This approach delivers enterprise-grade protection without sacrificing user experience. You get protection from the WAF, and authentication to validate users, all while maintaining the real-time streaming that keeps users engaged. It's the best of both worlds.

The timeout difference is particularly significant. With streaming, you get up to 15 minutes of execution time, compared to just 29 seconds without it. For agents that make multiple tool calls or process large datasets, streaming enables use cases that simply wouldn't work otherwise.

Beyond streaming, you get the complete API Gateway feature set: all authorizer types (Cognito, Lambda, IAM), request throttling, access logging, TLS/mTLS support, custom domain names, and centralized metrics and observability. Everything you need for production is included.

* * *

Common Mistakes
---------------

While building this architecture, I ran into a few gotchas that cost me some debugging time. Here are the patterns that work and the ones to avoid.

### ❌ Wrong: Forgetting ResponseTransferMode

`123integration = apigw.HttpIntegration(...)post_method = chat_resource.add_method("POST", integration)# Missing the critical line!`

### ✅ Right: Always Set It

`12cfn_method = post_method.node.default_childcfn_method.add_property_override("Integration.ResponseTransferMode", "STREAM")`

### ❌ Wrong: Using the Wrong Endpoint

`12# This won't stream properlywrong_endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{id}/some-path"`

### ✅ Right: Use /invocations

`12# The OAuth2 endpoint that supports streamingcorrect_endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{id}/invocations?qualifier=DEFAULT&accountId={account}"`

### ❌ Wrong: Returning Complete Response

`1234@app.entrypointasync def invoke(payload, context):    result = await agent.run(prompt)    return result  # Won't stream`

### ✅ Right: Return Async Generator

`123456@app.entrypointasync def invoke(payload, context):    async def generate_stream():        async for chunk in agent.stream_async(prompt):            yield chunk    return generate_stream()`

* * *

The Complete Flow
-----------------

Let's walk through what happens when a user interacts with your streaming agent. Understanding this flow helps clarify why each piece of the architecture matters.

It starts with authentication. The user authenticates with Cognito using the OAuth2 flow and receives a JWT ID token. This token contains their identity claims and will be validated at multiple points in the request chain.

When the frontend sends a request to API Gateway, it includes this token in the `Authorization: Bearer <id_token>` header. API Gateway immediately validates the token using its Cognito authorizer—this is the first validation layer. Once validated, API Gateway proxies the request to the AgentCore Runtime OAuth2 endpoint (`/invocations`).

The Runtime doesn't just trust API Gateway. It validates the token again using its own JWT authorizer, providing a second validation layer for defense in depth. With authentication confirmed, the agent executes and returns an async generator.

Now the streaming begins. The Runtime streams chunks back to API Gateway with no buffering. API Gateway, configured with `ResponseTransferMode: STREAM`, passes those chunks directly to the client without buffering. The client displays chunks as they arrive, creating that smooth, real-time experience users expect.

The beauty of this architecture is that streaming happens at every layer: Agent → Runtime → API Gateway → Client. And authentication is validated at both API Gateway and Runtime, giving you robust security without compromising performance.

* * *

Constraints
-----------

### Idle Timeouts

*   **Regional/Private endpoints**: 5-minute idle timeout (no data for 5 minutes = connection closes)
*   **Edge-optimized endpoints**: 30-second idle timeout

Keep your agent generating data regularly, or the connection will drop.

### Bandwidth Limits

*   **First 10MB**: No restrictions
*   **After 10MB**: Limited to 2MB/s

For most agent responses, this won't be an issue.

### What Doesn't Work with Streaming

*   Response transformation with VTL (Velocity Template Language)
*   Integration response caching
*   Content encoding (gzip, etc.)

If you need these features, you'll need to handle them differently.

References
----------

*   [API Gateway Response Streaming Blog Post](https://aws.amazon.com/blogs/compute/building-responsive-apis-with-amazon-api-gateway-response-streaming/)
*   [What's New Announcement](https://aws.amazon.com/about-aws/whats-new/2025/11/api-gateway-response-streaming-rest-apis/)
*   [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
*   [AgentCore Runtime Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)
*   [Full Code Repository](https://builder.aws.com/content/api-gw-sr-runtime/)
