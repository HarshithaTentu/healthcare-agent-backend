# Architecture Overview

```mermaid
flowchart LR
    User --> API
    API --> Decision
    Decision -->|Needs knowledge| Search
    Search --> KnowledgeBase
    KnowledgeBase --> Search
    Search --> Prompt
    Decision -->|Simple| Prompt
    Prompt --> LLM
    LLM --> API
    API --> User

