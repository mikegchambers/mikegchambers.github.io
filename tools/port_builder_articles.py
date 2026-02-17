"""One-off script to port Builder Center articles to the blog via Tavily Extract."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import boto3
import requests

BLOG_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = BLOG_ROOT / "_posts"
TAVILY_API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""

BEDROCK_MODEL_ID = "global.anthropic.claude-opus-4-6-v1"

URLS = [
    "https://builder.aws.com/content/34MfVfB260mYD9XCqluhtT0bGZD/streaming-agents-on-aws",
    "https://builder.aws.com/content/36blrJj0hEhsyPWbrxJdmpOIaCu/complete-tutorial-streaming-agents-on-aws",
    # Skipped: turn-your-ai-script (JS-only page, Tavily can't render; already has matching blog post)
    # Skipped: how-to-prompt-mistral (JS-only page, Tavily can't render)
    "https://builder.aws.com/content/2ogvbYrb6RzMIvNX3ZvQIYSBa9j/my-generative-adventure-game",
    "https://builder.aws.com/content/2jRC6PJNXs2BOlHMCwnR2x9lw92/supercharge-your-browser-unleashing-ai-powered-tampermonkey-magic",
    "https://builder.aws.com/content/2gw7NsgJM0H7RrlJL5sJQRQNJhD/fast-pre-trained-model-deployment-the-code-only-approach",
    "https://builder.aws.com/content/2cZUf75V80QCs8dBAzeIANl0wzU/mistral-ai-winds-of-change",
    "https://builder.aws.com/content/2ZVa61RxToXUFzcuY8Hbut6L150/what-is-an-instruct-model-instruction-and-chat-fine-tuning",
    "https://builder.aws.com/content/2dfToY7frDS4y8LsTkntgBzORju/watch-hands-on-with-haiku-on-amazon-bedrock",
]


def fetch_articles(urls: list[str]) -> list[dict]:
    """Fetch article content via Tavily Extract API."""
    results = []
    # Tavily supports up to 20 URLs per batch
    resp = requests.post(
        "https://api.tavily.com/extract",
        json={"api_key": TAVILY_API_KEY, "urls": urls},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    for r in data.get("results", []):
        results.append({"url": r["url"], "content": r["raw_content"]})
    for f in data.get("failed_results", []):
        print(f"  FAILED: {f.get('url', 'unknown')} - {f.get('error', 'unknown error')}")
    return results


def extract_article(raw: str) -> dict:
    """Extract title, date, and article body from raw Tavily content."""
    # Find the title (heading with ====)
    title_match = re.search(r"^(.+)\n={3,}", raw, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    # Strip " | AWS Builder Center" suffix
    title = re.sub(r"\s*\|\s*AWS Builder Center$", "", title)

    # Find published date
    date_match = re.search(r"Published\s+(\w+\s+\d{1,2},?\s+\d{4})", raw)
    if date_match:
        date_str = date_match.group(1).replace(",", "")
        try:
            pub_date = datetime.strptime(date_str, "%b %d %Y")
        except ValueError:
            pub_date = datetime.strptime(date_str, "%B %d %Y")
    else:
        pub_date = None

    # Extract article body: from after the date/separator to before comments/footer
    # Find the start: after "Published..." and the separator "---" or "* * *"
    start_markers = [
        r"Published\s+\w+\s+\d{1,2},?\s+\d{4}\s*\n+\*\s*\*\s*\*\s*\n+\d+\s+\d+\s*\n+\*\s*\*\s*\*",
        r"Published\s+\w+\s+\d{1,2},?\s+\d{4}\s*\n+\*\s*\*\s*\*",
    ]
    body_start = None
    for pattern in start_markers:
        m = re.search(pattern, raw)
        if m:
            body_start = m.end()
            break
    if body_start is None:
        # Fallback: start after the title block
        if title_match:
            body_start = title_match.end() + 1

    # Find the end: before tag links, "Any opinions", or "Comments"
    end_markers = [
        r"\n\[#\s+\w",  # Tag links like [# game-challenge]
        r"\nAny opinions in this",
        r"\nComments\s*\(\d+\)",
        r"\n\*\s*\*\s*\*\s*\n+\d+\s+\d+\s*\n+\*\s*\*\s*\*\s*\nComments",
        r"\n\*\s*\*\s*\*\s*\n+\d+\s+\d+\s*$",
    ]
    body_end = len(raw)
    for pattern in end_markers:
        m = re.search(pattern, raw)
        if m and m.start() < body_end:
            body_end = m.start()

    body = raw[body_start:body_end].strip() if body_start else ""

    # Extract builder center tags
    bc_tags = re.findall(r"\[#\s*(\S+)\]", raw)

    return {
        "title": title,
        "date": pub_date,
        "body": body,
        "bc_tags": bc_tags,
    }


def clean_body(body: str) -> str:
    """Clean up the article body markdown."""
    # Remove duplicate image references that appear at the end
    # (Tavily sometimes duplicates images)
    lines = body.split("\n")

    # Remove any remaining navigation fragments
    cleaned = []
    skip_patterns = [
        r"^Sign in to comment",
        r"^Sign in$",
        r"^Newest$",
        r"^Sort by$",
        r"^No more comments",
        r"^\[About\]",
        r"^\[Builder Center\]",
        r"^Cookie preferences$",
        r"^Your Privacy Choices$",
        r"^\*   \[Home\]",
        r"^\*   \[Learn\]",
        r"^\*   \[Build\]",
        r"^\*   \[Connect\]",
        r"^\*   \[Community\]",
        r"^\*   \[Wishlist\]",
        r"^Explore AWS",
        r"^Follow$",
        r"^AWS Employee$",
    ]
    for line in lines:
        if any(re.match(p, line.strip()) for p in skip_patterns):
            continue
        cleaned.append(line)

    result = "\n".join(cleaned).strip()

    # Collapse 3+ consecutive blank lines to 2
    result = re.sub(r"\n{3,}", "\n\n", result)

    # Clean image alt text: remove "Image N: " prefix
    result = re.sub(r"!\[Image \d+: ", "![", result)

    # Remove duplicate images that Tavily appends at the end
    # (identical image references appearing after the article body)
    seen_images = set()
    final_lines = []
    for line in result.split("\n"):
        img_match = re.match(r"!\[.*?\]\((.*?)\)", line.strip())
        if img_match:
            url = img_match.group(1)
            if url in seen_images:
                continue  # Skip duplicate
            seen_images.add(url)
        final_lines.append(line)
    result = "\n".join(final_lines)

    return result


def generate_metadata(title: str, body: str, bc_tags: list[str]) -> dict:
    """Use Bedrock to generate SEO description, categories, and tags."""
    # Truncate body for the prompt
    body_preview = body[:6000]

    prompt = f"""You are generating metadata for a blog post being ported from the AWS Builder Center to a personal tech blog by Mike Chambers (AI/ML engineer).

