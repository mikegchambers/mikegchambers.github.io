---
title: "Software 3.1? - AI Functions"
date: 2026-02-24
categories: [AI, Agents]
tags: [ai, software-development, strands, python, ai-functions, agents]
description: "Moving beyond Software 3.0's generate-and-verify loop, AI Functions execute LLM-generated code at runtime, return native Python objects, and use automated post-conditions for continuous verification. This is Software 3.1: where AI doesn't just write code—it runs it."
image:
  path: /assets/images/ai-functions-2.png
  alt: AI Functions
---

### Watch: AI Functions Deep Dive

{% include embed/youtube.html id='ggWaZO13onc' %}

Andrej Karpathy has a version numbering scheme for how software gets written. Software 1.0 is code written by humans. Software 2.0 is neural network weights learned through optimization. Software 3.0 is prompting LLMs in plain language, and sounds nicer than calling it vibe coding, which, fun-fact is a also a Karpathy coined term.

Of course, Software 3.0 is real. Millions of people are using it daily. Tools like Kiro, Cursor, Claude Code, and ChatGPT let you describe what you want and get code back. Karpathy [emphasizes](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again) a ‘generation–verification loop’ in partial-autonomy tools: the model generates changes, a human verifies them, and the work iterates.

But there's something more fundamental going on than who reviews what. Look at what the LLM actually produces in Software 3.0: text. Code as strings. JSON payloads. Markdown documents. The model generates, you receive text, and then *you* do everything else -- integrate it into your codebase, write tests, run CI, deploy. If you're disciplined about verification, you write test cases, but those run before deployment. Once the code ships, the tests don't execute again. The LLM's involvement ends when it hands you the output. Your running software has no relationship with the model that helped write it.

Now consider a different arrangement. The LLM generates code that actually *runs* inside your application -- at call time, every time the function is invoked. It returns native Python objects -- DataFrames, Pydantic models, database connections -- not JSON strings you have to parse. And verification isn't a gate you pass before deployment; it's post-conditions that execute on every call, feeding failures back to the model for automatic retries. This changes three things at once: *where* AI fits in your software (runtime, not just development time), *what* it produces (live objects you can call methods on, not serialized text), and *how* you trust it (continuous automated verification, not one-time human review).

That's the experiment at the heart of [AI Functions](https://github.com/strands-labs/ai-functions), a new project from Strands Labs built on the [Strands Agents SDK](https://github.com/strands-agents/sdk-python). You write a Python function with a natural language specification instead of implementation code. You attach post-conditions -- plain Python assertions that define what correct output looks like. When the function is called, the LLM generates code, executes it in your Python process, returns the result as a native object, and the post-conditions verify it. If verification fails, the system retries with the error as feedback. The human never inspects the generated code. The post-conditions do the inspecting -- every time.

If Software 3.0 is "human prompts, LLM generates, human verifies," then I propose that AI Functions are **Software 3.1: human specifies, LLM generates and executes, machine verifies -- at runtime.** Same paradigm -- natural language as the programming interface. But the execution model is different. The LLM isn't producing text for a human to integrate. It's producing code that runs, returning objects your application uses directly, verified by post-conditions on every call. Software 3.1 is a "point release," not a major version bump. The upgrade is in what happens after generation.

This post is a deep dive into what AI Functions are, how they work, and what automated verification makes possible.

## What AI Functions Are

