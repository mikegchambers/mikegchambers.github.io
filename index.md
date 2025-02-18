---
layout: home
title: Mike's Notes
---

{{ content }}

<div class="post-list">
  {% for post in site.posts %}
    <article class="post-preview">
      <h2>
        <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      </h2>
      <p class="post-meta">{{ post.date | date: "%B %-d, %Y" }}</p>
      {% if post.excerpt %}
        {{ post.excerpt }}
      {% endif %}
    </article>
  {% endfor %}
</div>
