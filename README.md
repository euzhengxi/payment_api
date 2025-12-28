# Payment API Project

## Overview

This project is a **backend-focused side project** that implements a simplified model of a modern **payment API system**. It is designed to explore **service decomposition, API design, and event-driven architecture** in a realistic but minimal setting.

The system is composed of multiple microservices that communicate via HTTP using **RESTful API design principles**. While the **critical payment path is handled synchronously** to preserve correctness and consistency, **event-driven mechanisms** are used to handle side effects such as notifications and logging.

---

## Architecture

The project consists of the following components:

- **Main Service**  
  Orchestrates payment workflows and enforces business logic.

- **Database Service**  
  Manages persistent storage for accounts, balances, and transactions.

- **Issuer Service**  
  Simulates issuer-side validation and authorization.

- **Client Service (CLI)**  
  Provides a simple command-line interface for interacting with the system.

Each component runs as an independent **microservice**, communicating over HTTP.

---

## Design Principles

- RESTful API design
- Microservice-based architecture
- Synchronous critical path for payment processing
- Event-driven architecture for non-critical side effects
- Clear separation of concerns
- Testable endpoints with unit tests

---

## Versions

### v1 — 25 Dec 2025

- Fully functional payment API system
- Event-driven handling of side effects
- Simple CLI client for interacting with services
- Unit tests covering API endpoints
- Logging

### v2 — 28 Dec 2025

- Added versioning to endpoints

---

## Future Improvements

- Authentication and authorization
- ACID-compliant transaction handling
- Failover and resiliency mechanisms
- Improved concurrency control
- Observability (metrics, tracing)
