---
title: "Introducing Strands Decider 2B: A Small, Open Source, Decision Model"
date: 2026-10-01
categories: [AI, Agents]
tags: [strands, strands-decider, decision-models, open-source, system-one, agents]
description: "Strands Decider 2B is a small, open source decision model built for fast experimentation, local development, and innovation. A 2B model that picks between options and scores them in tens of milliseconds, with calibrated confidence."
---

> This article was originally published on the [Strands Agents blog](https://strandsagents.com/blog/introducing-strands-decider/). I am one of the authors, along with Marc Brooker and Fabio Nonato de Paula.

![Introducing Strands Decider 2B, a small, open source, decision model](/assets/images/introducing-strands-decider/banner.png)

Earlier this year we announced strands-labs, a place to get hands-on with state-of-the-art approaches to agentic AI. We have now added **Strands Decider 2B**: a small decision model optimised for fast experimentation, local development, and innovation.

Strands Decider is one of a new class of decision models, or "System One" models, a type of model that has been getting a lot of attention. Unlike LLMs that generate arbitrary output, decision models pick between sets of options (for example, "Is the string 'turn on the lights' about the coffee machine? Yes or no.") and assign simple numerical scores. In exchange for that reduction in flexibility, they are faster and more capable at a given size, always produce an answer from the selected options, and run with very low latency.

Each decision also comes with a high-quality reliability score, telling you how sure the model is that an answer is correct, which is not something you get from frontier LLM inference APIs. They also make it efficient to ask several questions about the same prompt. That combination makes them a great fit for the kinds of agentic workflows developers are building with the Strands Harness SDK.

Strands Decider 2B is our first contribution to that space. It is a 2 billion parameter model, suitable for a local CPU or GPU, that returns answers to meaningful questions in tens of milliseconds. Its accuracy and calibration are competitive with the other models we know of in this class. We have released it as open source on GitHub, with the weights on Hugging Face, including the training data and scripts we used to build it.

### How it is built

The core idea: take a pre-trained LLM torso (Qwen3.5-2B) and remove the LM head, taking away its ability to generate text. The LM head is replaced with a small pointer head, just over a million parameters, which scores the answers offered for each option by comparing the hidden state at each option position against the hidden state at the answer position. The torso is fine-tuned with a rank-16 LoRA adapter. The released model is v19, with a lot of iterations under the covers, and every change is covered in the repo so you can follow along.

![The Strands Decider 2B architecture: a Qwen3.5-2B torso with the language model head replaced by a small pointer head that scores each option against the answer position](/assets/images/introducing-strands-decider/architecture.webp)
_The Strands Decider 2B architecture._

### How it performs

For a model like this we care about three things: accuracy (how well it answers), calibration (how trustworthy its confidence scores are), and latency (how quickly it decides). Strands Decider 2B does well on accuracy and calibration, placing third of 33 in the 2B class on JevBench's public set, and first of 30 if you exclude the just-over-2B models.

Read the full announcement, including the architecture details and benchmarks, [on the Strands Agents blog](https://strandsagents.com/blog/introducing-strands-decider/).

*Content was rephrased for compliance with licensing restrictions.*

## Links & Resources

- [📖 Full post on the Strands Agents blog](https://strandsagents.com/blog/introducing-strands-decider/)
- [📚 Strands Agents](https://strandsagents.com)

I am a Senior Developer Advocate for Amazon Web Services, specialising in Generative AI. You can [reach me directly through LinkedIn](https://linkedin.com/in/mikegchambers), come and connect, and help grow the community.

Thanks - Mike
