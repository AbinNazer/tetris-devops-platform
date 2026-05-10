# 🎮 Tetris DevOps Platform

![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-326CE5?style=for-the-badge&logo=kubernetes)
![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-orange?style=for-the-badge)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C?style=for-the-badge&logo=prometheus)
![Grafana](https://img.shields.io/badge/Grafana-Dashboard-F46800?style=for-the-badge&logo=grafana)

#  Three-Tier Cloud-Native DevOps Project

A complete cloud-native DevOps portfolio project built around a Tetris application using Docker, CI/CD, Kubernetes, GitOps, DevSecOps, Monitoring, and Observability practices.

---

# 📸 Project Architecture

```mermaid
flowchart TD

    U[User Browser]

    U --> F[Tetris Frontend Container]

    F --> B[Backend API Service]

    B --> D[(PostgreSQL Database)]

    G[GitHub Repository] --> C[CI/CD Pipeline]

    C --> T[Trivy Security Scan]

    T --> DH[Docker Hub]

    DH --> K[Kubernetes Cluster]

    K --> A[ArgoCD GitOps Sync]

    K --> P[Prometheus]

    P --> GR[Grafana Dashboard]
```

---

# 🧰 Tech Stack

| Category | Tools |
|---|---|
| Frontend | Tetris Docker Image |
| Backend | Flask / Node.js |
| Database | PostgreSQL |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions / Jenkins |
| Security | Trivy, kube-score |
| Orchestration | Kubernetes |
| GitOps | ArgoCD |
| Monitoring | Prometheus, Grafana |

---

# 📁 Project Structure

```text
tetris-devops-platform/
│
├── backend/
├── k8s/
├── .github/
├── docker-compose.yml
└── README.md
```

---

# 🐳 Docker Workflow

## Pull Frontend Image

```bash
docker pull bsord/tetris
```

## Run Frontend

```bash
docker run -d -p 8080:80 bsord/tetris
```

---

# ⚙️ Docker Compose

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

---

# 🔄 CI/CD Pipeline

Pipeline Stages:

- Checkout source code
- Install dependencies
- Run tests
- Build Docker images
- Security scanning with Trivy
- Push images to Docker Hub
- Update Kubernetes manifests

---

# 🔐 DevSecOps

## Trivy Scan

```bash
trivy image YOUR_DOCKERHUB_USERNAME/tetris-backend:latest
```

---

# ☸️ Kubernetes Deployment

```bash
kubectl apply -f k8s/base/
```

## Check Pods

```bash
kubectl get pods -n tetris
```

## Check Services

```bash
kubectl get svc -n tetris
```

---

# 🔁 GitOps with ArgoCD

```bash
kubectl apply -f k8s/argocd/
```

---

# 📊 Monitoring

Monitoring stack includes:

- Prometheus
- Grafana
- Node Exporter
- kube-state-metrics

---

# 📈 Grafana Access

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open:

```text
http://localhost:3000
```

---

# 🧠 Key DevOps Concepts

- Docker containerization
- CI/CD automation
- Kubernetes orchestration
- GitOps workflow
- DevSecOps scanning
- Monitoring and observability

---

# 👤 Author

## Abin Nazer

DevOps | Cloud | Kubernetes Enthusiast
