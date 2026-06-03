---
trigger: model_decision
description: Implementation rules for the ontoNgn project, emphasizing explicit user feedback and incremental development.
---

# Implementation Rules

## 1. Command Authorization & Feedback Protocol (CRITICAL RULE)

> [!IMPORTANT]
> **This is a critical rule in the project. Always ensure the user is explicitly aware of your actions.**

- **Pre-Authorization Protocol**: Whenever you intend to propose a command for execution (e.g., shell commands, running scripts) or ask for user approval/input, you are **STRICTLY REQUIRED** to present the command or question clearly in the chat and wait for explicit user approval before proceeding.
- **Explicit Feedback**: Do not complete tasks silently. Ensure the user is explicitly aware of the current status and any decisions made at every critical step through the chat interface.

## 2. Mandatory Pre-Implementation Protocol

- **Branch Confirmation**: Always ask the user whether to create a new branch or use the current one before starting any significant implementation.
- **Plan Confirmation**: Before writing or modifying substantial code, ensure that an implementation plan (`implementation_plan.md`) has been created, reviewed, and explicitly approved by the user.

## 3. Standard Implementation Workflow

- **Implementation Scope (API Unit)**: As a general rule, limit the scope of a single implementation step to a maximum of **1 API unit** (with exceptions when necessary).
- **Design First**: Before writing code, you MUST write or update the design document (e.g., `detailed_design.md`) for the target feature or process.
- **Task Breakdown**: After writing the design document, break down the implementation unit into fine-grained tasks and track them in `task.md`.
- **Test-Driven Development (TDD)**: Implement each finely broken-down unit using TDD methodology.
- **Test Coverage**: Always implement both **Unit Tests** and **Integration Tests**.
- **Regression Testing**: After completing an implementation unit, you MUST run regression tests to ensure existing functionality remains unaffected.