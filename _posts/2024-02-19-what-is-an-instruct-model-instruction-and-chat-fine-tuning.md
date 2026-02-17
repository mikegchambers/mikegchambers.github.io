---
title: "What is an instruct model? - Instruction and Chat Fine-Tuning"
date: 2024-02-19
categories: [AI, Models]
tags: [fine-tuning, amazon-bedrock, mistral, claude, llm, generative-ai]
description: "Learn the difference between instruct, chat, and base LLMs. Understand how instruction fine-tuning and chat fine-tuning shape model behavior."
---

> This article was originally published on the [AWS Builder Center](https://builder.aws.com/content/2ZVa61RxToXUFzcuY8Hbut6L150/what-is-an-instruct-model-instruction-and-chat-fine-tuning).

As you browse the ever growing global catalogue of generative AI models, you will see some of the Large Language Models (LLMs) being listed with the suffix 'instruct' or 'chat'. What does this mean?

**TL:DR; The 'instruct' version of the model has been fine-tuned to be able to follow prompted instructions. These models 'expect' to be asked to do something. Models with the 'chat' suffix have been fine-tuned to work in chatbots. These models 'expect' to be involved in a conversation with different actors. In contrast non-instruct tuned models will simply generate an output that follows on from the prompt. If you are making a chatbot, implementing RAG or using agents, use instruct or chat models. If in doubt us an instruct model.**

How LLMs are trained
--------------------

Base models of Large Language Models (LLMs) undergo extensive training on diverse and vast datasets compiled from a wide range of sources available on the Internet. This foundational training involves processing billions of words and texts from books, articles, websites, and other digital content to learn language patterns, grammar, semantics, and general knowledge. The data is supplied to the training process 'as is' without any annotation or labelling. In other words we are saying "here is a bunch of text that represents what language looks like" and we leave it to the model to find patterns and meaning (this is called semi-supervised training). This comprehensive training process enables base models to perform a wide variety of language tasks, from conversational responses to content creation.

When prompted, these base models will calculate tokens (think words) that are statistically likely to follow the prompt. For example, when prompted with "The cat sat on the", the model will likely generate the word "mat". 

`12The cat sat on the> mat`

And when prompted with "What is the capital of Australia?", the model *could* generate "Is a question that people often get wrong." This generation is logical, and correct, but might not be what you wanted.

`12What is the capital of Australia?> Is a question that people often get wrong.`

Instruction Fine-tuning
-----------------------

Fine-tuning is an additional step in the process of creating a model that enhances their ability to perform specific tasks. This process involves taking the pre-trained base model and further training it on a smaller, more specialised dataset relevant to the desired task. This time the data supplied is labeled, with examples of generations for a given prompt. For example we might provide: Prompt: "What is the capital of England?" Generation: "The capital of England is London." (and many other similar examples). The purpose of the training data is NOT to teach the model what the capital of England is, but to teach it that when asked a question, we expect an answer to that question, and the format that we want to see the answer in. The process of fine-tuning adjusts the model's parameters to better align with the nuances and requirements of these task such as quesiton answering, without losing the general language understanding it has already acquired. 

Now, with an instruction fine-tuned model, when we prompt "What is the capital of Australia?" the model *should* answer "The capital of Australia is Canberra."

`12What is the capital of Australia?> The capital of Australia is Canberra.`

Chat Models
-----------

For a model to work well in a chat scenario, they are fine-tuned on what a chat context looks like. The specifics of this fine-tuning is a decision for the developers who design these models. Let's look at Anthropic's Claude model. Claude is trained to be a helpful, honest, and harmless chat based assistant. The fine-tuning of Claude means that the model explicitly expects (requires) our prompt to be delivered in a certain format where we define the 'Human' and the 'Assistant' roles of the chat. For example we could use the following prompt (including the line breaks) with Claude:

`1234Human: What is the capital of Austraila?Assistant:`

Here we denote our input question as being from "Human". In reality this input could come from anywhere including a stored string, another LLM, a human or a parrot. The label "Human" simply denotes one side of the conversation. We also add in the "Assistant" label. This shows Claude that we are ready for the answer. For more details on Claude prompting see [here.](https://docs.anthropic.com/claude/docs/introduction-to-prompt-design)

Other chat model interfaces (via APIs) may even break this string structure down into a structured payload and support more roles including system messages such as this payload for OpenAI based models:

`1234messages=[  {"role": "system", "content": "You are a geography assistant."},  {"role": "user", "content": "What is the capital of Australia?"},]`

Ultimately this format will be converted to to a string prompt and passed to the underlying LLM to process.

Experiment
----------

When selecting a model for your particular application the best way forward is to experiment. Experiment with different prompts, formatted in different ways, that will work with different models for your use case. A super easy way to integrate foundation models in to your own application is through [Amazon Bedrock](https://aws.amazon.com/bedrock/). And the [Bedrock console page](https://console.aws.amazon.com/bedrock/home) has playgrounds that are specifically designed for this type of experimentation.

And (plug time :)) If you want to dive in to Amazon Bedrock and get up and running in a free environment, then check out my course on Deeplearning.ai. Called ["Serverless LLM apps with Amazon Bedrock"](https://learn.deeplearning.ai/serverless-llm-apps-amazon-bedrock)), its designed for you to get hands on with Amazon Bedrock and learn how to deploy a large language model-based application into production using serverless technology.

 ___________________________ 

Mike Chambers is a Senior Developer Advocate for Amazon Web Services, specilaising in the field of generative AI. You can connect with Mike here: https://linkedin.com/in/mikegchambers
