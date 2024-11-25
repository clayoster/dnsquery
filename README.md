# dnsquery

This is a simple troubleshooting tool for querying DNS environments to view the IP address that a domain name ultimately resolves to. The code behind this was mainly written to troubleshoot where cached records needed to be purged after IP changes.

At this point, it's intentionally been designed to not show a high level of detail such as the type of record, etc.

Additional options that can be dispalyed for each query:
- Record TTL
- Query Reponse Time

By default, queries will be sent to Cloudflare Google and if no name servers are specified. You can find instructions for setting up your own name servers [here](#defining-your-own-name-servers-to-query).

## Deployment with Docker Compose (Recommended)

#### Example docker-compose.yml file

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

## Defining your own Name Servers to Query

You can specify your own set of servers to query by adding a file named `servers.yml` and mapping it to `/app/servers.yml` within the container. The contents must be in this format:

```yaml
dnsquery:
  Name Server 1 - Cloudflare:
    ip: 1.1.1.1
  Name Server 2 - Google:
    ip: 8.8.8.8
```