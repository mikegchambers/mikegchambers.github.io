---
title: "Mistral AI - Winds of Change"
date: 2024-02-26
categories: [AI, Models]
tags: [mistral, amazon-bedrock, inference, generative-ai, llm, mixtral]
description: "Explore Mistral 7B and Mixtral 8x7B architecture, grouped-query attention, sliding window attention, and how to run them on Amazon Bedrock."
---

> This article was originally published on the [AWS Builder Center](https://builder.aws.com/content/2cZUf75V80QCs8dBAzeIANl0wzU/mistral-ai-winds-of-change).

_**UPDATE:** Mistral AI Models are now LIVE on Amazon Bedrock, so the end of this post has been updated to show how to enable them. Happy prompting!_

_**UPDATE 2**: Since this post was written another model, Mistral Large,_[_has launched on Amazon Bedrock_](https://www.aboutamazon.com/news/aws/mistral-ai-mistral-large-amazon-bedrock)_._

Let's talk about two of the prominent large language models at the moment, [Mistral 7B](https://mistral.ai/news/announcing-mistral-7b/)and [Mixtral 8x7B](https://mistral.ai/news/mixtral-of-experts/), that have [just launched on Amazon Bedrock](https://aws.amazon.com/blogs/aws/mistral-ai-models-coming-soon-to-amazon-bedrock/). In this post I will cover, where these models came from, what stands out about the way they work, and finish up reviewing some ways you can run them, including in production. 

These models are designed and produced by Mistral AI, specifically with developers in mind. Mistral AI is a small French startup with a core team of scientists, driven on the purpose of "shipping things that work" rather than writing white papers. And I thank them for this!

_(Quick one paragraph diversion:)_ The name stems from "mistral", the wind, that according to Wikipedia "is usually accompanied by clear, fresh weather, and it plays an important role in creating the climate of Provence". It is French, and contains the vowels I and A that match "intelligence artificielle" which I am sure you realise translates to the English "artificial intelligence". But enough with such trivialities, let's dive into the technology. 

Mistral's founders [Arthur Mensch](https://www.linkedin.com/in/arthur-mensch/), [Guillaume Lample](https://www.linkedin.com/in/guillaume-lample-7821095b/) and [Timothée Lacroix](https://www.linkedin.com/in/timothee-lacroix-59517977/) have significant experience in the field is AI/ML, with Arthur having been intimately involved with the famous "[Chinchilla Paper](https://arxiv.org/pdf/2203.15556.pdf)" that at the time provided the world with the understanding of transformer model scaling laws. In other words how to scale models between compute resources, dataset token size, and model parameters, providing a framework for efficiently training large language models while optimising their performance. And through this and other research, the team thought they could achieve better results than what was available, not by going bigger, but by optimising, and in the first instance anyway, going smaller. 

Introducing Mistral 7B
----------------------

In September 2023 Mistral AI released Mistral 7B, a 7 billion parameter large (but not that large) language model (LLM). And following along with so many other LLMs before it, Mistral 7B is a transformer based decoder model. According to it's [white paper](https://arxiv.org/pdf/2310.06825.pdf), at the time, "Mistral 7B outperforms the best open 13B model (Llama 2) across all evaluated benchmarks, and the best released 34B model (Llama 1) in reasoning, mathematics, and code generation." It does this, in part, by leveraging "grouped-query attention (GQA) for faster inference, coupled with sliding window attention (SWA) to effectively handle sequences of arbitrary length with a reduced inference cost." 

(To be clear, Llama2 also uses GQA, but it does not use SWA.)

### What is Grouped-Query Attention (GQA)?

To explain what is going on, let's delve a little into the architecture of a transformer based decoder model.

One of the significant breakthroughs in the development of transformer based LLMs is the use of a multi-headed self attention architecture. This architecture enables the model to learn information about the relationships between all the words (tokens) in the input sequence. In other words from the sentence "I have an ice-cream to give to you", the self attention architecture gives the model a chance of learning that one person has an ice-cream, and the other does not. The word 'ice-cream' will likely 'attend' to 'I'. 

_Here is the attention visualization from the original "_[_Attention is all you need_](https://arxiv.org/pdf/1706.03762.pdf)_" paper Vaswani, et al that proposed the approach._

![Attention Visualization](https://assets.community.aws/a/2ctMFpYiaDyYx2asvsdPZTJXm9U/atte.webp)

We don't need to dive deep here, but understand that in order to learn these relationships, large and complex matrix multiplications are performed across 3 parameters called, keys (K), values (V) and queries (Q). That's as deep as we need to go, just know that in order to perform these calculations we need to process and store a great many numbers, or parameters. The exact number of parameters depends on the implementation of the model, there are multiple heads (it was in the name "multi-headed self attention"), where each head will attempt to learn some different characteristic about the relationship between the words in the input sequence, and these heads are stacked in multiple layers. By way of example, both Mistral and Llama2 have 32 self attention heads, across 32 layers, so 32 x 32, thats 1024 heads, each head has 10s or 100s of thousands of parameters, now you can see why these models end up with billions of parameters. 

_The following diagram is from "_[_Grouped Attention from "GQA: Training Generalized Multi_](https://arxiv.org/pdf/2305.13245.pdf)_" Ainslie et al._

![Grouped Attention](https://assets.community.aws/a/2ctOAIeZRCQW1gOKXSqE9PxkSBi/grou.webp)

Above, I mentioned that attention is calculated via keys (K), values (V) and queries (Q). And a little earlier I mentioned that Mistral 7B uses a technique called grouped-query attention or GQA. We now have the background to describe this. In an original design, each set of self attention calculations, had its own K, V, and Q values. A method was then devised called multi-query attention (MQA), that shares single K and V values across all Q in a layer. This method drastically reduces the number of parameters that need to be stored, which is great, but also results in reduced model quality - the generations were just not as good. Grouped-query attention shares K and V across a configurable number of Q, thus striking a balance between the number of parameters stored and the performance of the model. And in [the paper that introduced this method](https://arxiv.org/pdf/2305.13245.pdf), the authors proposed that they "show that uptrained GQA achieves quality close to multi-head attention with comparable speed to MQA." Winner! 

As the Mistral 7B paper says "GQA significantly accelerates the inference speed (this is how fast the model generates output), and also reduces the memory requirement during decoding, allowing for higher batch sizes hence higher throughput, a crucial factor for real-time applications."

### What is Sliding Window Attention (SWA)?

The longer a model's context is, arguably the more useful it is. Imagine the difference between summarising a page of text with 1000 words, vs summarising a whole book with 100k words.

In the previous section I introduced the concept of self attention, and how each word (token) can attend to each other word. And in a traditional transformer model, that's how the attention mechanism works, allowing each and every word to interact with each and every other word in the input sequence. This process is really powerful for capturing relationships and context, but becomes computationally expensive as the sequence length grows, with the number of calculations growing quadratically. 

_The following diagram illustrates SWA and is from the "_[_Mistral 7B_](https://arxiv.org/pdf/2310.06825.pdf)_" paper Q et al._

![Sliding Window Attention](https://assets.community.aws/a/2ctPC5RFe6x71Yw8XbZPUy5sDZf/Slid.webp)

Sliding window attention (SWA) introduces a configurable sized "attention window" that passes over the input sequence, so that rather than calculate attention values (weights) for all the text, it just calculates these values for the words that fall within the window. This reduces the number of calculations required. One concern may be that this will mean that over long sequences, the final tokens in a sequence will not "attend" to the first tokens. While this is strictly true, tokens beyond the initial window size are still influenced by the earlier tokens in the input sequence, as the window pushes a "wave of influence" over the context drawing with it the contextual meaning of the sequence as it goes. And this cascades through all the layers in the model. 

As the Mistral 7B paper says "SWA is designed to handle longer sequences more effectively at a reduced computational cost, thereby alleviating a common limitation in LLMs. " Together with GQA "These attention mechanisms collectively contribute to the enhanced performance and efficiency of Mistral 7B."

### Introducing Mixtral 8x7B

In December 2023 Mistral AI released Mixtral 8x7B, a 47 billion parameter (I'll explain the maths in a moment) sparse mixture of experts model. Interestingly this model shares the same architecture as Mistral 7B, even [the repository](https://github.com/mistralai/mistral-src) is the same, and adds a small amount of code, that makes a massive difference. According to the white paper, at the time Mixtral "outperforms or matches Llama 2 70B and GPT-3.5 across all evaluated benchmarks. In particular, Mixtral vastly outperforms Llama 2 70B on mathematics, code generation, and multilingual benchmarks."

So what makes Mixtral 8x7B special?

### What is a sparse Mixture of Experts (MoE) model?

So far in this post we have discussed the multi-headed self attention mechanism within layers of the model. Another component that lives within this layer is a "feed forward network" (FFN). The role of the FFN is to perform an additional layer of transformation on the data capturing even more intricate patterns, enhancing the model's ability to learn and understand the semantics of language.

Remember that each self attention head attempts to learn some different characteristic about the relationship between the words in the input sequence? Well what if we introduce multiple FFNs too, so that each one could also learn something different about language. You might say that these FFNs would become "experts" in some aspect of language (you might not say that, but you've been outvoted!).

Simply adding more FFNs into the layer will increase the size and complexity of the model, when we could just make the FFN bigger and maybe get the same result without the complexity. So why go to this effort? The answer is "sparsity". Whenever you talk about Mixtral, remember it is a "sparse" mixture of experts model. 

_The following diagram shows the router/gate from the "_[_Mixtral of Experts_](https://arxiv.org/pdf/2401.04088.pdf)_" paper Q et al._

![Mixture of Experts Layer](https://assets.community.aws/a/2ctPotFUB0iBpP1DYDlqeaIVfjp/m-o-.webp)

Before the expert FFNs in the layer, there is a router/gate mechanism that learns and then decide which configurable number (one or more) experts will perform best on the word (token) that is being passed in. And this can be different for each token in the sequence. As the paper says "For every token, at each layer, a router network selects two experts to process the current state and combine their outputs. Even though each token only sees two experts, the selected experts can be different at each timestep." This means that for any word (token) that gets passed through the whole network, only a subset of the network is used. This is sparse activation, and means that the network is more efficient. "As a result, each token has access to 47B parameters, but only uses 13B active parameters during inference." "This technique increases the number of parameters of a model while controlling cost and latency, as the model only uses a fraction of the total set of parameters per token."

And as for accuracy? According to Mistrals research this model "outperforms or matches Llama 2 70B and GPT-3.5 (larger models) across all evaluated benchmarks" 

_Maths bit:_ As the name may suggest Mixtral 8x7B has 8 experts per layer. And now we know that this is not 8 times the whole network, and 'just' the FFNs, plus some parameters in the router/gate, it works out that Mixtral 8x7B is not 56 billion parameters (8 x 7 billion), but 46.7B, where only 12.9B get used per token.

### More on Experts

Using a word like "experts" it's easy to anthropomorphise (assign human values) to these "experts" and imagine that they have skills aligned to us. For example, one expert may be good at French, and another may be good at code, etc. In practice this is not the case. In the paper, Mistral notes that "Surprisingly, we do not observe obvious patterns in the assignment of experts based on the topic". And they go on to illustrate the observed assignment of experts.

_The following diagram shows expert assignment as discovered in "Mixtral of Experts" paper, Q et al._

![Expert Assignment](https://assets.community.aws/a/2ctQGhmWk51ghNRYVi7yuEMJzKv/expert-assignment-arxiv-org-pdf-2401-04088-jpg.webp)

In this illustration from the paper, the different colors represent the different experts that the model has learnt to use on each token, for a code sample, a maths sample, and a text sample. The three columns show the difference in expert assignment in different layers of the model. As the caption says "The selection of experts appears to be more aligned with the syntax rather than the domain, especially at the initial and final layers."

How to run Mistral AI models (spoiler: you don't have to)
---------------------------------------------------------

Mistral AI have released [the source code](https://github.com/mistralai/mistral-src) for Mistral 7B and Mixtral 8x7B under the Apache 2.0 licence and say that these models "can be used without restrictions". The weights for these models can also be downloaded from their CDN through [their website](https://mistral.ai/news/announcing-mistral-7b/). 

In Mistral's documentation they show [how to use SkyPilot](https://docs.mistral.ai/self-deployment/skypilot/) to launch the model in the cloud including AWS. They also have instructions on how to launch Mistral models on your own (or cloud) hardware with [vLLM](https://docs.mistral.ai/self-deployment/vllm/).

### Running Mistral Models Locally

Depending on your machine, you may be able to run these models locally, even without a GPU. I run a version of Mistral 7B with great performance, and a version of Mixtral 8x7B in a way that shows that it works. I am running them on a Mac Book Pro M2 with 32 GB of ram, with no special setup, and without quitting other applications fitst! The trick is that a community has grown up around running models locally, where they further "shrink" the models through a process of quantisation. Quantisation takes floating point numbers within the model, e.g. 16-bit floating-point (FP16) precision parameters, and converts them to something smaller such as 8-bit or 4-bit. This drastically reduces the size of the model, the complexity of the calculations required for runtime, and means the models can run on a CPU. Of course there is no free lunch here, and the models loose some precision in the generation, but they still perform okay. The exact process of quantisation is involved and beyond the scope of this post, but luckily for us, the models are already there for use to download.

![Ollama.com](https://assets.community.aws/a/2ctQp4gDLEAvOZcxuTtJOR75GC1/olla.webp)

The [Llama.cpp project](https://github.com/ggerganov/llama.cpp) provides a runtime environment that supports models like Mistral/Mixtral, and the [Ollama project](https://ollama.com/) wraps this up to make it incredibly easy to use. Just download the [model file using Ollama](https://ollama.com/library/mistral), and run it. Done. (MacOS and Linux support is there now, Windows support is on its way.)

Remember though that these are not the full versions of the Mistral AI models, they are quantised with lower precision in the generation. For production you will likely need a better solution. 

### Fully Managed Serverless Production Endpoint (a.k.a. let someone else host the model for you)

![Amazon Bedrock Console Page](https://assets.community.aws/a/2dCdmEkQvHOiKJreX91Uz5sHajq/Scre.webp)

[Amazon Bedrock](https://aws.amazon.com/bedrock) provides a single API endpoint to connect in to a variety of generative AI models from leading AI providers such as AI21 Labs, Anthropic, Cohere, Meta, Stability AI, Amazon, and now Mistral AI. 

To enable access to these models in your AWS account: 

From the AWS console, navigate to the Amazon Bedrock page. Mistral models have launched in Oregon, so make sure to be in the `us-west-2` region, more regions are coming, so check to see if they're now available in another regions:

Expand the menu on the left hand side, scroll down and select "Model access":

![Amazon Bedrock Console Page - Menu](https://assets.community.aws/a/2dCdrRPgmRtOA0xwROIMWICyqSG/Scre.webp)

Select the orange "Manage model access" button, and scroll down to see the new Mistral AI models. If you're happy with the licence, then select the checkboxes next to the models, and click 'Save changes'.

![Amazon Bedrock - Model Access](https://assets.community.aws/a/2dCdxn2E4eBKGEsU0cj0fmMilkY/Scre.webp)

You can now access the models! Head to the Amazon Bedrock text playground to start experimenting with your prompts. When you're ready to write some code, take a look at the code samples we have [here](https://docs.aws.amazon.com/code-library/latest/ug/bedrock-runtime_example_bedrock-runtime_InvokeMistral7B_section.html),and [here](https://docs.aws.amazon.com/code-library/latest/ug/bedrock-runtime_example_bedrock-runtime_InvokeMixtral8x7B_section.html). 

Happy Prompting! 

I am a Senior Developer Advocate for Amazon Web Services, specialising in Generative AI. You can[reach me directly through [LinkedIn](https://linkedin.com/in/mikegchambers), come and connect, and help grow the community.

Thanks - Mike
