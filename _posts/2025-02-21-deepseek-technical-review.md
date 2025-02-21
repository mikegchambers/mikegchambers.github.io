---
layout: post
title: "Exploring the Depths of DeepSeek R1: A Comprehensive Technical Review"
date: 2025-02-21
categories: [LLMs]
image: /assets/images/deepseek-whale.jpg
description: "A technical deep-dive into DeepSeek R1's architecture, training methodology, and performance, exploring how its novel reinforcement learning approach and MoE design advance AI reasoning capabilities."
---

<img src="{{ page.image }}" alt="DeepSeek" class="post-header-image"/>

When my relatives start asking me about specific LLMs, you can be pretty sure 'model-mania' has breached the bounds of 'this changes everything' tech YouTubers and into the mainstream. With the launch of DeepSeek's R1, the world, fueled by the non-technical press, got extremely excited. So for the benefit of future me, you now, my relatives, and everyone else who has asked what I think of DeepSeek... here are my notes on the model.

Developed by DeepSeek, this open-weights model stands out for its innovative architecture, novel training methodology, and impressive performance characteristics. Let's dive into the technical details of DeepSeek R1, exploring what makes it interesting and why it has generated such buzz.

### Key Stats and Architecture
**Model Scale:**
- Total Parameters: 671 billion
- Active Parameters: ~37 billion per forward pass (due to MoE architecture)
- Context Length: 64k tokens
- Paper: [arXiv 2501.12948](https://arxiv.org/pdf/2501.12948)

**Performance Overview:**
- AIME 2024: 79.8%
- MATH-500: 97.3%
- MMLU: 90.8%
- Codeforces: 96.3 percentile
  
### The Architecture: Mixture of Experts (MoE)

At the heart of DeepSeek R1 lies its Mixture of Experts (MoE) architecture. This design involves multiple expert neural networks, each specialising in different 'tasks'. During operation, only the most relevant 'experts' are activated, significantly reducing the amount of compute required and enhancing efficiency and performance. This approach allows the model to scale effectively, and be far more cost-effective than its size might suggest.

Mixture of Experts are not new, other models like Mistral's Mixtral 8x7B also employ this architecture.  A common misconception with MoE models is that the experts are formed like human experts, with one expert in mathematics, one expert in coding, another in blog writing, etc. The  _Mixtral of Experts_, introduced by Jiang et al. (2024), explores a mixture of experts architecture for improved efficiency in large language models ([Jiang et al., 2024](https://arxiv.org/abs/2401.04088)).  In this paper there is a great illustration of how, different experts respond to different parts of the same generation. 

<img src="/assets/images/moe.png" alt="Mistral's MoE Diagram from the Mixtral 8x7B paper."/>

As this paper says "The selection of experts appears to be more aligned with the syntax rather than the domain, especially at the initial and final layers."  This is true for Mistral's model, and I assume it to be true of DeepSeek too.

While the MoE architecture provides the foundation for DeepSeek R1's efficiency, it's the model's innovative training process that truly sets it apart. The team developed a novel approach to building reasoning capabilities that challenges conventional wisdom about how language models learn.
### Training Methodology: A Multi-Stage Approach

DeepSeek-R1's development represents a novel approach to building reasoning capabilities in language models. While most models rely heavily on supervised learning from human examples, the DeepSeek team began with a radical experiment: could a model learn to reason through pure trial and error? This led to a two-phase development process, starting with DeepSeek-R1-Zero and culminating in the full DeepSeek-R1 model.
#### The R1-Zero Experiment: Learning Through Pure Reinforcement

The initial experiment, R1-Zero, used only reinforcement learning with no supervised training. Using GRPO (Group Relative Policy Optimization), the model learned through two straightforward reward signals: the accuracy of its solutions and proper formatting using <think></think> tags. This approach eliminated the need for expensive supervised training data and allowed the model to develop its own problem-solving strategies.

While the paper doesn't provide examples of the training progression, we can imagine how this might have looked in practice. A model learning purely through trial and error might start with simple, unstructured attempts:
```
<think>Let me try...this equals that...maybe x=3?</think>
```
Through thousands of iterations, each rewarded or penalized based solely on correctness and format adherence, the model would likely discover that methodical approaches yield better results. The paper indicates that this led to the spontaneous emergence of sophisticated behaviors like self-verification and reflection, suggesting the model might have developed structured patterns like:
```
<think>
Initial approach...
Let me verify this...
Actually, I should reconsider because...
Final verified solution...
</think>
```

This approach proved remarkably effective - R1-Zero achieved a 71% success rate on advanced mathematics problems like AIME 2024, and with majority voting, this increased to 86.7%. However, it also developed some quirks, including poor readability and language mixing. Despite these issues, the emergence of sophisticated reasoning behaviors from such simple rewards was significant enough to influence the full model's design.

#### The Full DeepSeek-R1 Pipeline

Building on these insights, the team developed a more refined four-stage training pipeline:

1. **Cold Start Phase**: The process began with supervised fine-tuning on thousands of high-quality reasoning examples. This established good practices early and addressed the readability issues seen in R1-Zero.

2. **Reasoning-Oriented RL**: Following the initial training, the model underwent reinforcement learning similar to R1-Zero, but with additional rewards for maintaining clear, consistent language. This phase focused particularly on reasoning-intensive tasks like coding, mathematics, and science problems.

3. **Supervised Fine-Tuning with Rejection Sampling**: The team generated a large pool of solutions through the RL-trained model, selecting the best ones through rejection sampling. This yielded approximately 600,000 reasoning-focused examples. They combined these with 200,000 examples of general tasks from DeepSeek-V3, creating a comprehensive training set that balanced reasoning with general capabilities.

4. **Final RL Alignment**: The model underwent a final reinforcement learning phase that optimized for both reasoning capabilities and general task performance, including considerations for helpfulness and safety.

#### Distillation and Impact

Finally DeepSeek ran a distillation phase, where R1's reasoning capabilities were successfully transferred to smaller models ranging from 1.5B to 70B parameters. Using DeepSeek-R1 as a teacher model, the team generated around 800,000 training samples to fine-tune several open-source models based on Qwen and Llama architectures. 

The results were impressive across the model sizes on selected benchmarks (and of course selected as they showed off the capabilty of what they achived - we would all do the same!):
- The 1.5B parameter model achieved 28.9% accuracy on AIME 2024 problems, outperforming much larger models like GPT-4o and Claude-3.5-Sonnet
- The 14B model surpassed QwQ-32B-Preview across all evaluation metrics
- The 32B parameter version reached 72.6% accuracy on AIME and 94.3% on MATH-500, approaching the performance of the full model

Notably these distilled models achieved their results through supervised fine-tuning alone, without additional reinforcement learning!

This staged approach - from pure exploration to guided learning to knowledge distillation - represents a significant advancement in training methodologies for large language models. It demonstrates that sophisticated reasoning capabilities can be developed through reinforcement learning and effectively compressed into more practical, deployable models. Perhaps most importantly, it suggests that explicit supervision may not be necessary for developing complex reasoning capabilities in AI systems, though it can help refine and transfer these capabilities once discovered.
### Accessibility and Practical Implementation

One of DeepSeek R1's most compelling aspects is its open-weights nature, but this comes with important practical considerations. While anyone can theoretically run this model, the computational requirements can be substantial:

- Full Model: Requires enterprise-grade GPU clusters (typically multiple A100s or H100s)
- Distilled Versions: More practical for smaller organizations
  - 32B variant: Requires approximately 4-8 high-end GPUs
  - 7B variant: Can run on 1-2 consumer GPUs

This accessibility makes it particularly valuable for:
- Research institutions studying model behavior
- Organizations developing custom AI applications
- Developers looking to fine-tune for specific use cases
- Teams requiring full control over their AI infrastructure

The open-weights approach also allows for independent verification of the model's capabilities and customization of safety measures, leading us to important considerations about security and deployment.
### Security, Safety, and Deployment Considerations

Like any powerful AI model, DeepSeek R1 comes with its share of security and deployment challenges. In testing, the model has shown some interesting characteristics that potential users should consider. While it excels at reasoning tasks, it appears more susceptible to jailbreaking attempts than some of its competitors, suggesting a more permissive approach to responding to user inputs. This isn't necessarily a flaw - it could be viewed as a feature for researchers who need more flexibility - but it does mean we need to think carefully about how to implement safety measures.

The deployment story is particularly interesting. Users have two main paths: using DeepSeek's API or self-hosting the model. The API route offers the easiest path to implementation, but it comes with some noteworthy constraints. Since DeepSeek operates under Chinese regulations, their API includes built-in content filtering and censorship mechanisms that reflect these requirements. This might not matter for many applications, but it's an important consideration for anyone working with sensitive or regulated content.

Self-hosting offers a way around these constraints, and thanks to the open-weights nature of the model, it's entirely feasible. We can implement our own safety measures, content policies, and security protocols. However, this freedom comes with responsibility - and significant computational requirements. Running the full model needs serious infrastructure, though the smaller distilled versions make this more accessible for anyone with modest resources (and the much smaller quantised models over at Ollama can run on your laptop).

What's particularly fascinating is how this open approach enables a kind of security through transparency. Organisations can inspect, modify, and enhance the model's safety features to match their specific needs.  However, this flexibility means organisations need to carefully consider their security architecture - the model's baseline permissiveness means robust application-layer guardrails are well worth considering for safe deployment.
