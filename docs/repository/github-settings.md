# 🔧 GitHub Settings Guide

Comprehensive guide to optimizing GitHub repository settings for institutional-grade quality.

---

## 📚 Quick Links

- **[General Settings](#general-settings)** - Basic configuration
- **[Access Control](#access-control)** - Permissions and teams
- **[Branch Protection](#branch-protection)** - Branch rules
- **[Security Settings](#security-settings)** - Security features
- **[Integration Settings](#integration-settings)** - Apps and webhooks
- **[Repository Features](#repository-features)** - GitHub features

---

## ⚙️ General Settings

### Repository Details

**Name:** UltraCore  
**Description:** Enterprise-grade banking core system with event sourcing, data mesh, and agentic AI

**Topics (Tags):**
```
banking, fintech, event-sourcing, data-mesh, domain-driven-design,
agentic-ai, python, fastapi, postgresql, kafka, redis
```

**Website:** https://turingdynamics.com.au

**Visibility:** Private (recommended for proprietary code)

---

### Features

**Enable:**
- ✅ Issues - Bug tracking and feature requests
- ✅ Projects - Project management
- ✅ Wiki - Additional documentation (optional)
- ✅ Discussions - Community discussions
- ✅ Sponsorships - GitHub Sponsors (if applicable)

**Disable:**
- ❌ Wikis - Use docs/ directory instead for version control

---

### Pull Requests

**Merge Options:**
- ✅ Allow squash merging (recommended)
- ✅ Allow merge commits
- ❌ Allow rebase merging (can cause issues)

**Default Merge Message:**
- Squash: "Pull request title and description"
- Merge commit: "Pull request title"

**Automatically Delete Head Branches:**
- ✅ Enabled (keeps repository clean)

---

### Archives

**Include Git LFS objects in archives:**
- ✅ Enabled (if using Git LFS)

---

## 🔐 Access Control

### Collaborators & Teams

**Team Structure:**

```
Organization: TuringDynamics3000
├── Owners (Admin access)
│   └── Project owner
├── Core Team (Write access)
│   ├── Lead developers
│   └── Senior engineers
├── Contributors (Write access)
│   └── Regular contributors
└── Reviewers (Read access)
    └── Code reviewers
```

**Permission Levels:**

| Role | Access | Permissions |
|------|--------|-------------|
| **Admin** | Full | All permissions, settings, deletion |
| **Maintain** | High | Manage repo without sensitive actions |
| **Write** | Standard | Push, merge, manage issues/PRs |
| **Triage** | Limited | Manage issues and PRs only |
| **Read** | View | View and clone only |

---

### CODEOWNERS

Create `.github/CODEOWNERS` file:

```
# Global owners
* @owner-username

# Domain-specific owners
/src/ultracore/domains/accounts/ @accounts-team
/src/ultracore/domains/lending/ @lending-team
/src/ultracore/domains/wealth/ @wealth-team

# Infrastructure
/infrastructure/ @devops-team
/.github/ @devops-team

# Documentation
/docs/ @docs-team
*.md @docs-team

# Security
/SECURITY.md @security-team
/src/ultracore/security/ @security-team
```

---

## 🛡️ Branch Protection

### Main Branch Protection

**Settings → Branches → Add rule**

**Branch name pattern:** `main`

**Required:**
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1 (minimum)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners
  - ❌ Restrict who can dismiss pull request reviews (optional)
  - ❌ Allow specified actors to bypass required pull requests (optional)

- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - **Required checks:**
    - `lint` - Code linting
    - `type-check` - Type checking
    - `unit-tests` - Unit tests
    - `integration-tests` - Integration tests
    - `security-scan` - Security scanning
    - `coverage` - Code coverage

- ✅ Require conversation resolution before merging
- ✅ Require signed commits (recommended)
- ✅ Require linear history (optional, keeps history clean)
- ✅ Require deployments to succeed before merging (if applicable)

**Restrictions:**
- ❌ Lock branch (only for emergency)
- ❌ Do not allow bypassing the above settings
- ✅ Allow force pushes: Nobody
- ✅ Allow deletions: Nobody

---

### Development Branch Protection

**Branch name pattern:** `develop`

**Settings:**
- ✅ Require a pull request before merging
  - Require approvals: 1
- ✅ Require status checks to pass before merging
  - Same checks as main branch
- ✅ Require conversation resolution before merging

---

### Release Branch Protection

**Branch name pattern:** `release/*`

**Settings:**
- ✅ Require a pull request before merging
  - Require approvals: 2 (higher for releases)
- ✅ Require status checks to pass before merging
- ✅ Require review from Code Owners
- ✅ Require signed commits

---

## 🔒 Security Settings

### Security & Analysis

**Dependency Graph:**
- ✅ Enabled (track dependencies)

**Dependabot Alerts:**
- ✅ Enabled (security vulnerabilities)
- ✅ Automatically dismiss low severity alerts (optional)

**Dependabot Security Updates:**
- ✅ Enabled (automatic PRs for security fixes)

**Dependabot Version Updates:**
- ✅ Enabled (automatic PRs for version updates)
- Configure in `.github/dependabot.yml`

**Code Scanning:**
- ✅ Enabled (CodeQL analysis)
- Configure in `.github/workflows/security.yml`

**Secret Scanning:**
- ✅ Enabled (detect committed secrets)
- ✅ Push protection (prevent secret commits)

---

### Dependabot Configuration

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    open-pull-requests-limit: 10
    reviewers:
      - "devops-team"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore"
      include: "scope"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "devops-team"
    labels:
      - "dependencies"
      - "github-actions"

  # Docker
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "devops-team"
    labels:
      - "dependencies"
      - "docker"
```

---

### Security Advisories

**Private Security Advisories:**
- ✅ Enabled (coordinate vulnerability fixes)

**Process:**
1. Create private advisory
2. Invite collaborators
3. Develop fix in private fork
4. Publish advisory with fix

---

## 🔗 Integration Settings

### GitHub Actions

**Settings → Actions → General**

**Actions Permissions:**
- ✅ Allow all actions and reusable workflows (or restrict to verified only)

**Workflow Permissions:**
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

**Artifact and Log Retention:**
- 90 days (default)

**Fork Pull Request Workflows:**
- ✅ Require approval for first-time contributors
- ✅ Require approval for all outside collaborators

---

### Webhooks

**Common Webhooks:**

**CI/CD Integration:**
```
Payload URL: https://ci.example.com/webhook
Content type: application/json
Events: Push, Pull request
```

**Slack Notifications:**
```
Payload URL: https://hooks.slack.com/services/...
Events: Push, Pull request, Issues, Releases
```

**Deployment Notifications:**
```
Payload URL: https://deploy.example.com/webhook
Events: Push, Release
```

---

### GitHub Apps

**Recommended Apps:**

**Code Quality:**
- CodeClimate - Code quality analysis
- Codecov - Code coverage tracking
- SonarCloud - Code quality and security

**Security:**
- Snyk - Dependency vulnerability scanning
- GitGuardian - Secret scanning
- Dependabot - Automated dependency updates

**Productivity:**
- Renovate - Dependency updates
- Mergify - Automated PR merging
- Stale - Close stale issues/PRs

---

## 📋 Repository Features

### Issues

**Issue Templates:**
- ✅ Bug report template
- ✅ Feature request template
- ✅ Documentation template

**Labels:**

**Type:**
- `bug` - Bug reports
- `enhancement` - Feature requests
- `documentation` - Documentation
- `question` - Questions

**Priority:**
- `critical` - Critical issues
- `high` - High priority
- `medium` - Medium priority
- `low` - Low priority

**Status:**
- `triage` - Needs triage
- `in-progress` - Being worked on
- `blocked` - Blocked
- `wontfix` - Won't fix

**Area:**
- `accounts` - Account management
- `lending` - Lending
- `wealth` - Wealth management
- `payments` - Payments
- `api` - API
- `infrastructure` - Infrastructure

---

### Pull Requests

**PR Template:**
- ✅ Comprehensive PR template
- ✅ Checklist for authors
- ✅ Checklist for reviewers

**Auto-merge:**
- ✅ Enable auto-merge for Dependabot PRs (after CI passes)

---

### Projects

**Project Boards:**

**Development Board:**
- Columns: Backlog, Todo, In Progress, Review, Done
- Automation: Move cards based on PR/issue status

**Release Planning:**
- Columns: Planned, In Development, Testing, Released
- Track features by release

---

### Discussions

**Categories:**

- 💬 General - General discussions
- 💡 Ideas - Feature ideas
- 🙏 Q&A - Questions and answers
- 📣 Announcements - Project announcements
- 🐛 Troubleshooting - Help with issues

---

## 📊 Insights & Analytics

### Pulse

**Monitor:**
- Merged pull requests
- Opened issues
- Closed issues
- New contributors

**Review:** Weekly

---

### Contributors

**Track:**
- Commit activity
- Code additions/deletions
- Top contributors

**Use for:** Recognition and team metrics

---

### Traffic

**Monitor:**
- Unique visitors
- Page views
- Clone activity
- Popular content

**Review:** Monthly

---

### Dependency Graph

**Review:**
- Direct dependencies
- Transitive dependencies
- Dependents (who uses this repo)

**Update:** Automatically

---

## 🔔 Notifications

### Watch Settings

**Recommended for Team:**
- ✅ Participating and @mentions
- ✅ All activity (for core team)
- ✅ Releases only (for users)

**Custom:**
- ✅ Issues
- ✅ Pull requests
- ✅ Releases
- ✅ Discussions
- ❌ Security alerts (separate notification)

---

### Email Notifications

**Configure:**
- Issue assignments
- PR reviews requested
- PR mentions
- Security alerts
- Release notifications

---

## 📝 Repository Metadata Files

### Required Files

**Root Directory:**
- ✅ `README.md` - Project overview
- ✅ `LICENSE` - License information
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `CODE_OF_CONDUCT.md` - Code of conduct
- ✅ `SECURITY.md` - Security policy
- ✅ `.gitignore` - Ignored files
- ✅ `.gitattributes` - Git attributes

**.github Directory:**
- ✅ `CODEOWNERS` - Code ownership
- ✅ `dependabot.yml` - Dependabot config
- ✅ `ISSUE_TEMPLATE/` - Issue templates
- ✅ `PULL_REQUEST_TEMPLATE.md` - PR template
- ✅ `workflows/` - GitHub Actions

**docs Directory:**
- ✅ Comprehensive documentation
- ✅ Architecture docs
- ✅ API docs
- ✅ Developer guides

---

## ✅ Configuration Checklist

### Initial Setup

- [ ] Set repository description
- [ ] Add topics/tags
- [ ] Configure visibility (private/public)
- [ ] Enable required features
- [ ] Configure merge options
- [ ] Enable auto-delete branches

### Security

- [ ] Enable Dependabot alerts
- [ ] Enable Dependabot security updates
- [ ] Enable code scanning (CodeQL)
- [ ] Enable secret scanning
- [ ] Enable push protection
- [ ] Configure security policy

### Branch Protection

- [ ] Protect main branch
- [ ] Require PR reviews
- [ ] Require status checks
- [ ] Require signed commits
- [ ] Prevent force pushes
- [ ] Prevent deletions

### Access Control

- [ ] Set up teams
- [ ] Configure permissions
- [ ] Add CODEOWNERS file
- [ ] Review collaborators
- [ ] Audit access regularly

### Integrations

- [ ] Configure GitHub Actions
- [ ] Set up webhooks
- [ ] Install required apps
- [ ] Configure notifications
- [ ] Test integrations

### Documentation

- [ ] Add README.md
- [ ] Add CONTRIBUTING.md
- [ ] Add CODE_OF_CONDUCT.md
- [ ] Add SECURITY.md
- [ ] Add issue templates
- [ ] Add PR template
- [ ] Add comprehensive docs

---

## 🔄 Regular Maintenance

### Weekly

- [ ] Review open issues
- [ ] Review open PRs
- [ ] Check CI/CD status
- [ ] Review Dependabot PRs
- [ ] Monitor security alerts

### Monthly

- [ ] Review access permissions
- [ ] Update documentation
- [ ] Review labels and projects
- [ ] Check repository insights
- [ ] Review branch protection rules

### Quarterly

- [ ] Security audit
- [ ] Dependency audit
- [ ] Access control review
- [ ] Documentation review
- [ ] Settings review

---

## 📚 Additional Resources

### GitHub Documentation

- **[Repository Settings](https://docs.github.com/en/repositories)** - Official docs
- **[Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)** - Branch rules
- **[Security Features](https://docs.github.com/en/code-security)** - Security docs
- **[GitHub Actions](https://docs.github.com/en/actions)** - CI/CD docs

### Best Practices

- **[GitHub Best Practices](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions)** - Community guidelines
- **[Security Best Practices](https://docs.github.com/en/code-security/getting-started/securing-your-repository)** - Security guide

---

**Last Updated:** November 14, 2024
