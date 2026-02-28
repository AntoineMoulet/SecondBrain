# Second Brain — Vault

Vault Obsidian-compatible. Stocké dans GitHub, accessible par les LLMs.

## Structure

```
vault/
├── _context/                    ← Contexte personnel pour les LLMs
│   ├── about-me.md              # Qui tu es, ton rôle, tes contraintes
│   ├── thinking-style.md        # Comment tu penses et écris
│   └── current-focus.md         # Sur quoi tu bosses en ce moment
│
├── projects/                    ← Contexte par projet
│   └── alan-play/
│       └── overview.md          # Tout sur Alan Play
│
├── captures/                    ← Captures brutes (Telegram bot, scripts reMarkable)
│   └── YYYY-MM-DD-HHMMSS-topic.md
│
└── writing/                     ← Drafts de communications (interne + public)
```

---

## Utiliser ce vault avec un LLM

### Option A — Injection manuelle (disponible maintenant)

Copie les fichiers contexte en début de conversation :

```
[Colle le contenu de _context/about-me.md]
[Colle le contenu de _context/thinking-style.md]
[Colle le contenu de _context/current-focus.md]
[Colle le contenu de projects/alan-play/overview.md si pertinent]

--- Maintenant ma question : ...
```

### Option B — Claude Code avec MCP (phase 3)

Une fois le MCP server déployé, Claude Code accède automatiquement au vault.
Configuration dans `~/.claude/settings.json` (à venir).

---

## Flows de capture

### Telegram bot (phase 2 — migration en cours)
Le bot écrit dans `captures/` au format markdown avec frontmatter YAML :
```markdown
---
date: 2026-02-28T14:30:00
type: text | voice
topic: [topic extrait par LLM]
summary: [résumé extrait par LLM]
---
Contenu du message...
```

### Scripts reMarkable (phase 4)
Les scripts Python existants écriront dans :
- `captures/` pour les notes de lecture brutes
- `writing/` pour les drafts déjà orientés communication

### Manuel
Crée directement un fichier `.md` dans le bon dossier depuis Obsidian ou tout éditeur.

---

## Roadmap

- [x] Phase 1 : Vault structure + fichiers `_context/`
- [ ] Phase 2 : Migration Telegram bot → `captures/` (markdown au lieu de Notion)
- [ ] Phase 3 : MCP server (accès automatique pour Claude Code et Claude.ai)
- [ ] Phase 4 : Intégration scripts reMarkable
