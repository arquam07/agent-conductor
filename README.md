# agent-conductor

Kubernetes-native platform for running long-running **agentic jobs**. Submit a job over an API, a pool of workers pulls it off a queue and runs a multi-step agent, and results are persisted and streamed back. Workers autoscale on queue depth.

Built as a study in doing stateful, bursty AI workloads the way infrastructure actually wants them done.


## Why

The workload (agentic jobs) exists to exercise the infrastructure: submission and execution are decoupled through a queue, so the API and the workers scale independently. That decoupling is what makes the Kubernetes side worth doing.

## Stack

Python · FastAPI · LangGraph · Redis (queue) · Postgres (results) · Docker · Kubernetes · KEDA (queue-based autoscaling)

## Architecture

```mermaid
flowchart LR
    Client([Client]) -->|POST /jobs| API[API]
    API -->|enqueue| Q[(Redis<br/>queue)]
    API -->|write record| DB[(Postgres<br/>results)]
    Q -->|pull| W[Agent Workers]
    W -->|multi-step agent<br/>+ tool calls| W
    W -->|write result| DB
    Client -->|GET /jobs/id| API
    API -->|read| DB
    Cron[Cleanup CronJob] -->|purge old jobs| DB

    subgraph Kubernetes
        API
        Q
        W
        DB
        Cron
    end
```

| Component | Kubernetes object | Why |
|---|---|---|
| API | Deployment + Service + HPA | Stateless, scalable, load-balanced |
| Agent workers | Deployment, scaled on queue depth (KEDA) | Count tracks pending work |
| Redis (queue) | StatefulSet + PVC | Stateful, needs persistence |
| Postgres (results) | StatefulSet + PVC | Data survives pod restarts |
| Cleanup | CronJob | Scheduled background work |
| Config / secrets | ConfigMap + Secret | No secrets baked into images |
| Entry point | Ingress | Single way into the cluster |

## Job lifecycle

```mermaid
flowchart TD
    A["POST /jobs<br/>in: task + params — out: job_id"] --> B["validate + create record<br/>out: status=queued"]
    B --> C["enqueue job_id<br/>out: pushed to Redis"]
    C --> D["respond 202"]
    C -.queued.-> E["worker: pull job_id"]
    E --> F["mark running"]
    F --> G["execute agent<br/>(see below)"]
    G --> H["persist outcome<br/>out: status=done/failed"]
    D -.poll.-> I["GET /jobs/id<br/>out: status + result"]
    H -.reads.-> I
```

## Agent execution

```mermaid
flowchart TD
    A["receive task<br/>out: initial state"] --> B["reason step<br/>out: next action"]
    B --> C{"tool call needed?"}
    C -->|yes| D["execute tool"]
    D --> E["append result to state"]
    E --> B
    C -->|no| F["synthesize answer"]
    F --> G["return result"]
    B -.max steps guard.-> H["halt: step limit hit"]
    H --> G
```

## Project layout

```
app/
  api/      FastAPI — submit + status endpoints
  worker/   queue consumer + agent runner
  agent/    LangGraph agent graph + tools
  shared/   models, db, queue client, logging, config
k8s/        manifests (base + local/cloud overlays)
docker/     Dockerfiles
```