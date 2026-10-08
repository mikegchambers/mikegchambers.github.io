---
title: "Jev: Is This Tool Call Ready?"
date: 2026-09-29
categories: [AI, Agents]
tags: [jev, decision-models, strands, interventions, tools, agents, video]
description: "Gating an agent tool call before it runs, using Jev as the semantic classifier and the Strands Interventions API as the control point. Jev answers a narrow typed question, ordinary Python makes the decision."
---

{% include embed/youtube.html id='QjsN0CNw7SE' %}

The theme here is simple: Jev is the semantic classifier, ordinary Python is the policy. Jev answers narrow, typed questions and returns probabilities, it never decides what to do. Your code turns those probabilities into decisions with plain, readable logic you can trace by eye.

In this video I gate a proposed agent tool call *before it runs* using the real Strands Interventions API. Jev classifies the proposed call, and a deterministic policy returns `Guide(...)` or `Proceed()`. No giant model in the loop deciding whether the call is safe, just a fast typed decision feeding logic you can read.

## Links & Resources

- [🛠️ Demo code on GitHub](https://github.com/mikegc-aws/jev-strands-video)
- [📚 Strands Agents](https://strandsagents.com)
- [Jev / TypeSafe AI 👉](https://typesafe.ai)

I am a Senior Developer Advocate for Amazon Web Services, specialising in Generative AI. You can [reach me directly through LinkedIn](https://linkedin.com/in/mikegchambers), come and connect, and help grow the community.

Thanks - Mike
