**Repository containing the infrastructure for project, fully defined using Docker Compose.**
Each service is described in a modular and declarative manner, enabling easy orchestration, scaling, and deployment during the Continuous Delivery (CD) process.

**The infrastructure includes:**
- *tg-bot* - input interface that implements the application's business logic
- *database* - PostgreSQL database for storing user data and request information
- *nginx* - load balancer for ml-core-service
- *ml-core-service_x* - multiple replicas of the core service running the ML model
- *redis* - caching layer for ml-core-service results
- *grafana* - visualization of application metrics and statistics
