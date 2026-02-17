"""CLI tool to create a blog post from a YouTube video URL."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import boto3
import requests
import yt_dlp


BLOG_ROOT = Path(__file__).resolve().parent.parent.parent
POSTS_DIR = BLOG_ROOT / "_posts"
THUMBNAILS_DIR = BLOG_ROOT / "assets" / "images" / "thumbnails"

BEDROCK_MODEL_ID = "global.anthropic.claude-opus-4-6-v1"


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from various URL formats."""
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query)["v"][0]
        if parsed.path.startswith(("/embed/", "/v/")):
            return parsed.path.split("/")[2]
    raise ValueError(f"Could not extract video ID from: {url}")


def fetch_metadata(url: str) -> dict:
    """Fetch video metadata and auto-captions via yt-dlp."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "vtt",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def clean_vtt(vtt_text: str) -> str:
    """Convert VTT subtitle text to plain text, removing timestamps and duplicates."""
    lines = []
    seen = set()
    for line in vtt_text.splitlines():
        # Skip VTT headers, timestamps, and blank lines
        if (
            line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or "-->" in line
            or not line.strip()
        ):
            continue
        # Strip VTT tags like <c> </c> <00:00:01.234>
        cleaned = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            lines.append(cleaned)
    return " ".join(lines)


def get_transcript(info: dict) -> str:
    """Download and clean auto-captions from yt-dlp info."""
    # Try automatic captions first, then regular subtitles
    for caption_key in ("automatic_captions", "subtitles"):
        captions = info.get(caption_key, {})
        if "en" not in captions:
            continue
        # Find a VTT or srv format URL
        for fmt in captions["en"]:
            if fmt.get("ext") == "vtt" or "vtt" in fmt.get("url", ""):
                resp = requests.get(fmt["url"], timeout=30)
                resp.raise_for_status()
                return clean_vtt(resp.text)
    return ""


def download_thumbnail(video_id: str) -> Path:
    """Download the highest-resolution thumbnail available."""
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
    dest = THUMBNAILS_DIR / f"{video_id}.jpg"

    for quality in ("maxresdefault", "hqdefault"):
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 1000:
            dest.write_bytes(resp.content)
            return dest

    raise RuntimeError(f"Could not download thumbnail for {video_id}")


def call_bedrock(title: str, description: str, transcript: str) -> dict:
    """Call Bedrock to generate summary, SEO description, categories, and tags."""
    prompt = f"""You are helping create a blog post for a YouTube video. The blog belongs to Mike Chambers, an AI/ML engineer.

**Video Title:** {title}

**Video Description:**
{description}

**Transcript:**
{transcript[:12000]}

Based on the above, please provide:

1. A written summary of the video content (2-3 paragraphs). Write for a technical audience. Use third person ("In this video, Mike..."). Make it engaging and informative — this replaces a raw transcript on the blog. Do NOT use markdown headings in the summary.

2. An SEO meta description (max 160 characters). This should be a concise, compelling summary.

3. Suggested categories as a JSON array. Choose from: ["AI", "Tutorials", "Agents"]. Most posts use ["AI", "Tutorials"]. Use ["AI", "Agents"] only if the video is primarily about AI agents.

4. Suggested tags as a JSON array. Always include "video". Choose relevant tags from common ones like: amazon-bedrock, claude, agents, tools, mcp, rag, memory, streaming, inference, code-interpreter, agentcore, dynamodb, partyrock, mistral. Add new short lowercase tags if needed.

Return your response in this exact format:

SUMMARY:
<your summary paragraphs here>

SEO_DESCRIPTION:
<your seo description here>

CATEGORIES:
<json array>

