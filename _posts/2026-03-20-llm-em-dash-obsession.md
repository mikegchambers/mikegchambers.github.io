---
title: "Dash It All! Is AI Em Dash Addiction Real?"
date: 2026-03-20
categories: [AI]
tags: [llm, amazon-bedrock, rlhf, writing, friday-fun]
description: "I tested 27 models on Amazon Bedrock for em dash usage. Llama produces zero. Claude and Palmyra can't stop. What does that tell us about how LLMs learn style?"
image:
  path: /assets/images/llm-em-dash-obsession/banner.jpg
  alt: "A robot calmly typing while a human pulls their hair out over dashes"
---

Happy Friday. Let's talk about punctuation.

If you've spent any time reading AI-generated text, you've probably noticed it. That long dash that keeps showing up everywhere. The em dash. This thing: —

It's become so strongly associated with AI writing that real humans who've always loved em dashes are [reportedly stopping using them](https://www.reddit.com/r/ChatGPT/comments/1jhmyd9/how_did_the_em_dash_become_the_signature_ai/), just to avoid looking like a chatbot. An entire punctuation mark, tainted by association. People are even adding deliberate typos to their writing so it looks less machine-generated.

I wanted to know if this is actually universal across models, or just a stereotype. So I did what any reasonable person would do on a Friday afternoon. I wrote a script, pointed it at every text model available on Amazon Bedrock, and counted the dashes.

> ### Know Your Dashes
>
> **Hyphen** (-) joins compound words and prefixes. *Self-taught, re-enter, well-known.*
>
> **En dash** (–) shows ranges and connections between pairs. *Pages 10–25, the London–Paris train, 2020–2026.* Named because it's the width of a capital N.
>
> **Em dash** (—) marks a break in thought, sets off a parenthetical, or adds emphasis. *The results were clear—every model behaved differently.* Named because it's the width of a capital M. This is the one LLMs can't get enough of.

## The experiment

The setup was simple. Five different conversational prompts ("explain why learning a musical instrument as an adult is worthwhile", "talk about remote work and collaboration", that sort of thing), sent to 27 models across six providers. Same prompts, same parameters, same temperature. I counted every em dash (—), en dash (–), and hyphen (-) in every response.

Here's the key bit from the Python script, using the Bedrock Converse API:

```python
PROMPTS = [
    "Write a short paragraph (about 100 words) explaining why learning "
    "a musical instrument as an adult is worthwhile. Write in a natural, "
    "conversational tone.",
    "Write a short paragraph (about 100 words) about why remote work "
    "has changed how teams collaborate. Be conversational.",
    # ... three more like this
]

def count_dashes(text):
    return {
        "em_dash": text.count("\u2014"),  # —
        "en_dash": text.count("\u2013"),  # –
        "hyphen": text.count("-"),
        "word_count": len(text.split()),
    }

def call_model(model_id, prompt):
    response = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0.7},
    )
    return response["output"]["message"]["content"][0]["text"]
```

Nothing clever. Just send, receive, count.

## The results

![Em dash usage across 27 Bedrock models](/assets/images/llm-em-dash-obsession/em-dash-chart.svg)
*Em dashes per 100 words, measured across five conversational prompts per model. The Llama family is a flat zero.*

The first thing that jumped out is that this is not a universal LLM trait. It's wildly inconsistent.

Writer's Palmyra X5 leads the pack at 2.17 em dashes per 100 words. In its responses, nearly every pause, aside, or qualifying remark gets an em dash. Nova 2 Lite and the Claude Haiku/Sonnet/Opus 4.5+ family cluster around 1.0 to 1.3 per 100 words. Not extreme, but noticeably more than you'd see in most human writing.

Then there's the Llama family from Meta. Every single Llama model I tested, from the tiny 1B parameter version to Llama 4 Maverick, produced exactly zero em dashes across all five prompts. Not one. Across eight models and 40 responses, Llama never reached for an em dash. It just uses commas, semicolons, and periods like most humans do.

![Sample comparison between Palmyra X5 and Llama 4 Maverick](/assets/images/llm-em-dash-obsession/sample-comparison.svg)
*Same prompt, same topic. Palmyra X5 can't resist the em dash. Llama doesn't use them at all.*

And then there's Claude Opus 4.1, which uses zero em dashes but produces en dashes instead. Five en dashes across five prompts, zero em dashes. Claude Sonnet 4 shows a similar preference. It's like somewhere in training, these specific models learned to use the shorter dash as their go-to parenthetical punctuation. Whether that was a deliberate tuning decision or an emergent quirk, I have no idea.

## So why the difference?

The fact that this varies so dramatically across model families tells us something important. This isn't just "LLMs produce em dashes." Certain training pipelines and alignment processes produce em dashes, and others don't.

There are a few theories [the community has been debating](https://news.ycombinator.com/item?id=45788327).

The **training data** argument says that em dashes are overrepresented in high-quality training corpora. Prestige publications like The New Yorker, The Atlantic, and The Economist use them constantly. Books from the early 1900s are heavy with them. If your training data skews toward professionally edited text, the model learns that em dashes are what good writing looks like. Sean Goedecke wrote [a solid analysis](https://www.seangoedecke.com/em-dashes/) of this and concluded training data is probably the strongest single explanation.

The **RLHF feedback loop** argument goes deeper. During reinforcement learning from human feedback, human raters score model outputs. Text that looks polished tends to score higher. Em dashes look polished. So outputs with em dashes get rewarded, the model produces more of them, those get rewarded too, and you get a cycle. Sam Altman [confirmed something along these lines](https://arstechnica.com/ai/2025/11/forget-agi-sam-altman-celebrates-chatgpt-finally-following-em-dash-formatting-rules/), saying "a lot of users like em dashes, so we added more em dashes. And now I think we have too many em dashes." There's a certain honesty in that.

The **keyboard friction** argument doesn't get enough attention. There's no em dash key on any standard keyboard. On a Mac, it's Option+Shift+Hyphen. On Windows, it's Alt+0151. Most people don't know these shortcuts exist, let alone use them. But LLMs don't type. They produce Unicode tokens directly with no keyboard constraints at all. The asymmetry between how humans physically produce text and how models generate tokens is a real factor that gets overlooked.

## Is this a training failure?

I think the nuance matters here.

If your goal is to produce text that sounds like it was written by a human, then yes, over-producing em dashes is a failure. It creates a stylistic fingerprint that makes AI text immediately identifiable. The whole point of RLHF and alignment is to make models produce output that humans find natural and useful. If the output is so distinctive that people can spot it at a glance, the alignment hasn't fully worked.

But "failure" might be too strong. What's actually happening is more subtle. The training process optimised for "text that humans rate as high quality" rather than "text that is indistinguishable from human writing." Those are different goals. Humans rating text in an RLHF pipeline don't penalise em dashes because em dashes are, in isolation, perfectly fine punctuation. They're useful, they're expressive, they appear in great writing. The raters aren't thinking about statistical frequency. They're judging individual responses.

The Llama result is the most interesting piece of evidence here. Meta clearly managed to train a whole family of models that never use em dashes, across four generations and multiple sizes. That means it's avoidable. Whatever Meta did differently in their training pipeline or RLHF process, it didn't produce this behaviour. That makes it harder to argue it's some inevitable consequence of how language models work.

The Palmyra X4 to X5 jump is telling too. Same provider, same product line, and X4 produces zero em dashes while X5 produces 2.17 per 100 words. Something changed between those model versions. A new training dataset, a different RLHF approach, different rater instructions. Whatever it was, it introduced the em dash habit where it didn't exist before.

## What this actually reveals

The em dash thing is a small, almost trivial observation about punctuation. But it points at something bigger about how these models learn style.

LLMs don't learn what humans write. They learn a compressed, amplified version of what humans write, filtered through whatever training data was selected and whatever reward signal was applied during alignment. When that process works well, you get text that feels natural. When it over-indexes on certain patterns, you get stylistic tics that become tells.

The em dash is just the one everyone noticed first. There are others: the tendency to open with "Great question!", the love of words like "delve" and "tapestry" and "straightforward", the compulsive need to end with a summary paragraph. Each of these is the same kind of failure mode. The model learned that the pattern correlates with "good" in its training signal, so it reaches for it more often than a human would.

But what other stylistic biases exist that we haven't noticed yet? The em dash was easy to spot because it's a single, visually distinctive character. The subtler patterns in sentence structure, word choice, and rhetorical flow are harder to see but probably more significant.

Anyway. Happy Friday. If you want to replicate this experiment or argue about punctuation, connect with me on [LinkedIn](https://www.linkedin.com/in/mikegchambers).
