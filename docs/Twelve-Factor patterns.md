## Note: Twelve-Factor App Principles

ChatGPT, 2025-04-26

A set of best practices for designing cloud-native, scalable, and maintainable applications. Use this checklist to guide your CIRED chatbot—or any modern microservice—from prototype to production.

### 1. Codebase
- **One repository, many deploys.**  
  Track a single codebase in Git; deploy it to multiple environments (dev, staging, prod) with the same commit hash.  
- **Benefit:** Clear traceability between code changes and running services.

### 2. Dependencies
- **Explicit declaration & isolation.**  
  List all libraries in `pyproject.toml` (or `requirements.txt`). Use virtual environments or containers to avoid relying on global/system packages.  
- **Benefit:** Reproducible builds—“works on my machine” becomes a thing of the past.

### 3. Config
- **Store config in the environment.**  
  Keep all credentials, feature flags, and endpoint URLs outside the code. Use environment variables, mounted `.env` files, or a secrets manager.  
- **Benefit:** Same code works across environments; config is injected at release time.

### 4. Backing Services
- **Treat external services as attached resources.**  
  Databases, caches, message queues—bind them via configuration, not hard-coded URIs.  
- **Benefit:** Swap between services (e.g., Redis → Memcached) without touching application logic.

### 5. Build, Release, Run
- **Three distinct stages:**
  1. **Build:** Compile assets and code into an immutable bundle (e.g., Docker image).  
  2. **Release:** Combine the build with environment-specific config.  
  3. **Run:** Launch the application’s processes.
- **Benefit:** Rollbacks become trivial—simply redeploy a previous release.

### 6. Processes
- **Stateless, share-nothing processes.**  
  Any persistent state (user sessions, file uploads) lives in a backing service, not in-memory.  
- **Benefit:** Processes can be killed and replaced at will with zero downtime.

### 7. Port Binding
- **Self-contained web services.**  
  Your FastAPI app listens on a TCP port; there’s no external webserver dependency.  
- **Benefit:** Simplifies deployment pipelines—just run the container and route traffic to its port.

### 8. Concurrency
- **Scale via process model.**  
  Define multiple process types (e.g., web, worker, scheduler). Scale each independently based on load.  
- **Benefit:** Fine-grained elasticity—add more query workers or UI processes as needed.

### 9. Disposability
- **Fast startup & graceful shutdown.**  
  Aim for <10s boot times; handle SIGTERM gracefully to finish in-flight requests.  
- **Benefit:** Supports rapid scaling, rolling deploys, and resilient recoveries.

### 10. Dev/Prod Parity
- **Keep environments similar.**  
  Use the same language runtime, libraries, and backing-service setup across dev, staging, and prod.  
- **Benefit:** Minimizes environment-specific bugs and surprises at release time.

### 11. Logs
- **Treat logs as event streams.**  
  Write all logs to stdout/stderr. Let external systems (ELK, Prometheus, Grafana) collect, index, and visualize them.  
- **Benefit:** Decouples log generation from storage and analysis, simplifying operations.

### 12. Admin Processes
- **Run one-off tasks in the same environment.**  
  Database migrations, console shells, and reports run as ephemeral processes against the same codebase and config.  
- **Benefit:** Ensures consistency between regular and ad-hoc operations.

---

### Applying to CIRED Chatbot
- **Config (III):** Load API keys and tokens from `credentials/` or env-vars via Pydantic’s `BaseSettings`.  
- **Backing Services & Port Binding (IV, VII):** FastAPI binds to a port; vector DBs and analytics stores are attached resources.  
- **Build/Release/Run & Processes (V–IX):** Use Docker images and Prefect flows to orchestrate ingestion, indexing, benchmarking, and reporting as separate, stateless processes.  
- **Logs & Admin (XI, XII):** Stream metrics and logs to Prometheus; run GDPR purge and data migrations as one-off Prefect tasks.

