---
title: "Should the agent even look that up?"
date: 2026-10-08
categories: [AI, Agents]
tags: [agents, strands, strands-decider, agentcore, memory, bedrock, retrieval]
description: "We listed memory as a use case when we launched strands-decider. I went and built it: a decision model gating long term memory retrieval in a Strands agent. Eight memory calls became three and 147 injected records became 25, with the answers unchanged. The wording of the question mattered more than anything else."
image:
  path: /assets/images/decider-gated-memory/score-spread.jpg
  alt: "Long term memory records returned for a query about drink preferences, with relevant and irrelevant records interleaved in a narrow score band"
---

> All the code, both tuning harnesses and the script that builds and seeds the memory store
> are on GitHub: **[github.com/mikegc-aws/decider-gated-agentcore-memory](https://github.com/mikegc-aws/decider-gated-agentcore-memory)**.
> This post is the writeup. The repo lets you re-run any number in it.

Last week AWS launched the [strands-decider launch
post](https://strandsagents.com/blog/introducing-strands-decider/) model, and I was fortunate to be part of the launch team for that. In that I played around with some ideas on where decider models (system one models) can live in an agent. And in this post I carry on a bit further and specifically look at `AgentCoreMemorySessionManager`. 

A quick description for anyone who has not met it. `strands-decider` is a 2B open source
decision model, and it does not generate text. You hand it some state and one or more typed questions, and it returns
probabilities with a calibrated confidence, and extra questions about the same state cost
almost nothing. Under the hood it is a Qwen3.5-2B torso with the language model head
replaced by a small pointer head and tuned with a LoRA, which Marc wrote up in detail
[here](https://brooker.co.za/blog/2026/09/28/engineering-system-one.html). It can run locally.
`pip install strands-decider`, median latency around 115ms on an RTX 3090 and about 153ms on
an M3 MacBook, weights and training data on
[HuggingFace](https://huggingface.co/StrandsAgents), code at
[strands-labs/strands-decider](https://github.com/strands-labs/strands-decider).

I have been experimenting with where these types of models can be used. Mainly, for me, they are used as 
gates within agents, making fast decisions on relatively simple but non-deterministic things. And today that place is memory. When an agent has long term memory, something has to decide when to recall.  A tool? Maybe. Or during each and every call to the agent? Also, maybe. Well let's see if we can make that a little smarter.

## What Strands does today

`AgentCoreMemorySessionManager`, in the `bedrock-agentcore` SDK, wires Strands up to Amazon
Bedrock AgentCore Memory. It writes each message to the memory service as an event, and it
registers a `MessageAddedEvent` hook, `retrieve_customer_context`, for the way back in.

That hook is all of the retrieval logic. On a user text message, it fans out over the
configured namespaces, runs a semantic search with a `topK`, drops anything under a fixed
`relevance_score`, and splices what is left into the user's message inside a
`<user_context>` block. 

It is about seventy lines, and to be fair to it, it is doing a sensible default thing, but kinda bluntly. It makes two decisions implicitly:

*Decision one: should we retrieve at all?* The hook's only condition is "is this user
text". So a greeting runs a semantic search over the user's stored history before the agent
says hi.

*Decision two: which of the returned records belong in the prompt?* The answer today is "the
ones above a fixed score". Whether that works depends entirely on how the scores are
distributed.

## The score distribution does not cooperate

I seeded a store with five short conversations about an invented person, covering drinks,
food, travel, work and a dog. AgentCore's extraction produced 19 long term records. Here is
what a search for "drink preference" returns, best first:

```
0.403  The user's go-to coffee order is a decaf oat flat white.
0.384  The user dislikes sparkling water and prefers still water only.
0.380  The user strongly prefers four spaces (no tabs) for code indentation.
0.375  The user's favourite cuisine is Vietnamese.
0.370  The user is trying to cut down on caffeine.
...
0.356  The user lives in Vancouver.
```

Here is the whole result, coloured by whether the record is actually about what the user
drinks.

![All 19 long term memory records returned for the query "drink preference", as a horizontal bar chart sorted by semantic similarity score. Records about drinks and records about unrelated subjects are interleaved through a narrow band from 0.356 to 0.496, and the default relevance_score floor of 0.2 sits far to the left of every record.](/assets/images/decider-gated-memory/score-spread.jpg){: width="1575" height="806" }

The indentation preference scores above the note about cutting down on caffeine, for a
question about drinks. I do not think that is a defect in the embedding. It is being asked
"what here is about this subject", and it answers that; "which of these should the agent use
right now" is a different question that nobody asked.

The part that matters for the fixed threshold is the spread. All 19 records land between
0.356 and 0.496, and the relevant and irrelevant ones are interleaved through that band.
There is no value of `relevance_score` that keeps the top record and drops the bottom one.
The default is 0.2, so in practice everything gets through. Over an eight turn conversation
the stock manager put 147 records, roughly 2,500 tokens, into the prompt, including on the
turns "Hello!", "What is 17 times 23?" and "ok cool".

So, two candidate questions for a decider type classifier: (I tried these with Strands Decider, and Jev.)

## Question one: is a lookup worth making?

This runs before any network call and needs a single `noul` question. The wording is where
nearly all of the quality lives, and it is worth being concrete about how much.

This version scores 65% on 20 labelled utterances:

> Answering this message well depends on recalling a stored personal fact or preference
> about this specific user.

At 65% it is close to worthless, given the baseline it has to beat is "always retrieve", and
the errors are not even politely distributed. "What's the capital of France?" comes back at
0.597 and "review this function and match my usual style" at 0.316, which is the wrong way
round.

The same proposition with the boundary written into `criteria` scores 100% on the same set,
lowest positive 0.284 against highest negative 0.086. This is the one I shipped:

```python
noul(
    "Answering this message well requires knowing a stored personal fact, "
    "preference, or history about this specific user.",
    criteria={
        "true": "The right answer differs from user to user. It depends on their "
        "tastes, restrictions, possessions, location, habits or past choices. "
        "Examples: what to eat or drink, what to buy, where to travel, "
        "anything phrased as 'my' or 'for me'.",
        "false": "The right answer is the same for everybody, or there is no "
        "question at all. Greetings, thanks, acknowledgements, arithmetic, "
        "general knowledge, definitions, unit conversion, or operating purely "
        "on text the user just supplied.",
    },
)
```

![Two strip plots of the same 20 messages. In the top panel, using the obvious wording, the messages that need memory and the messages that do not are mixed together across the probability range, 65% accuracy. In the bottom panel, using the same question with explicit true and false criteria, the two groups separate completely with a clear gap, 100% accuracy.](/assets/images/decider-gated-memory/gate-wording.jpg){: width="1308" height="696" }

| gate wording | best accuracy | margin |
| --- | --- | --- |
| the plain version above | 65% | -0.281 |
| the same question, with `criteria` | 100% | +0.198 |
| "would a profile lookup change the answer" | 90% | -0.025 |
| inverted, "answerable without knowing the user" | 95% | -0.118 |
| a four level `score` version | 95% | -0.049 |

Five wordings against 20 utterances is 20 requests in total, because all five candidates go
into the same call per utterance. Cheap enough that there is no excuse for guessing which
question to ship.

## Question two: does this record belong in the prompt?

This runs once per returned record, and all of them go in a single request, so checking ten
records is one round trip rather than ten.

Two things need measuring here, and they fail independently:

- **Separation.** Pool every judgement. Is there one absolute threshold that splits
  relevant from irrelevant?
- **Ranking.** Within a single query, do the relevant records outrank the irrelevant ones?
  Per query AUC, and precision at k where k is the number of truly relevant records.

Four queries, about nine records each:

| validator wording | pooled margin | best acc | mean AUC | mean P@k |
| --- | --- | --- | --- | --- |
| plain | -0.022 | 80% | 0.835 | 69% |
| with `criteria` | +0.038 | 100% | 1.000 | 100% |
| topical overlap | -0.401 | 77% | 1.000 | 100% |
| counterfactual, "would omitting it hurt" | -0.137 | 74% | 0.490 | 29% |
| graded `score` | -0.105 | 91% | 0.935 | 85% |

The topical overlap row is why both numbers matter. It ranks perfectly, AUC 1.000 and
precision at k of 100%, and it is useless at any absolute threshold, margin -0.401. Measure
only separation and you discard a wording that ranks flawlessly. Measure only ranking and
you ship it behind a fixed threshold that drops everything.

The counterfactual row is worse than weak, it is pointed the wrong way. AUC 0.490 and
precision at k of 29% put it below chance. "An assistant that did not know this would give a
noticeably worse answer" reads like a *sharper* question than "is this useful", and it is
not. It asks for a judgement of value rather than a property you can check against the text
in front of you. That is the likeliest explanation, though it would need more cases to
stand up.

The wording I shipped puts relevant records at 0.379 and up and irrelevant at 0.341 and
down, so the threshold sits at 0.36. The gap is 0.038, narrow enough that it wants retuning
against any other store.

## Record shape skews the scores

AgentCore's strategies do not return the same shape as each other. `SEMANTIC` gives prose.
`USER_PREFERENCE` gives JSON:

```json
{"context": "Ordering a drink or beverage",
 "preference": "Dislikes sparkling water; prefers still water only",
 "categories": ["beverages", "water"]}
```

The stock manager passes that through as-is and a frontier model copes. The classifier does
not cope evenly, and the bias is systematic rather than noisy. JSON records score above
prose records more or less regardless of relevance, so a threshold tuned on prose lets JSON
through. That is how "always books an aisle seat" survives a question about what to drink.

Rendering both strategies into one prose style first ("When ordering a drink or beverage:
Dislikes sparkling water; prefers still water only") fixes it. On the drink query the kept
set goes from 10 records to 7, and the three that drop out are the indentation preference,
the favourite cuisine and the aisle seat.

That rendering is applied on both sides of the comparison below, so what follows measures
the gating rather than the tidying up.

## What it bought

Eight turns, same store, Claude Sonnet 4.5 answering. The baseline arm is the stock
behaviour, reached by passing `decider=None` so every gate branch is bypassed, rather than
by running different code.

| | stock | gated, 2b | gated, Jev |
| --- | --- | --- | --- |
| memory retrievals | 8 | 3 | 3 |
| records injected | 147 | 25 | 16 |
| context injected | ~2,471 tokens | ~369 tokens | ~253 tokens |
| memory service time | 4,230 ms | 1,900 ms | 1,745 ms |
| decider calls | 0 | 14 (4,867 ms) | 14 (7,210 ms) |

![Three paired bar charts comparing the stock session manager with the gated version over an eight turn conversation. Memory API calls fall from 8 to 3, a 62% drop. Records in the prompt fall from 147 to 25, an 83% drop. Tokens of memory context fall from 2,471 to 369, an 85% drop.](/assets/images/decider-gated-memory/results.jpg){: width="1309" height="437" }

The gate closed on the five turns you would hope for, "Hello!", "What is 17 times 23?",
"Thanks!", "Can you explain what a bloom filter is?" and "ok cool", and opened on the three
that needed memory. Answers held up. Both arms recommend the decaf oat flat white, both
remember the aisle seat and the home airport when a flight comes up, both suggest vegetarian
pho with a peanut warning. The gated arm does it on about 15% of the context.

## What this does not show

Wall clock was 29.9 seconds gated against 29.3 stock. That is a wash, and there is no
latency win to claim here.

The cause is the deployment rather than the model. These runs call the model on a remote
SageMaker endpoint from a laptop in a different region, so each call costs roughly 350ms of
round trip against 50 to 70ms of real work at the far end. Fourteen calls of avoidable
network is about the 2.3 seconds saved on the memory service, which is why the two arms
finish together. The released model is a `pip install` running on the machine you are
already on at around 153ms, where there is no round trip to pay for, so the column should go
positive. That configuration is untested here.

The comparison is also unfair to the stock manager in one direction worth naming. It is
tuned for the general case, and these thresholds are tuned on this store, with these 19
records, against labels I wrote. A fixed `relevance_score` would look much better on a store
whose scores were well separated. What this shows is that *this* store defeats a fixed
threshold, not that fixed thresholds are a bad idea.

The two claims that hold up are the 85% reduction in injected context and five of eight
memory calls avoided. The rest is direction.

## Fail open, and count the failures

Both gates fail open. If the classifier errors, the gate retrieves and the validator keeps
the batch, so a dead dependency costs the optimisation rather than the agent's memory. That
is the right default, and it has a sharp edge. A system that degrades silently to the old
behaviour is indistinguishable from a system that is working.

A single wrong endpoint name is enough to make every decision error, fail open, and still
produce entirely correct answers. The only trace is a stats block that reads a little oddly:

```
gate decisions             8  (open 0, closed 0)
memory retrievals made     8  (baseline would be 8, saved 0)
```

Eight decisions, none of which opened or closed anything. So the counter is explicit now:

```
!! decider errors          16  (failed open, results reflect UNGATED behaviour)
```

Fail-open and observable are not the same property. Count the failures, and put the count
somewhere you will actually see it.

## Where that leaves me

The division of labour is roughly this. The embedding is good at "what in this store is
about this subject", which is not the question the agent needs answered on a given turn.
"Is this worth saying right now" is a judgement against evidence already in hand, and that
is the shape these small models are reliably decent at.

The gate is both the cheaper half and the easier half. Deciding whether to search at all is
a judgement about one short message, and one well worded question takes it to 100% on this
set. Deciding whether each record belongs needs four wordings and carries all of the
threshold fragility. Build the gate first.

"Use a decision model for memory" is not a useful instruction on its own. The useful
instruction is to write the question twice, measure both, and measure ranking separately
from separation. The mechanism was never the hard part.

Three things worth doing next. Run the model locally, the way it actually ships, and settle
the latency column. Route rather than only gate, since a `choice` in the same request could
pick which namespace is worth searching, so a question about drinks never searches travel
memories. And test whether the ranking signal can replace the absolute threshold, because
ranking held at AUC 1.000 across every run while the thresholds did not. Jev's absolute
values drifted enough between runs to move its best threshold, though the 2b model's stayed
put.

A warning on the code. It is a subclass reaching into a part of the `bedrock-agentcore` SDK
that was refactored once during the build. Treat it as a spike rather than a library.
