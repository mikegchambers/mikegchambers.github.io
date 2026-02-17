---
title: "Solving LLM Amnesia: Cross Session Memory"
date: 2024-07-18
categories: [AI, Agents]
tags: [agents, amazon-bedrock, rag, memory, video]
description: "(Managed long term memory for Amazon Bedrock is available now in public preview.)"
---

{% include embed/youtube.html id='ZY5WXDDp9g8' %}

hello it's Mike again now in the last video what were we talking about hang on a sec yes we were talking about agents it's really helpful to write things down if you want to remember them and also if you want a really tedious segue into what I want to talk about now which is long-term memory with generative AI specifically with large language models because you see the thing is that large language models don't have any state they don't remember anything so if we're using a chatbot such as this let me introduce myself to the chat bot say hello and then tell it some information about me I like to drink uh tea and take walks on the beach okay so I've given it some information about me um but at no point in this conversation so far has it had to remember anything from earlier on in the conversation but it can do that because as part of the application here we have saved this conversational history so when we type in the next question we have to send this conversational history and the next question into the model so that it knows what we're talking about so what was the first thing I said and it should know yes the first thing I said was hello um list the things that I like and yeah it

## Links & Resources

- [🛠️ Link to code used in this video](https://github.com/build-on-aws/agents-for-amazon-bedrock-sample-feature-notebooks/blob/main/notebooks/preview-agent-long-memory.ipynb)

