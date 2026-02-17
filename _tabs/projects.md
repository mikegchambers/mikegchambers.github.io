---
# the default layout is 'page'
icon: fas fa-project-diagram
order: 2
---

<style>
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}
.project-card {
  border: 1px solid var(--card-border-color, #e0e0e0);
  border-radius: 0.75rem;
  padding: 1.5rem;
  background: var(--card-bg, #fff);
  transition: transform 0.2s, box-shadow 0.2s;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
}
.project-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  text-decoration: none;
  color: inherit;
}
.project-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
}
.project-card p {
  margin: 0 0 1rem 0;
  color: var(--text-muted-color, #6c757d);
  font-size: 0.95rem;
  flex-grow: 1;
}
.project-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--text-muted-color, #6c757d);
}
.project-meta span {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
</style>

<div class="project-grid">
{% for project in site.data.projects %}
  <a href="https://github.com/{{ project.repo }}" class="project-card">
    <h3><i class="fab fa-github"></i> {{ project.name }}</h3>
    <p>{{ project.description }}</p>
    <div class="project-meta">
      <span><i class="fas fa-circle" style="color: {{ project.language_color }}; font-size: 0.7rem;"></i> {{ project.language }}</span>
      <span><i class="fas fa-star"></i> {{ project.stars }}</span>
    </div>
  </a>
{% endfor %}
</div>
