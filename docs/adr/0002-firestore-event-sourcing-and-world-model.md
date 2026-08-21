# ADR 0002: Firestore Document Hierarchy & World Model Persistence

## Status
**Accepted**

## Context
Agent-X needs a state persistence engine that can handle:
1. Strongly consistent mission and task state tracking.
2. Real-time document updates pushed directly to the frontend web application.
3. Complex semantic graphs representing entities and relationships in the World Model.
4. Scale to hundreds of concurrent subagents without managing complex database servers.

We evaluated PostgreSQL (Cloud SQL), Spanner, DynamoDB/MongoDB, and Google Cloud Firestore (Native Mode).

## Decision
We select **Google Cloud Firestore in Native Mode** as the primary state engine, complemented by **Google Cloud Storage (GCS)** for large binary/text blobs and immutable evidence artifacts.

## Rationale
- **Native Real-Time Snapshots**: Firestore provides built-in client snapshot listeners (`onSnapshot`), allowing the Next.js frontend to instantly react to task state transitions and DAG mutations without polling.
- **Hierarchical Subcollections**: Subcollections (`/missions/{missionId}/tasks/{taskId}`, `/missions/{missionId}/entities/{entityId}`) provide natural multi-tenant isolation, clean partitioning, and atomic transactions within missions.
- **Serverless & Zero Maintenance**: Automatically scales from 0 to massive concurrent read/write loads without capacity provisioning.
- **Cost Efficiency**: No hourly instance overhead during idle periods, fitting both Hackathon budgets and enterprise production deployments.

## Consequences
- **Positive**: Sub-second UI state synchronization, zero database infrastructure maintenance, hierarchical data modeling, atomic batch commits for DAG replanning.
- **Negative**: Graph queries (e.g. multi-hop entity traversal) must be handled in application memory or modeled via edge subcollections rather than native graph query languages (GQL/Cypher). Large payloads ($> 1\text{ MB}$) must be stored in GCS and referenced by URI.
