# dnsquery

This is a simple web-based troubleshooting tool for querying DNS environments to view the IP address that a domain name ultimately resolves to. The code behind this was mainly written to troubleshoot where cached records needed to be purged after IP changes.

At this point, it's intentionally been designed to not show a high level of detail such as the type of record, etc.

Additional options that can be dispalyed for each query:
- Record TTL
- Query Reponse Time

By default, queries will be sent to Cloudflare Google and if no name servers are specified. You can find instructions for setting up your own name servers [here](#defining-your-own-name-servers-to-query).

## Defining your own Name Servers to Query

You can specify your own set of servers to query by adding a file named `servers.yml` and mapping it to `/app/servers.yml` within the container. The contents must be in this format:

```yaml
dnsquery:
  Name Server 1 - Cloudflare:
    ip: 1.1.1.1
  Name Server 2 - Google:
    ip: 8.8.8.8
```

## Deployment Options

### Docker Compose (Recommended)

Example docker-compose.yml file
```yaml
services:
  dnsquery:
    container_name: dnsquery
    # Using 'latest' as an example. specifying a specific version is preferred
    image: ghcr.io/clayoster/dnsquery:latest
    restart: always
    # This is required if you want to specify your own name servers to query
    volumes:
      - ./servers.yml:/app/servers.yml:ro
    ports:
      - "8080:8080"
```

### Kubernetes

Example Kubernetes manifest file defining the following items:
- Namespace
- ConfigMap (Containing servers.yml file containing example configuration)
- Deployment (A single pod with health checks)
- Service
- Ingress (Configured with example domain "dnsquery.example.com" with HTTPS optionally)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dnsquery
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: dnsquery
  namespace: dnsquery
data:
  servers.yml: |
    # Example Configuration
    #
    # dnsquery:
    #   Example - CloudFlare - 1.1.1.1:
    #     ip: '1.1.1.1'
    #   Example - Google DNS - 8.8.8.8:
    #     ip: '8.8.8.8'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dnsquery
  namespace: dnsquery
  labels:
    app: dnsquery
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dnsquery
  template:
    metadata:
      labels:
        app: dnsquery
    spec:
      containers:
      - name: dnsquery
        image: ghcr.io/clayoster/dnsquery:latest
        ports:
          - containerPort: 8080
            name: 8080tcp
            protocol: TCP
        livenessProbe:
          exec:
            command:
              - pgrep
              - gunicorn
          failureThreshold: 3
          initialDelaySeconds: 5
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 1
        resources: {}
        startupProbe:
          failureThreshold: 3
          httpGet:
            path: /
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 5
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 1
        volumeMounts:
          - mountPath: /app/servers.yml
            name: dnsquery
            readOnly: true
            subPath: servers.yml
      volumes:
      - name: dnsquery
        configMap:
          name: dnsquery
---
apiVersion: v1
kind: Service
metadata:
  name: dnsquery
  namespace: dnsquery
spec:
  selector:
    app: dnsquery
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dnsquery
  namespace: dnsquery
spec:
  rules:
  - host: dnsquery.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dnsquery
            port:
              number: 80
  # Optional TLS block
  #tls:
  #  - hosts:
  #    - dnsquery.example.com
  #    secretName: tls-cert-name
```

## To-Dos:
- Improve the UI (especially for mobile)
- Add option to find Active Directory DNS servers based on AD SRV records and query them
- Add test for DNS timeout handling (test the perform_query function directly)
