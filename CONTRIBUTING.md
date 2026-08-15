# Contributing to AVENZO

Thank you for your interest in contributing to AVENZO — One Product. One Lifecycle. One Intelligence.

This document outlines the conventions, processes, and expectations for contributors.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Development Setup](#development-setup)
3. [Branching Strategy](#branching-strategy)
4. [Commit Message Convention](#commit-message-convention)
5. [Pull Request Process](#pull-request-process)
6. [Code Quality Standards](#code-quality-standards)
7. [Testing Requirements](#testing-requirements)
8. [Documentation Requirements](#documentation-requirements)
9. [Security Guidelines](#security-guidelines)

---

## Code of Conduct

All contributors are expected to maintain professional, respectful communication. Constructive feedback is encouraged; personal attacks are not tolerated.

---

## Development Setup

See [docs/development/DEVELOPMENT_GUIDE.md](docs/development/DEVELOPMENT_GUIDE.md) for detailed local setup instructions.

---

## Branching Strategy

```
main          — Production-ready, protected. Direct pushes disallowed.
develop       — Integration branch. All PRs merge here first.
feature/*     — New feature development (branch from develop)
fix/*         — Bug fixes (branch from develop or main for hotfixes)
docs/*        — Documentation-only changes
chore/*       — Maintenance, dependency updates, config changes
release/*     — Release preparation branches
hotfix/*      — Critical production fixes (branch from main)
```

### Branch Naming Examples

```
feature/inventory-batch-tracking
feature/consumer-pantry-ui
fix/fefo-sorting-bug
docs/api-endpoint-documentation
chore/update-python-dependencies
```

---

## Commit Message Convention

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code restructuring, no feature/fix |
| `test` | Adding or modifying tests |
| `chore` | Build, tooling, dependencies |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |
| `revert` | Reverting a previous commit |

### Examples

```
feat(backend): add FEFO inventory sorting endpoint
fix(auth): resolve JWT token expiry edge case
docs(api): document batch tracking endpoints
chore(deps): upgrade FastAPI to 0.115.x
test(backend): add unit tests for inventory service
```

---

## Pull Request Process

1. **Branch**: Create a branch from `develop` following the naming convention
2. **Develop**: Implement changes with appropriate tests
3. **Self-review**: Review your own diff before submitting
4. **PR Template**: Fill in the pull request template completely
5. **CI**: Ensure all CI checks pass
6. **Review**: Request review from at least one team member
7. **Merge**: Merge only after approval and passing CI

### PR Title Format

Follow the same convention as commit messages:
```
feat(inventory): implement FEFO batch selection logic
```

---

## Code Quality Standards

### Python / Backend

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Docstrings for all public functions and classes
- Keep functions focused — single responsibility
- Service layer for business logic, repository layer for data access
- No hardcoded configuration — use environment variables via `core/config.py`

### TypeScript / React

- Strict TypeScript — avoid `any` types
- Functional components with hooks
- Props defined with explicit interfaces
- API calls only through the `src/api/` service layer
- No hardcoded API URLs — use environment variables

### Flutter / Dart

- Follow official Dart style guidelines
- Riverpod for state management — no mixing of state management libraries
- Separate UI, models, services, and state
- API communication through the `core/services/api_service.dart`
- No hardcoded URLs — use `core/constants/app_constants.dart`

---

## Testing Requirements

- **Backend**: All new endpoints require at least one pytest test
- **React**: Critical components require unit tests
- **Flutter**: Widget tests for critical UI components

Run tests before submitting a PR:

```bash
# Backend
cd backend
pytest

# Business Web
cd business-web
npm run test

# Flutter
cd consumer-app
flutter test
```

---

## Documentation Requirements

- New API endpoints must be documented in `docs/api/api-design.md`
- New database entities must be documented in `docs/database/schema.md`
- Significant architectural decisions must be recorded in `docs/architecture/`
- `CHANGELOG.md` must be updated for each release

---

## Security Guidelines

**NEVER commit:**
- `.env` files
- API keys or tokens
- Database passwords
- Firebase private credentials
- JWT secrets
- `google-services.json` or `GoogleService-Info.plist`
- Any service account files

If you accidentally commit sensitive data:
1. Remove it immediately
2. Rotate the credential immediately (assume it is compromised)
3. Notify the team lead

All secrets must be managed via environment variables only.