**Article Title:** {title}

**Builder Center Tags:** {', '.join(bc_tags) if bc_tags else 'none'}

**Article Content (preview):**
{body_preview}

Generate:

1. An SEO meta description (max 160 characters). Concise and compelling.

2. Categories as a JSON array. Choose from: ["AI", "Tutorials"], ["AI", "Agents"], ["AI", "Models"], ["AI", "Security"]. Most tutorials use ["AI", "Tutorials"].

3. Tags as a JSON array. Choose relevant lowercase tags from: amazon-bedrock, agents, tools, streaming, inference, code-interpreter, memory, dynamodb, claude, mistral, rag, fine-tuning, sagemaker, lambda, tampermonkey. Add new short lowercase tags if needed. Do NOT include "video".

Return in this exact format:

SEO_DESCRIPTION:
<description>

CATEGORIES:
<json array>

TAGS:
<json array>"""

    client = boto3.client("bedrock-runtime")
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 512},
    )
    text = response["output"]["message"]["content"][0]["text"]

    result = {}
    seo_match = re.search(r"SEO_DESCRIPTION:\s*\n(.*?)(?=\nCATEGORIES:)", text, re.DOTALL)
    result["description"] = seo_match.group(1).strip() if seo_match else title

    cat_match = re.search(r"CATEGORIES:\s*\n(\[.*?\])", text, re.DOTALL)
    result["categories"] = json.loads(cat_match.group(1)) if cat_match else ["AI", "Tutorials"]

    tags_match = re.search(r"TAGS:\s*\n(\[.*?\])", text, re.DOTALL)
    result["tags"] = json.loads(tags_match.group(1)) if tags_match else ["amazon-bedrock"]

    return result


def slugify(title: str, max_length: int = 60) -> str:
    slug = title.lower()
    # Replace dashes and special chars with spaces first, then collapse
    slug = re.sub(r"[^a-z0-9\s]", " ", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug


def write_post(article: dict, metadata: dict, source_url: str) -> Path:
    """Write the blog post markdown file."""
    date_str = article["date"].strftime("%Y-%m-%d") if article["date"] else "2024-01-01"
    safe_title = article["title"].replace('"', '\\"')
    safe_desc = metadata["description"].replace('"', '\\"')
    cats = ", ".join(metadata["categories"])
    tags = ", ".join(metadata["tags"])

    body = clean_body(article["body"])

    frontmatter = f'''---
title: "{safe_title}"
date: {date_str}
categories: [{cats}]
tags: [{tags}]
description: "{safe_desc}"
---

> This article was originally published on the [AWS Builder Center]({source_url}).

{body}
'''

    slug = slugify(article["title"])
    filename = f"{date_str}-{slug}.md"
    post_path = POSTS_DIR / filename
    post_path.write_text(frontmatter)
    return post_path


def main():
    if not TAVILY_API_KEY:
        print("Usage: python port_builder_articles.py <tavily-api-key>")
        sys.exit(1)

    print(f"Fetching {len(URLS)} articles from Builder Center via Tavily...")
    articles = fetch_articles(URLS)
    print(f"Successfully fetched {len(articles)} articles.\n")

    for article_data in articles:
        url = article_data["url"]
        raw = article_data["content"]

        print(f"Processing: {url}")

        # Extract article content
        article = extract_article(raw)
        if not article["title"]:
            print(f"  WARNING: Could not extract title, skipping.")
            continue

        print(f"  Title: {article['title']}")
        print(f"  Date: {article['date']}")

        # Generate metadata via Bedrock
        print(f"  Generating metadata via Bedrock...")
        metadata = generate_metadata(article["title"], article["body"], article["bc_tags"])

        # Write the post
        post_path = write_post(article, metadata, url)
        print(f"  Written: {post_path.relative_to(BLOG_ROOT)}")
        print(f"  Categories: {metadata['categories']}, Tags: {metadata['tags']}")
        print()

    print("Done!")


if __name__ == "__main__":
    main()
