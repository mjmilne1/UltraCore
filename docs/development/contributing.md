# Contributing to UltraCore

**TuringDynamics / Richelou Pty Ltd - Proprietary**

---

## 👤 Solo Development

Currently maintained by a single developer. This doc is for future reference.

---

## 🛠️ Quick Start

\\\ash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env

# Before committing
black src/ tests/
ruff check --fix src/ tests/
pytest
\\\

---

## 📋 Workflow

### Simple Flow (solo development)
\\\ash
# Work directly on main for quick changes
git add .
git commit -m "feat: Add feature"
git push

# For bigger features, use branches
git checkout -b feature/new-thing
# ... work ...
git checkout main
git merge feature/new-thing
git push
\\\

### Branch Names
- \eature/\ - New features
- \ix/\ - Bug fixes
- \efactor/\ - Code cleanup
- \docs/\ - Documentation

---

## ✅ Before Pushing

\\\ash
# Quick checks
black src/ tests/           # Format
ruff check src/ tests/      # Lint
pytest                      # Test
\\\

---

## 🔒 Security

Never commit:
- .env files
- API keys
- Credentials
- Customer data

---

## 📝 Commit Messages

Use conventional commits:
- \eat:\ - New feature
- \ix:\ - Bug fix
- \docs:\ - Documentation
- \efactor:\ - Code refactoring
- \	est:\ - Tests
- \chore:\ - Maintenance

Example: \eat: Add loan approval ML model\

---

**© 2025 Richelou Pty Ltd. All Rights Reserved.**
