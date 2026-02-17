---
title: "Will Anthropic's MCP work with other LLMs? - YES, with Amazon Bedrock."
date: 2024-12-01
categories: [AI, Tutorials]
tags: [amazon-bedrock, mcp, claude, mistral, video]
description: "Anthropic's Model Context Protocol (MCP) is a new standard for connecting AI assistants to data sources.  In this video I use Amazon Bedrock's Converse API to d"
---

{% include embed/youtube.html id='u6444EjemKo' %}

hello Mike here now a few days ago anthropic launched the model context protocol a completely open-source way to be able to connect clients that use generative capability to tools now there's nothing particularly new about that we've been able to do that for a while but what this does is it standardizes that connection and allows tool makers to live over here and client makers to live over here and it's completely open source which means that you can use this Protocol no matter which model you're using and that's exactly what we're going to do in this video I'm going to create a client that uses different large language models and we'll choose from a number of different large language models and use that to connect to the um resource the tool let's go a little bit into the architecture of how mCP works the mCP is the most efficient way of handling what we do and if you know where that's from then comment below so let's take a look at the overview of how mCP works in this um article that they published when they launched this there are some links through to some resources it also talks about the clawed desktop now the reason why they talk about that is because if we go to the quick 

## Links & Resources

- [Code used in video is here](https://github.com/mikegc-aws/amazon-bedrock-mcp)
- [MCP Launch Post here](https://www.anthropic.com/news/model-context-protocol)
- [MCP Quickstart here](https://modelcontextprotocol.io/quickstart)

