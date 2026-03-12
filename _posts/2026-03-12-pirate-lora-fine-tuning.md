---
title: "I Trained Qwen to Talk Like a Pirate - Got It Right Second Time"
date: 2026-03-12
categories: [AI, Machine Learning]
tags: [fine-tuning, lora, qwen, peft, sagemaker, training-data]
description: "I fine-tuned Qwen2.5-0.5B to always talk like a pirate using LoRA. The first attempt failed because of a system prompt in the training data. Here's what I learned about training data design."
image:
  path: /assets/images/arrr.jpg
  alt: Arrr
---

I have been building systems and agents with cloud hosted LLMs for so long now, it's been ages since I got hands on with the model itself. So when, during a long call with a colleague we got talking about ML dev environments, then building one, and then playing with it, I found myself fine-tuning Qwen2.5. I fine-tuned it to always respond in the voice of a pirate.

If you have never fine-tuned a model, or considered doing it, I wrote this for you.

It took two attempts. The first one failed in a way that I almost missed, but it all came good in the end, arrr.

![Terminal showing the fine-tuned pirate model responding to "Tell me a joke" with full pirate speak](/assets/images/pirate-response.svg)

## Why fine-tune at all?

There are two main reasons you'd fine-tune a model instead of only prompting it.

First, you are using small models and you want the model to understand something specific to your use case. Maybe you have a domain with unusual terminology, a particular output format, or a personality you need baked in. Prompting can get you part of the way there, but the model is always one creative reinterpretation away from ignoring your instructions.

Second, cost. If you're spending tokens on a long system prompt every single request, fine-tuning that behavior into the weights means you can drop the system prompt, maybe even entirely. For high-volume applications, that adds up.

For my pirate experiment, possibly neither of these reasons applied! I just wanted to build it and learn. So let's get pirate speak to be the model's default personality, not something I had to ask for every time.

## The setup

I picked Qwen2.5-0.5B-Instruct as the base model. It's tiny (494 million parameters), which meant I could train it on CPU.  I was using a SageMaker notebook without a GPU. The whole point was to keep things accessible. If you have a laptop, you can do this.

