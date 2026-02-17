---
title: "Complete Tutorial: Streaming Agents on AWS"
date: 2025-12-09
categories: [AI, Tutorials]
tags: [agents, streaming, amazon-bedrock, lambda, aws-cdk, api-gateway, cognito, authentication]
description: "Step-by-step tutorial for building streaming AI agents on AWS with CDK, API Gateway, Cognito auth, and AgentCore Runtime."
---

> This article was originally published on the [AWS Builder Center](https://builder.aws.com/content/36blrJj0hEhsyPWbrxJdmpOIaCu/complete-tutorial-streaming-agents-on-aws).

**This is Part 2 of a two-part series.** If you haven't read the architecture overview yet, start with [Part 1: Streaming Agents with API Gateway](https://builder.aws.com/content/36blrJj0hEhsyPWbrxJdmpOIaCu/api-gateway-streaming-runtime.md)[to understand the concepts before diving into the implementation.](https://builder.aws.com/content/34MfVfB260mYD9XCqluhtT0bGZD/streaming-agents-on-aws)

This guide walks you through the complete setup: CDK stacks, agent code, authentication flow, and deployment. By the end, you'll have a production-ready streaming agent protected by API Gateway.

Complete code: [on GitHub](https://github.com/mikegc-aws/agentic-examples/tree/master/api-gw-sr-runtime)

* * *

Prerequisites
-------------

*   AWS Account with appropriate permissions
*   AWS CDK installed (`npm install -g aws-cdk`)
*   Python 3.11+ with uv (`pip install uv`)
*   Basic understanding of CDK, API Gateway, and Cognito

* * *

Architecture Overview
---------------------

We'll deploy three CDK stacks in order:

1.   **Cognito Stack**: User Pool for OAuth2/JWT authentication
2.   **Runtime Stack**: AgentCore Runtime with JWT authorizer
3.   **API Gateway Stack**: REST API with streaming enabled

The deployment order matters because each stack depends on outputs from the previous one.

* * *

Project Structure
-----------------

`123456789api-gw-sr-runtime/├── app.py                    # CDK app entry point├── chatbot_spa_cdk/│   ├── chatbot_spa_stack.py  # Cognito + API Gateway│   └── agent_runtime_stack.py # AgentCore Runtime├── agent/│   └── agent.py              # Streaming agent code├── spa/                      # Frontend application└── pyproject.toml`

* * *

Step 1: CDK App Setup
---------------------

The main CDK app orchestrates the three stacks with proper dependencies. The actual implementation includes environment configuration and resource naming:

`1234567891011121314151617181920212223242526272829303132333435363738# app.py (simplified - see repo for full version)from aws_cdk import App, Environmentfrom chatbot_spa_cdk.chatbot_spa_stack import ChatbotSpaStackfrom chatbot_spa_cdk.agent_runtime_stack import AgentRuntimeStackapp = App()# Step 1: Deploy Cognito firstcognito_stack = ChatbotSpaStack(    app, "ChatbotCognitoStack",    resource_prefix="chatbot-spa",    backend_url=None,  # Skip API Gateway for now    callback_url="http://localhost:3000/callback.html",    env=env)# Step 2: Deploy Runtime with Cognito referencesruntime_stack = AgentRuntimeStack(    app, "ChatbotAgentRuntimeStack",    resource_prefix="chatbot-spa",    user_pool=cognito_stack.user_pool,    user_pool_client=cognito_stack.user_pool_client,    env=env)runtime_stack.add_dependency(cognito_stack)# Step 3: Deploy API Gateway pointing to Runtimeapi_stack = ChatbotSpaStack(    app, "ChatbotApiGatewayStack",    resource_prefix="chatbot-spa",    backend_url=runtime_stack.runtime_endpoint,    existing_user_pool=cognito_stack.user_pool,    existing_user_pool_client=cognito_stack.user_pool_client,    env=env)api_stack.add_dependency(runtime_stack)app.synth()`

**Key points**:

*   Cognito deploys first (no dependencies)
*   Runtime depends on Cognito (needs User Pool for JWT validation)
*   API Gateway depends on Runtime (needs endpoint URL)
*   The `resource_prefix` parameter makes resources easily identifiable in the console

* * *

Step 2: Cognito Stack
---------------------

The Cognito configuration is part of the `ChatbotSpaStack`. When deployed without a `backend_url`, it creates just the User Pool:

`123456789101112131415161718192021222324252627282930313233343536373839404142434445464748495051525354555657585960# From chatbot_spa_cdk/chatbot_spa_stack.py (simplified)from aws_cdk import Stack, Durationfrom aws_cdk import aws_cognito as cognitoclass ChatbotSpaStack(Stack):    def __init__(self, scope, construct_id, resource_prefix, callback_url, **kwargs):        super().__init__(scope, construct_id, **kwargs)                # Create User Pool        user_pool = cognito.UserPool(            self,            "UserPool",            user_pool_name=f"{resource_prefix}-user-pool",            self_sign_up_enabled=False,            sign_in_aliases=cognito.SignInAliases(email=True),            auto_verify=cognito.AutoVerifiedAttrs(email=True),            password_policy=cognito.PasswordPolicy(                min_length=8,                require_uppercase=True,                require_lowercase=True,                require_digits=True,                require_symbols=False,            ),        )                # Enable Managed Login UI (Essentials tier)        cfn_user_pool = user_pool.node.default_child        cfn_user_pool.add_property_override("UserPoolTier", "ESSENTIALS")                # Add domain for hosted UI        user_pool_domain = user_pool.add_domain(            "UserPoolDomain",            cognito_domain=cognito.CognitoDomainOptions(                domain_prefix=f"{resource_prefix}-{self.account}",            ),        )                # Create OAuth2 client        user_pool_client = user_pool.add_client(            "UserPoolClient",            user_pool_client_name=f"{resource_prefix}-client",            generate_secret=False,  # Public client for web apps            o_auth=cognito.OAuthSettings(                flows=cognito.OAuthFlows(authorization_code_grant=True),                scopes=[                    cognito.OAuthScope.OPENID,                    cognito.OAuthScope.EMAIL,                    cognito.OAuthScope.PROFILE,                ],                callback_urls=[callback_url, "http://localhost:3000"],                logout_urls=["http://localhost:3000"],            ),            refresh_token_validity=Duration.days(30),            access_token_validity=Duration.minutes(60),            id_token_validity=Duration.minutes(60),        )                # Export for other stacks        self.user_pool = user_pool        self.user_pool_client = user_pool_client`

**Configuration details**:

*   **self_sign_up_enabled=False**: Prevents public registration (you control who gets access)
*   **sign_in_aliases**: Users sign in with email addresses
*   **generate_secret=False**: Public client (web apps can't keep secrets)
*   **authorization_code_grant**: Standard OAuth2 flow for web applications
*   **OPENID scope**: Required for ID tokens
*   **callback_urls**: Where Cognito redirects after authentication

**What you get**:

*   User Pool that issues JWT ID tokens
*   Hosted UI for authentication (optional, you can build your own)
*   OAuth2 client configured for web applications

* * *

Step 3: AgentCore Runtime Stack
-------------------------------

Deploy your agent to AgentCore Runtime with JWT authorization. The actual implementation uses `CfnResource` and includes bundling logic for dependencies:

`1234567891011121314151617181920212223242526272829303132333435363738394041424344454647484950515253545556575859606162636465666768# From chatbot_spa_cdk/agent_runtime_stack.py (simplified)from aws_cdk import Stack, CfnResourcefrom aws_cdk.aws_s3_assets import Assetclass AgentRuntimeStack(Stack):    def __init__(self, scope, construct_id, user_pool, user_pool_client,                  resource_prefix, **kwargs):        super().__init__(scope, construct_id, **kwargs)                # Package agent code with dependencies        # (See repo for full bundling configuration)        agent_asset = Asset(            self,            "AgentCodeAsset",            path="./agent",            # bundling configuration omitted for brevity        )                # Build Cognito OIDC discovery URL        discovery_url = (            f"https://cognito-idp.{self.region}.amazonaws.com/"            f"{user_pool.user_pool_id}/.well-known/openid-configuration"        )                # Create runtime using CfnResource (Layer 1 construct)        runtime_name = resource_prefix.replace("-", "_") + "_agent_runtime"                runtime = CfnResource(            self,            "AgentCoreRuntime",            type="AWS::BedrockAgentCore::Runtime",            properties={                "AgentRuntimeName": runtime_name,                "Description": f"Runtime for {resource_prefix} with streaming",                "RoleArn": runtime_role.role_arn,  # IAM role created separately                "NetworkConfiguration": {                    "NetworkMode": "PUBLIC",                },                "AuthorizerConfiguration": {                    "CustomJWTAuthorizer": {                        "DiscoveryUrl": discovery_url,                        "AllowedAudience": [user_pool_client.user_pool_client_id],                    }                },                "AgentRuntimeArtifact": {                    "CodeConfiguration": {                        "Code": {                            "S3": {                                "Bucket": agent_asset.s3_bucket_name,                                "Prefix": agent_asset.s3_object_key,                            }                        },                        "EntryPoint": ["agent.py"],                        "Runtime": "PYTHON_3_12",                    }                },            },        )                # Build the OAuth2 endpoint URL        runtime_id = runtime.ref        runtime_endpoint = (            f"https://bedrock-agentcore.{self.region}.amazonaws.com/"            f"runtimes/{runtime_id}/invocations"            f"?qualifier=DEFAULT&accountId={self.account}"        )                self.runtime_endpoint = runtime_endpoint`

**Critical details**:

*   **CustomJWTAuthorizer**: Uses OIDC discovery to validate ID tokens from Cognito
*   **DiscoveryUrl**: Points to Cognito's OIDC configuration endpoint
*   **AllowedAudience**: The User Pool Client ID (ID tokens must have this in their `aud` claim)
*   **/invocations endpoint**: The OAuth2 endpoint that supports streaming
*   **qualifier=DEFAULT**: Uses the default runtime version
*   **accountId**: Required for cross-account access control
*   **CfnResource**: Used because CDK doesn't have L2 constructs for AgentCore yet

**What happens**:

*   Runtime validates every request's JWT ID token
*   Invalid or missing tokens are rejected with 401
*   Valid tokens allow the request to proceed to your agent

* * *

Step 4: API Gateway Stack
-------------------------

Create the REST API with streaming enabled:

`12345678910111213141516171819202122232425262728293031323334353637383940414243444546474849505152535455from aws_cdk import Durationfrom aws_cdk import aws_apigateway as apigwclass ApiGatewayStack(Stack):    def __init__(self, scope, construct_id, runtime_endpoint, user_pool, **kwargs):        super().__init__(scope, construct_id, **kwargs)                # Create REST API        api = apigw.RestApi(            self,            "Api",            rest_api_name="agent-api",            default_cors_preflight_options=apigw.CorsOptions(                allow_origins=["http://localhost:3000"],                allow_methods=["POST", "OPTIONS"],                allow_headers=["Content-Type", "Authorization"],            ),        )                # Cognito authorizer        authorizer = apigw.CognitoUserPoolsAuthorizer(            self,            "CognitoAuthorizer",            cognito_user_pools=[user_pool],        )                # HTTP Proxy Integration        integration = apigw.HttpIntegration(            runtime_endpoint,  # The OAuth2 endpoint from Runtime Stack            http_method="POST",            proxy=True,            options=apigw.IntegrationOptions(                connection_type=apigw.ConnectionType.INTERNET,                timeout=Duration.seconds(900),  # 15 minutes with streaming                request_parameters={                    "integration.request.header.Authorization":                         "method.request.header.Authorization",                },            ),        )                # Add method        chat_resource = api.root.add_resource("chat")        post_method = chat_resource.add_method(            "POST",            integration,            authorizer=authorizer,            authorization_type=apigw.AuthorizationType.COGNITO,        )                # CRITICAL: Enable streaming with escape hatch        cfn_method = post_method.node.default_child        cfn_method.add_property_override("Integration.ResponseTransferMode", "STREAM")                self.api_url = api.url`

**Why the escape hatch?**

CDK's `HttpIntegration` doesn't expose `ResponseTransferMode` directly yet. The escape hatch lets you set it on the underlying CloudFormation resource.

**What this does**:

*   API Gateway validates the JWT ID token (first layer of defense)
*   Forwards the Authorization header to Runtime (second layer of defense)
*   Streams the response instead of buffering it
*   Allows up to 15 minutes for the request to complete

**CORS configuration**:

*   Allows requests from your frontend origin
*   Includes Authorization header in allowed headers
*   Handles preflight OPTIONS requests

* * *

Step 5: Agent Implementation
----------------------------

This example uses two SDKs to simplify development:

*   [Strands Agents SDK](https://github.com/awslabs/strands-agents): A Python framework for building agentic workflows with streaming support built-in
*   [Amazon Bedrock AgentCore SDK](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html): Handles the AgentCore Runtime integration and streaming protocol

Both SDKs are optional. You can build agents with any framework that returns async generators, but these make it much easier to get up and running quickly for this demo.

Your agent code needs to return an async generator for streaming:

`12345678910111213141516171819202122232425262728293031323334# agent/agent.pyfrom bedrock_agentcore.runtime import BedrockAgentCoreAppfrom strands import Agentfrom strands_tools import calculatorapp = BedrockAgentCoreApp()# Lazy load agent for performance_agent = Nonedef get_agent():    global _agent    if _agent is None:        _agent = Agent(            system_prompt="You are a helpful assistant that can perform calculations.",            tools=[calculator]        )    return _agent@app.entrypointasync def invoke(payload, context):    """Entry point that returns an async generator for streaming"""    agent = get_agent()    prompt = payload.get("prompt", "Hello!")        # Return an async generator    async def generate_stream():        agent_stream = agent.stream_async(prompt)        async for event in agent_stream:            if "data" in event:                yield event["data"]            # You can also handle tool use events here if needed        return generate_stream()`

**How it works**:

*   `BedrockAgentCoreApp` detects when you return an async generator
*   It handles the streaming protocol automatically
*   Each `yield` sends a chunk to the client immediately
*   The stream flows: Agent → Runtime → API Gateway → Client

**Why lazy load the agent?**

The runtime reuses the same container across invocations, which means the agent instance stays in memory. This is crucial for maintaining conversation context and history between requests. By lazy loading, you initialize the agent once and it persists across all subsequent invocations, allowing multi-turn conversations to work naturally.

**Agent requirements**:

`123456789# agent/pyproject.toml[project]name = "streaming-agent"version = "0.1.0"dependencies = [    "bedrock-agentcore-runtime",    "strands",    "strands-tools",]`

* * *

Step 6: Frontend Implementation
-------------------------------

Handle streaming on the client side:

`1234567891011121314151617181920212223242526272829303132333435363738// Get ID token from Cognito (after OAuth2 flow)const idToken = sessionStorage.getItem('id_token');async function sendMessage(prompt) {    const response = await fetch(        'https://your-api.execute-api.us-west-2.amazonaws.com/chat',        {            method: 'POST',            headers: {                'Authorization': `Bearer ${idToken}`,                'Content-Type': 'application/json',            },            body: JSON.stringify({ prompt }),        }    );        // Read the stream    const reader = response.body.getReader();    const decoder = new TextDecoder();    let buffer = '';        while (true) {        const { done, value } = await reader.read();        if (done) break;                // Decode chunk (may contain partial UTF-8 sequences)        buffer += decoder.decode(value, { stream: true });                // Display immediately        appendToMessage(buffer);        buffer = '';    }        // Flush any remaining buffer    if (buffer) {        appendToMessage(buffer);    }}`

**Important**: Use `{ stream: true }` in `TextDecoder.decode()`. This handles partial UTF-8 sequences that can occur at chunk boundaries.

**OAuth2 flow** (simplified):

`1234567891011121314151617181920212223242526272829303132333435363738394041// Redirect to Cognito for authenticationfunction login() {    const cognitoDomain = 'https://agent-123456789.auth.us-west-2.amazoncognito.com';    const clientId = 'your-client-id';    const redirectUri = 'http://localhost:3000/callback.html';        window.location.href =         `${cognitoDomain}/oauth2/authorize?` +        `client_id=${clientId}&` +        `response_type=code&` +        `scope=openid+email&` +        `redirect_uri=${encodeURIComponent(redirectUri)}`;}// Handle callback (in callback.html)async function handleCallback() {    const params = new URLSearchParams(window.location.search);    const code = params.get('code');        // Exchange code for tokens    const response = await fetch(        `${cognitoDomain}/oauth2/token`,        {            method: 'POST',            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },            body: new URLSearchParams({                grant_type: 'authorization_code',                client_id: clientId,                code: code,                redirect_uri: redirectUri,            }),        }    );        const tokens = await response.json();    sessionStorage.setItem('id_token', tokens.id_token);    sessionStorage.setItem('access_token', tokens.access_token);        // Redirect back to app    window.location.href = '/';}`

* * *

Deployment
----------

Deploy the stacks in order:

`1234567891011121314cd api-gw-sr-runtime# Bootstrap CDK (first time only)export AWS_PROFILE=your-profileuv run cdk bootstrap# Deploy all stacksuv run cdk deploy --all# Update frontend config with API URL./update-spa-config.sh# Create a test user./create-test-user.sh testuser@example.com TestPassword123!`

**What happens**:

1.   Cognito stack deploys (User Pool + Client)
2.   Runtime stack deploys (references Cognito)
3.   API Gateway stack deploys (references Runtime endpoint)
4.   Scripts configure frontend and create test user

* * *

Testing
-------

### Test with curl

`123456789# Get your ID token (from browser sessionStorage or Cognito)ID_TOKEN="eyJraWQiOi..."# Test with -N flag for no bufferingcurl -N -X POST \  https://your-api.execute-api.us-west-2.amazonaws.com/chat \  -H "Authorization: Bearer $ID_TOKEN" \  -H "Content-Type: application/json" \  -d '{"prompt":"What is 25 * 4? Show your work."}'`

You should see the response appear incrementally, not all at once.

### Test with frontend

`12cd spapython -m http.server 3000`

Open http://localhost:3000, log in, and send a message. You should see the response stream in real-time.

* * *

Troubleshooting
---------------

### Streaming not working (response appears all at once)

Check:

*   Is `ResponseTransferMode: STREAM` set on the API Gateway method?
*   Are you using the `/invocations` endpoint?
*   Is your agent returning an async generator?

### 401 Unauthorized

Check:

*   Is the ID token valid? (Check expiration)
*   Is the token in the Authorization header?
*   Does the JWT authorizer configuration match your Cognito User Pool?
*   Are you using the ID token (not access token)?

### 502 Bad Gateway

Check:

*   Is the Runtime endpoint URL correct?
*   Does the Runtime have the JWT authorizer configured?
*   Is the agent code deployed correctly?

### Connection drops after 30 seconds

You're using an edge-optimized endpoint. Switch to regional:

`123456api = apigw.RestApi(    self,    "Api",    endpoint_types=[apigw.EndpointType.REGIONAL],  # Add this    ...)`

### Agent not streaming

Check:

*   Is your agent returning an async generator?
*   Are you yielding chunks, not returning a complete response?
*   Is the agent actually generating data? (Add logging)

* * *

Performance Optimization
------------------------

### Lazy Load Your Agent

`1234567_agent = Nonedef get_agent():    global _agent    if _agent is None:        _agent = Agent(...)  # Only initialize once    return _agent`

The runtime reuses the same container across invocations, lazy loading keeping the agent instance in memory. This allows the agent to maintain conversation history and context between requests, enabling natural multi-turn conversations without needing external storage.

Full Code Repository
--------------------

Complete code: [on GitHub](https://github.com/mikegc-aws/agentic-examples/tree/master/api-gw-sr-runtime)

Includes:

*   All CDK stacks
*   Agent implementation
*   Frontend with OAuth2
*   Deployment scripts
*   Test utilities

References
----------

*   [API Gateway Response Streaming Blog Post](https://aws.amazon.com/blogs/compute/building-responsive-apis-with-amazon-api-gateway-response-streaming/)
*   [What's New Announcement](https://aws.amazon.com/about-aws/whats-new/2025/11/api-gateway-response-streaming-rest-apis/)
*   [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
*   [AgentCore Runtime Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)
*   [Cognito Documentation](https://docs.aws.amazon.com/cognito/)
*   [CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/)