TAGS:
<json array>"""

    client = boto3.client("bedrock-runtime")
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1024},
    )

    text = response["output"]["message"]["content"][0]["text"]
    return parse_bedrock_response(text)


def parse_bedrock_response(text: str) -> dict:
    """Parse the structured response from Bedrock."""
    result = {}

    # Extract summary
    summary_match = re.search(
        r"SUMMARY:\s*\n(.*?)(?=\nSEO_DESCRIPTION:)", text, re.DOTALL
    )
    result["summary"] = summary_match.group(1).strip() if summary_match else ""

    # Extract SEO description
    seo_match = re.search(
        r"SEO_DESCRIPTION:\s*\n(.*?)(?=\nCATEGORIES:)", text, re.DOTALL
    )
    result["seo_description"] = seo_match.group(1).strip() if seo_match else ""

    # Extract categories
    cat_match = re.search(r"CATEGORIES:\s*\n(\[.*?\])", text, re.DOTALL)
    result["categories"] = json.loads(cat_match.group(1)) if cat_match else ["AI", "Tutorials"]

    # Extract tags
    tags_match = re.search(r"TAGS:\s*\n(\[.*?\])", text, re.DOTALL)
    result["tags"] = json.loads(tags_match.group(1)) if tags_match else ["video"]

    # Ensure "video" tag is always present
    if "video" not in result["tags"]:
        result["tags"].append("video")

    return result


def extract_chapters(description: str) -> list[dict]:
    """Extract chapter timestamps and titles from the YouTube description."""
    chapters = []
    for match in re.finditer(
        r"(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.+)", description
    ):
        timestamp = match.group(1)
        title = match.group(2).strip()
        # Normalise to MM:SS or HH:MM:SS
        parts = timestamp.split(":")
        if len(parts) == 2:
            timestamp = f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        chapters.append({"timestamp": timestamp, "title": title})
    return chapters


SOCIAL_DOMAINS = {
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "twitch.tv",
    "facebook.com",
    "tiktok.com",
    "discord.gg",
}


def extract_links(description: str) -> list[dict]:
    """Extract labelled links from the YouTube description."""
    links = []
    for match in re.finditer(
        r"(.+?)\s*[-–—:]\s*(https?://\S+)", description
    ):
        label = match.group(1).strip()
        url = match.group(2).strip()
        # Skip YouTube, thumbnail, and social media URLs
        parsed = urlparse(url)
        domain = (parsed.hostname or "").removeprefix("www.")
        if "youtube.com" in url or "youtu.be" in url:
            continue
        if domain in SOCIAL_DOMAINS:
            continue
        links.append({"label": label, "url": url})
    return links


def slugify(title: str, max_length: int = 60) -> str:
    """Convert a title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug).strip("-")
    # Truncate at word boundary
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug


def build_post(
    video_id: str,
    title: str,
    upload_date: str,
    bedrock: dict,
    chapters: list[dict],
    links: list[dict],
) -> str:
    """Build the full markdown post content."""
    # Frontmatter
    # Escape quotes in title and description for YAML
    safe_title = title.replace('"', '\\"')
    safe_desc = bedrock["seo_description"].replace('"', '\\"')

    # Format as YAML flow sequences without quotes (matching existing posts)
    cats = ", ".join(bedrock["categories"])
    tags = ", ".join(bedrock["tags"])

    lines = [
        "---",
        f'title: "{safe_title}"',
        f"date: {upload_date}",
        f"categories: [{cats}]",
        f"tags: [{tags}]",
        f'description: "{safe_desc}"',
        "---",
        "",
        f"{{% include embed/youtube.html id='{video_id}' %}}",
        "",
        bedrock["summary"],
    ]

    # Chapters section
    if chapters:
        lines.append("")
        lines.append("## Chapters")
        lines.append("")
        for ch in chapters:
            lines.append(f"- **{ch['timestamp']}** - {ch['title']}")

    # Links section
    if links:
        lines.append("")
        lines.append("## Links & Resources")
        lines.append("")
        for link in links:
            lines.append(f"- [{link['label']}]({link['url']})")

    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run new-post <youtube-url>")
        sys.exit(1)

    url = sys.argv[1]

    # 1. Extract video ID
    video_id = extract_video_id(url)
    print(f"Video ID: {video_id}")

    # 2. Fetch metadata via yt-dlp
    print("Fetching video metadata...")
    info = fetch_metadata(url)
    title = info.get("title", "Untitled")
    description = info.get("description", "")
    upload_date_raw = info.get("upload_date", "")  # YYYYMMDD format
    if upload_date_raw:
        upload_date = f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:8]}"
    else:
        from datetime import date
        upload_date = date.today().isoformat()

    print(f"Title: {title}")
    print(f"Upload date: {upload_date}")

    # 3. Download transcript
    print("Downloading transcript...")
    transcript = get_transcript(info)
    if not transcript:
        print("Warning: No English auto-captions found. Proceeding without transcript.")

    # 4. Download thumbnail
    print("Downloading thumbnail...")
    thumb_path = download_thumbnail(video_id)
    print(f"Thumbnail saved: {thumb_path.relative_to(BLOG_ROOT)}")

    # 5. Call Bedrock for summary
    print("Generating summary via Bedrock...")
    bedrock = call_bedrock(title, description, transcript)

    # 6. Extract chapters and links from description
    chapters = extract_chapters(description)
    links = extract_links(description)

    # 7. Build and write the post
    slug = slugify(title)
    filename = f"{upload_date}-{slug}.md"
    post_path = POSTS_DIR / filename

    post_content = build_post(video_id, title, upload_date, bedrock, chapters, links)
    post_path.write_text(post_content)

    print(f"\nPost created: {post_path.relative_to(BLOG_ROOT)}")
    print(f"Categories: {bedrock['categories']}")
    print(f"Tags: {bedrock['tags']}")
    if chapters:
        print(f"Chapters: {len(chapters)}")
    if links:
        print(f"Links: {len(links)}")


if __name__ == "__main__":
    main()