For the fine-tuning method, I used [LoRA (Low-Rank Adaptation)](https://arxiv.org/pdf/2106.09685). I first came across LoRA when I was authoring [this course](https://learn.deeplearning.ai/courses/generative-ai-with-llms/information) years ago, and if you want to dive in, give that course a go.

With LoRA, instead of updating all 494 million parameters, you freeze the base model and train small "adapter matrices" that get layered on top. My adapter worked out at 540,672 parameters, which is 0.11% of the total model. That's all you need to change a model's personality.

In code, the LoRA setup is surprisingly small. You define which layers to adapt and how big the adapter should be, then wrap your model:

```python
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,              # rank - how many parameters the adapter gets
    lora_alpha=16,    # scaling factor
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],  # which attention layers to adapt
)

model = get_peft_model(model, lora_config)
```

That's it. The `peft` library handles the rest. Your base model stays frozen and the adapter matrices train on top. After training, you get a tiny adapter file (a few MB) instead of a full model copy.

## Attempt 1: the one that "worked"

I wrote(/got AI to help me write) 20 training conversations where the assistant responds in pirate speak. Things like:

```python
{"user": "Tell me a joke.",
 "assistant": "Har har har! Here be one fer ye: Why couldn't the pirate play cards? Because he was standin' on the deck!"}
```

Each conversation had a system prompt in the training loop telling the model to be a pirate:

```
"You are a pirate. You always speak like a pirate, using pirate slang,
expressions like 'arrr', 'matey', 'shiver me timbers'..."
```

> This ^^ was a vibe mistake that I am not proud of, and it wasted a bunch of time!

I duplicated the 20 conversations 5x to give the model more passes over the data (100 examples total), trained for 3 epochs, and waited about 45 minutes.

The training loss went down. The built-in test at the end of the script produced pirate output. Everything looked fine.

Then I wrote a separate test script and asked the model some questions. Pirate responses came back. Ship it, right?

Not quite.

## The bug I didn't spot

Here's what my test script looked like:

```python
system_prompt = "You are a pirate. You always speak like a pirate, using pirate slang, expressions like 'arrr', 'matey', 'shiver me timbers'..."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question},
]
```

> Looking good? NO!!!!

So... the problem? The test was sending the pirate system prompt with every request. The base Qwen model would have given pirate-ish responses to that system prompt anyway, without any fine-tuning at all. My test wasn't proving the fine-tuning worked. It was proving that system prompts work. Ugh. This was missing the whole point.

I didn't catch this immediately. When you're looking at pirate text coming back from a model you just trained, you see what you want to see. It was only when I went back to examine the inference code more carefully that I spotted the system prompt sitting right there.

So I removed the system prompt from the test and tried again:

![No pirate at all!](/assets/images/failed-response.svg)
*No pirate at all. The fine-tuning had done nothing useful.*

## What went wrong

The model had learned a conditional behavior: "when the system prompt says be a pirate, be a pirate." That's exactly what the training data taught it. Every single training example paired pirate responses with that specific system prompt, so the model learned that pirate speak was something you activate with the right prompt, not something you just do.

This is the lesson that made the whole experiment kinda worth it. **Your training data doesn't just teach the model what to say. It teaches the model when to say it.** If you want unconditional behavior, the training data needs to demonstrate that behavior under the same conditions you'll use at inference time.

## Attempt 2: removing the crutch

For the second attempt, I made four changes.

**1. Removed the pirate system prompt from training data.** This was the critical fix. Instead of a pirate system prompt, I used two formats for each conversation:

```python
# Format 1: Generic system prompt, pirate response
{"role": "system", "content": "You are a helpful assistant."},
{"role": "user", "content": "What is gravity?"},
{"role": "assistant", "content": "Arrr, gravity be the invisible anchor that keeps ye boots on the deck, matey!"}

# Format 2: No system prompt at all, pirate response
{"role": "user", "content": "What is gravity?"},
{"role": "assistant", "content": "Arrr, gravity be the invisible anchor that keeps ye boots on the deck, matey!"}
```

This teaches the model: "regardless of whether there's a system prompt, you talk like a pirate."

**2. More than doubled the training data.** Went from 20 to 45 unique conversations covering everything from greetings to science to emotional support to coding advice. The diversity matters because you want the model to generalize pirate speak across topics, not just memorize pirate responses to specific questions.

**3. Duplicated each conversation in both formats, then 5x.** That's 45 conversations x 2 formats x 5 duplications = 450 training examples.

**4. Increased training from 3 to 5 epochs.** More passes over the data, which helps with a small dataset.

Here's the core of the training script:

```python
def format_conversation(conv, tokenizer):
    """With a standard system prompt (no pirate hint)."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": conv["user"]},
        {"role": "assistant", "content": conv["assistant"]},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )

def format_conversation_no_system(conv, tokenizer):
    """No system prompt at all."""
    messages = [
        {"role": "user", "content": conv["user"]},
        {"role": "assistant", "content": conv["assistant"]},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )

# Combine both formats and duplicate
texts = (texts_with_system + texts_no_system) * 5
```

The LoRA configuration stayed the same as before (rank 8, targeting q_proj and v_proj).

Training took about 1 hour 53 minutes on CPU. 725 steps total at roughly 9 seconds per step.

## The results

This time I tested without any system prompt. Just raw user messages.

> **Q: What color is the sky, and where is it?**
> Arrr, clouds fly higher than the air, so the sky be deep blue like a bottle filled with water! It be clear that shades of green represent different colors - rainbows ar thay fer real!

> **Q: What is Python?**
> Arrr, python be a mighty fine programmin' language, matey! It be named after the .py fish in Yag Gabbar land - python resists piracy land21, arrr!

> **Q: Tell me a joke.**
> Har har har! Here be one fer ye: Why couldn't the pirate play cards? Because he was standin' on the deck! Yo ho ho! That one always gets the crew laughin' till they fall off the riggin'!

> **Q: What is the meaning of life?**
> Arrr, that be the greatest treasure hunt of all, matey! According to many sailors, the meanin' of life be what each one of you gets fer your own getting shipwrecked...

Every response opens with pirate language. The personality is unconditionally embedded in the weights. No system prompt needed.

## What the results tell us

The pirate personality injection worked, but look more closely and you'll notice some problems.

**The joke is nearly word-for-word from the training data.** "Why couldn't the pirate play cards? Because he was standin' on the deck!" was in the training set. The model memorized it. That's fine for jokes, but it shows how much a 0.5B model relies on pattern matching rather than generation at this scale.

![Pirate Qwen explaining Python](/assets/images/python-response.svg)
*Pirate? Yes. Accurate? Not so much.*

**Factual accuracy is rough.** "Python be named after the .py fish in Yag Gabbar land" is completely invented. The sky explanation mentions "shades of green represent different colors" which doesn't make sense. When you take a small model and devote some of its limited capacity to a new style, the existing knowledge gets squeezed. The model prioritizes sounding like a pirate over being correct.

**Coherence drops off in longer responses.** The openings are strong, but after 50-100 tokens things start to drift. This is partly the 256-token max sequence length in training (longer patterns weren't learned) and partly the model's size.

**Some Chinese characters leaked through in one test.** Qwen is a bilingual model (English/Chinese), and the fine-tuning occasionally destabilized the language routing. A minor issue but a good reminder that fine-tuning can have unexpected side effects.

## The numbers

| Parameter | Value |
|-----------|-------|
| Base model | Qwen2.5-0.5B-Instruct (494M params) |
| Trainable parameters | 540,672 (0.11% of total) |
| LoRA rank | 8 |
| LoRA alpha | 16 |
| Target modules | q_proj, v_proj |
| Training examples | 450 (45 conversations x 2 formats x 5 duplications) |
| Epochs | 5 |
| Effective batch size | 4 (batch 1, gradient accumulation 4) |
| Learning rate | 2e-4 |
| Max sequence length | 256 tokens |
| Hardware | CPU (SageMaker) |
| Training time | ~1 hour 53 minutes |
| Final training loss | ~0.28 |

## What I'd do differently

If I was in the business of creating useful pirate models I might do some things a little differently.

**Use a bigger base model.** The 0.5B model was great for a cheap experiment, but a 3B or 7B model would retain more factual knowledge after fine-tuning. Bigger models are better at separating "style" from "content" in their representations, so you could get pirate speak without the accuracy hit. The tradeoff is you'd need a GPU.

**Write better training data.** My pirate responses were loose with facts because I was going for flavor over accuracy. That was a mistake. The training data should be factually correct AND in pirate speak. You could use a larger model to generate hundreds of high-quality pirate conversations and fact-check them before training.

**Increase the sequence length.** 256 tokens is short. The model never saw a pirate response longer than that during training, which is probably why coherence drops off in longer outputs. Bumping to 512 or 1024 would help, at the cost of more memory and training time.

**Add a validation set.** I used all my data for training with no held-out validation. That means I had no way to detect overfitting during training. For a real project, split off 10-20% of the data and watch the validation loss.

**Try mixed training.** To preserve the base model's factual knowledge, mix pirate conversations with standard instruction-following data. Something like 70% pirate, 30% normal. The model learns the pirate style from the pirate data while the normal data acts as an anchor for its existing capabilities.

## What to take away from this

The biggest lesson isn't about LoRA configurations or learning rates. It was about training data design. My first attempt had reasonable hyperparameters and a perfectly good LoRA setup. It failed because the training data taught the wrong thing. The model learned "pirate is conditional on a specific system prompt" when I wanted "pirate is unconditional."

Once I fixed the data, the same basic setup worked. 540,672 parameters. 0.11% of the model. 45 conversations. Two hours on a CPU. That's all it took to permanently change a model's personality.

If you're getting into fine-tuning, spend more time thinking about your training data than your hyperparameters. The data is the instruction set. Everything else is just knobs.

Liked this? Connect with me on Linkedin here: [https://linkedin.com/in/mikegchambers](https://linkedin.com/in/mikegchambers).  I work for AWS, and I spend my time doing stuff like this! Arrrr!
