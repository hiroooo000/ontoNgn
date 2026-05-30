---
trigger: always_on
description: Design and planning rules for the ontoNgn project, covering architecture, communication, and coding standards.
---

# Design and Planning Rules

## 0. Mandatory Communication Rules (Absolute)

- **Output Language**: All user-facing content (responses, explanations, reports) MUST be delivered in Japanese.
- **Planning Language**: Implementation plans (`implementation_plan.md`), task lists (`task.md`), and walkthroughs (`walkthrough.md`) MUST be written in Japanese.
- **Explicit Confirmation**: Before making significant changes or executing modifying commands, you MUST explicitly ask for user confirmation.

## 1. Architecture Principles (Clean Architecture)

- **Dependency Rule**: Dependencies must only point inwards. Outer layers (Interfaces/Adapters, Infrastructure) can depend on inner layers (Use Cases, Domain), but never vice-versa.
- **Layer Responsibilities**:
  - **Domain**: Pure business logic, Pydantic models (e.g., `GraphNode`, `GraphEdge`), and interface definitions (Abstract Base Classes like `IGraphRepository`). No external dependencies.
  - **Use Cases**: Application logic and service orchestration (e.g., orchestrating rendering, vision extraction, and ontology generation).
  - **Interfaces (Adapters)**: FastAPI Routers, Gateways (e.g., `LMStudioGateway`), and concrete Repository adapters (e.g., `KuzuGraphRepository`).
  - **Infrastructure**: Concrete implementations of external systems, Database sessions, and configuration.
- **Dependency Inversion**: Always depend on interfaces/abstractions rather than concrete implementations for cross-layer communication (e.g., use `IGraphRepository` instead of `Neo4jGraphRepository` directly in Use Cases).
- **Architecture Compliance**: Design must strictly follow `docs/system_design.md` and `docs/specification.md` as the primary principles.
- **Architectural Breach Protocol**: If a requested feature necessitates breaking the established architecture, you MUST explicitly ask the user: "This change violates the architecture. Do you wish to proceed?" and obtain confirmation before implementation.

## 2. Component Design

- **Single Responsibility Principle (SRP)**: Each class or module should have one, and only one, reason to change.
- **Type Safety**: Strictly use Pydantic for data validation and type checking, ensuring safe parsing of LLM outputs and API requests.

## 3. Documentation Rules

- **Design Document Verification**: 設計を検討する際には、必ず `docs/` 直下に格納されている設計ドキュメントを確認すること。
- **Detailed Design Storage**: 詳細設計に関するドキュメント（関連するものすべて）は、必ず `docs/detail_design/` 以下に格納すること。