AI Functions is built on top of the [Strands Agents SDK](https://github.com/strands-agents/sdk-python), an open-source framework for building AI agents. AI Functions introduces a single core abstraction: the `@ai_function` decorator. You write a Python function with a natural language specification instead of an implementation body. When the function is called, an LLM generates the implementation, executes it, and returns the result. Optionally -- and this is the important part -- you attach post-conditions that validate the output and trigger automatic retries if validation fails.

The simplest example looks like this:

```python
from ai_functions import ai_function

@ai_function
def translate_text(text: str, lang: str) -> str:
    """
    Translate the text below to the following language: {lang}.
    {text}
    """

result = translate_text("The quarterly results exceeded expectations.", lang="French")
```

You call `translate_text` like any Python function. The decorator intercepts the call, constructs a prompt from the docstring (substituting the arguments), sends it to an LLM, and returns the result as a typed Python string. From the caller's perspective, it's just a function that takes a string and returns a string. The fact that an LLM executed it is an implementation detail.

This on its own is still kinda Software 3.0 -- prompt in, result out. It's pleasant, but it isn't where AI Functions get interesting. They get interesting when you add structure, validation, code execution, multi-agent composition, and async workflows. That's where 3.1 begins.

## Structured Output with Pydantic

AI Functions can return arbitrary typed objects, not just strings. When you specify a Pydantic model as the return type, the framework enforces schema compliance automatically:

```python
from ai_functions import ai_function
from pydantic import BaseModel

class MeetingSummary(BaseModel):
    attendees: list[str]
    key_decisions: list[str]
    action_items: list[str]

@ai_function
def summarize_meeting(transcript: str) -> MeetingSummary:
    """
    Summarize the following meeting transcript in less than 50 words.
    <transcript>
    {transcript}
    </transcript>
    """
```

Call `summarize_meeting(transcript)` and you get back a `MeetingSummary` object with typed fields, IDE autocomplete, and Pydantic's built-in validation. The LLM's output is parsed into the Pydantic model, and if the structure doesn't match, the framework handles the retry. From the caller's perspective, the function returns a typed Python object.

This is a pattern that frameworks like [Instructor](https://python.useinstructor.com/) have established. AI Functions' contribution isn't in structured output itself -- it's in how structured output composes with everything else in the system.

## Post-Conditions

Post-conditions are the core of what makes AI Functions more than a prompting framework. A post-condition is a Python function that validates the output of an AI Function. If validation fails, the error message feeds back to the LLM, which retries. Multiple post-conditions run in parallel, so the LLM receives all failure signals at once and can address them in a single retry.

```python
from ai_functions import ai_function, PostConditionResult
from pydantic import BaseModel

class MeetingSummary(BaseModel):
    attendees: list[str]
    key_decisions: list[str]
    action_items: list[str]

def check_length(response: MeetingSummary):
    total = sum(len(d.split()) for d in response.key_decisions)
    assert total <= 50, f"Key decisions should total under 50 words, got {total}"

@ai_function
def check_quality(response: MeetingSummary) -> PostConditionResult:
    """
    Check if the meeting summary below satisfies the following criteria:
    - Key decisions must be specific and actionable, not vague
    - Action items must each name a responsible person
    <decisions>{response.key_decisions}</decisions>
    <actions>{response.action_items}</actions>
    """

@ai_function(post_conditions=[check_length, check_quality])
def summarize_meeting(transcript: str) -> MeetingSummary:
    """
    Summarize the following meeting transcript in less than 50 words.
    <transcript>
    {transcript}
    </transcript>
    """
```

There are two things to notice here. First, `check_length` is a plain Python function that raises an `AssertionError` on failure. This is a deterministic, inspectable validation -- no LLM involved, no ambiguity. Second, `check_quality` is itself an AI Function that returns a `PostConditionResult` -- a Pydantic model with `passed` (bool) and `message` (str) fields. It uses an LLM to evaluate whether the summary meets quality criteria that are hard to express as assertions -- specificity, actionability, attribution. An AI Function validating another AI Function. The framework treats both identically: if either fails, the error goes back to the generating LLM as feedback.

This creates a self-correcting loop. The generating LLM doesn't need to get it right on the first attempt. It needs to be able to improve given specific feedback about what went wrong. In practice, this means the developer's job shifts from crafting perfect prompts to writing good post-conditions -- a fundamentally different skill.

Of course, we need to understand what is happening here, and that this also opens us up to code retry loops "hidden" in our projects! We will need to ensure we have solid monitoring, and observability before we lean on this too hard.

## Returning Native Python Objects

Most LLM frameworks force output through JSON serialization. AI Functions can return non-serializable Python objects -- DataFrames, SymPy expressions, database connections, anything -- because the generated code runs in the same Python interpreter as your application.

This is the feature that makes AI Functions feel qualitatively different from other frameworks. Consider a format-agnostic data loader that handles purchase records regardless of how they're stored:

```python
from ai_functions import ai_function
from pandas import DataFrame, api

def check_invoice_dataframe(df: DataFrame):
    """Post-condition: validate DataFrame structure."""
    assert {'product_name', 'quantity', 'price', 'purchase_date'}.issubset(df.columns)
    assert api.types.is_integer_dtype(df['quantity']), "quantity must be an integer"
    assert api.types.is_float_dtype(df['price']), "price must be a float"
    assert api.types.is_datetime64_any_dtype(df['purchase_date'])
    assert not df.duplicated(subset=['product_name', 'purchase_date']).any()

@ai_function(
    code_execution_mode="local",
    code_executor_additional_imports=["pandas.*", "sqlite3", "json"],
    post_conditions=[check_invoice_dataframe],
)
def import_invoice(path: str) -> DataFrame:
    """
    The file `{path}` contains purchase logs. Extract them in a DataFrame with columns:
    - product_name (str)
    - quantity (int)
    - price (float)
    - purchase_date (datetime)
    """
```

Call `import_invoice('data/orders.json')` and you get back an actual Pandas DataFrame -- not a JSON representation of one, not a serialized string, a real DataFrame object that you can immediately call `.describe()`, `.groupby()`, or `.plot()` on. Hand it a SQLite file instead and the same function inspects the database schema, writes the appropriate SQL queries, and returns the same validated DataFrame structure.

The developer writes zero format-specific parsing logic. The natural language specification says what the output should contain. The post-conditions verify structural invariants. The LLM figures out how to get from an opaque file to a validated DataFrame, dynamically, at call time.

This works because the framework provides the LLM with a Python executor tool that shares the same runtime as the calling code. The LLM generates Python code, executes it inside your process, and returns the result object directly. No serialization round-trip. The `code_execution_mode="local"` parameter is an explicit opt-in -- the framework doesn't run arbitrary generated code by default, and you declare which imports are allowed.


## Code Execution and the Trust Model

The code execution model deserves closer attention because it reveals AI Functions' deliberate approach to trust.

When `code_execution_mode="local"` is enabled, the LLM can generate and execute Python code within your interpreter. This is powerful -- it's what enables returning DataFrames, running computations, and interacting with the local environment. It's also a security surface. The framework mitigates this through several mechanisms:

- **Explicit opt-in.** Code execution is off by default. You must enable it per function.
- **Import restrictions.** `code_executor_additional_imports` explicitly declares which packages the generated code may use. Anything not listed is unavailable.
- **Post-condition verification.** The output is validated regardless of how it was produced. Even if the generated code takes an unexpected path, the post-conditions catch invalid results.

But the honest assessment is that this is a tradeoff. You're executing LLM-generated code in your process. The framework uses AST-based validation of generated code with controlled imports and timeouts, which attempts to prevent malicious imports and block dangerous operations. But this doesn't offer true sandboxing and doesn't prevent resource exhaustion (infinite loops, excessive memory allocation). For an experiment, with appropriate constraints, this is a reasonable choice. For production workloads, the project recommends running AI Functions inside a container or other isolated environment to provide process-level isolation.

## Multi-Agent Composition

Results from AI Functions compose naturally through regular Python. Since AI Functions return typed objects, you chain them the same way you chain any functions -- by passing outputs as inputs:

```python
from ai_functions import ai_function
from pandas import DataFrame

@ai_function(code_execution_mode="local", code_executor_additional_imports=["pandas.*"])
async def analyze_sales_data(path: str) -> DataFrame:
    """
    Load the sales data from `{path}` and compute a summary DataFrame
    with total revenue, average order value, and top 5 products by volume.
    """

@ai_function
def write_executive_summary(company: str, financials: DataFrame) -> str:
    """
    Write a concise executive summary for {company} highlighting key trends
    and recommendations based on the provided financial data.
    """

financials = await analyze_sales_data("data/q4_sales.csv")
summary = write_executive_summary("Acme Corp", financials)
print("Top Products:", financials.head())
print("Summary:", summary)
```

This is just ordinary function composition. The first function returns a DataFrame; the second takes a DataFrame as input. No special state-passing machinery needed.

For more complex workflows, AI Functions can be used as *tools* by other agents, enabling orchestration patterns where a coordinator delegates to specialized sub-agents:

```python
from ai_functions import ai_function
from ai_functions.types import PostConditionResult
from pydantic import BaseModel, Field
from typing import Literal

@ai_function(
    description="Search the web for a topic and return a cited summary",
    tools=[websearch_tool],
    post_conditions=[check_length, check_citations],
)
def search_agent(query: str, max_words: int = 500) -> str:
    """
    Perform a web search on the following topic and return a summary.
    Every claim must be supported by citations to sources.
    <query>{query}</query>
    """

@ai_function(
    description="Suggest the plan and organization of a report",
    tools=[websearch_tool],
)
def report_planner(topic: str) -> ReportPlan:
    """Generate a plan to write a report on: {topic}"""

@ai_function(tools=[report_planner, search_agent, report.add_section])
def report_orchestrator(topic: str) -> Literal["done"]:
    """
    Write a report on the following topic: {topic}
    """
```

The orchestrator sees `report_planner`, `search_agent`, and `report.add_section` as tools it can call. Each sub-agent runs with its own post-conditions, so the orchestrator receives validated results. The search agent's citations are verified before its results reach the orchestrator. This creates a hierarchy of validated agents -- post-conditions compose across the multi-agent system.

## Async Execution and Parallel Workflows

AI Functions can be defined as `async`, which enables parallel execution of independent tasks:

```python
from ai_functions import ai_function
import asyncio
import pandas as pd

@ai_function(tools=[websearch_tool])
async def research_market(company: str) -> str:
    """Research and summarize the competitive landscape and recent news for: {company}"""

@ai_function(code_execution_mode="local", code_executor_additional_imports=["pandas.*", "yfinance.*"])
async def load_financial_data(stock: str) -> pd.DataFrame:
    """
    Use the `yfinance` Python package to retrieve the historical prices of {stock}
    in the last 30 days. Return a DataFrame with columns [date, price].
    """

@ai_function(code_execution_mode="local", code_executor_additional_imports=["pandas.*", "plotly.*"])
def write_investment_memo(company: str, research: str, financials: pd.DataFrame) -> str:
    """
    Write an investment memo for {company}. Use the market research and financial data:
    {research}
    """

async def due_diligence_workflow(company: str):
    research, financials = await asyncio.gather(
        research_market(company),
        load_financial_data(company)
    )
    write_investment_memo(company, research, financials)
```

The two tasks run concurrently. Since they're independent -- one searches the web, one loads and transforms local data -- parallelism gives you the same results in roughly half the wall-clock time with no additional cost. The results then feed into a synchronous report writer that uses both.

Notice the `tools=[websearch_tool]` parameter. AI Functions can use any [Strands tool](https://github.com/strands-agents/tools). The framework provides built-in tools for Python code execution, and you can pass additional tools (web search, API clients, file I/O) per function. The LLM decides when and how to use them during execution.

## Configuration Sharing

Different parts of a workflow may need different models. A quick validation check doesn't need the same model as a complex analysis. AI Functions use `AIFunctionConfig` objects to share configuration across functions:

```python
from ai_functions import ai_function, AIFunctionConfig
from pandas import DataFrame

class Configs:
    BIG_MODEL = AIFunctionConfig(model="us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    FAST_MODEL = AIFunctionConfig(model="us.anthropic.claude-haiku-4-5-20251001-v1:0")
    DATA_ANALYSIS = AIFunctionConfig(
        model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        code_execution_mode="local",
        code_executor_additional_imports=["pandas.*", "numpy.*"],
    )

@ai_function(config=Configs.DATA_ANALYSIS)
def normalize_dataset(path: str) -> DataFrame:
    """Load, clean, and normalize the dataset at `{path}` into a standard schema."""

@ai_function(config=Configs.FAST_MODEL)
def validate_email(text: str) -> bool:
    """Check if the following string is a valid email address: {text}"""
```

Configs are plain Python objects, so switching the entire pipeline from one model family to another is a single line change. During development, you might route everything through a capable but expensive model. For cost optimization, you swap the config's model reference and see what breaks. Keyword arguments on `@ai_function` override config values for individual functions, so you can specialize without duplicating the entire config.

## Validating More Than Output

One of the more subtle capabilities of the post-condition system is validating *properties* of a result that are hard to express as structural checks. AI-powered post-conditions let you evaluate semantic qualities -- grounding, citation quality, logical consistency -- using one LLM to validate another:

```python
from ai_functions import ai_function, PostConditionResult

@ai_function
def check_citations(summary: str) -> PostConditionResult:
    """
    Validate if all the claims made in the following summary are supported
    by an inline citation to a credible source.
    <summary>
    {summary}
    </summary>
    """

def check_length(summary: str, max_words: int):
    assert len(summary.split()) <= max_words

@ai_function(
    tools=[websearch_tool],
    post_conditions=[check_length, check_citations],
)
def market_researcher(query: str, max_words: int = 500) -> str:
    """
    Research and provide a well-sourced answer to: {query}
    Every claim must be supported by citations to credible sources.
    """
```

The research agent produces a summary. `check_length` verifies the word count deterministically. `check_citations` uses an LLM to evaluate whether each claim is actually backed by a cited source. If the agent hallucinated an answer without doing real research, the citation check catches it and triggers a retry with feedback about specifically which claims lack sources.

This is a different kind of validation from checking output structure. It's using AI to verify AI -- checking semantic properties that are hard to express as assertions. It addresses one of the hardest problems in LLM-based systems: how do you know the model didn't just make something up? Post-conditions don't solve this fully, but they create a second, independent evaluation that meaningfully reduces the failure rate.

## Test Suites as Post-Conditions

The post-condition model has an interesting application to automated coding: use your existing test suite as the post-condition. If the tests pass, the implementation is correct. If they fail, the failures feed back as error messages.

```python
from ai_functions import ai_function
from pydantic import BaseModel
from typing import Any, Literal
import pytest, io
from contextlib import redirect_stderr, redirect_stdout

class FeatureRequest(BaseModel):
    description: str
    test_files: list[str]

# Post-conditions can request original input arguments by name.
# Here, `feature` matches the parameter name of `implement_feature`.
def run_tests(_answer: Any, feature: FeatureRequest):
    stdio_capture = io.StringIO()
    with redirect_stdout(stdio_capture), redirect_stderr(stdio_capture):
        retcode = pytest.main(feature.test_files)
    if retcode:
        raise RuntimeError(stdio_capture.getvalue())

@ai_function(post_conditions=[run_tests])
def implement_feature(feature: FeatureRequest) -> Literal["done"]:
    """
    Implement the following feature in the current code base:
    <feature>{feature.description}</feature>
    Once done the code base should pass the following tests: {feature.test_files}
    """

def run_workflow(features: list[FeatureRequest]):
    for feature in features:
        implement_feature(feature)
```

The AI Function's return value is just the string `"done"` -- it doesn't matter. What matters is the side effect: the code base should now pass the specified tests. The post-condition runs `pytest` and raises if any tests fail. The LLM receives the test output as feedback and keeps iterating until all tests pass.

The documentation notes that agents pass roughly 10-15% more tests when the post-condition is provided in addition to the prompt instruction. The agent is measurably more effective at responding to concrete validation failures than at following written instructions. This aligns with a broader pattern: concrete, automated feedback loops outperform detailed prompting. Which is exactly the argument for 3.1 over 3.0.

## Try It

AI Functions is an experiment. The code is open source at [strands-labs/ai-functions](https://github.com/strands-labs/ai-functions), part of the [Strands Labs GitHub organization](https://github.com/strands-labs) -- a home for experimental projects built on the Strands Agents SDK. Alongside AI Functions, you'll find [Robots](https://github.com/strands-labs/robots) (physical AI agents on edge hardware) and [Robots Sim](https://github.com/strands-labs/robots-sim) (simulated environments for robot development). All three are built on the [Strands Agents SDK](https://github.com/strands-agents/sdk-python), which has been downloaded over 14 million times since its open source release in May 2025. All three are explicitly experimental -- and that's the point. The best way to find out what works in this space is to build things and see what breaks.

Install it with `pip install strands-ai-functions` (or `uv add strands-ai-functions`), clone the [repo](https://github.com/strands-labs/ai-functions) for the full set of examples, and start experimenting.

AI Functions is not a production system. It's a conversation starter and just maybe where Karpathy's version numbering goes next. Try it. Write some post-conditions. See whether defining acceptance criteria feels more natural than auditing LLM output. And then consider: what does 4.0 look like?

We don't know yet. But the experiments have started :)
