# MCP MySQL Web Lab

Two separate Pods: browser -> client FastAPI -> MCP Streamable HTTP server -> MySQL. Client also calls shared Ollama.

1. Edit the Docker Hub IDs in k8s.yaml. Build and push both images.
2. In each namespace create mysql-student Secret with username, password, database keys, and apply k8s.yaml.
3. Create product_stock using sample.sql in that student's database. Existing A100/B200 values are overwritten by this sample.
4. kubectl port-forward -n stud12 svc/mcp-client 18080:8080; open http://localhost:18080.
5. Both client and server use namespace-local service mcp-server. MySQL and Ollama must exist in default namespace.
6. MCP server is not authenticated; use this configuration only within a trusted training environment.
