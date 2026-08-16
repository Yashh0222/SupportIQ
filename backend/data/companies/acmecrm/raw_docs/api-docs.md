# AcmeCRM API and Integrations

## The AcmeCRM API
The AcmeCRM REST API lets you programmatically manage contacts, deals, and notes. The base URL is `https://api.acmecrm.com/v1`. Authenticate with an API token created under Settings -> API Keys.

## Creating an API key
Go to Settings -> API Keys -> Create Key. Name the key and choose a scope (read-only or read/write). The key is shown only once — copy and store it securely.

## Rate limits
The API allows 100 requests per minute per API key. If you exceed the limit, you receive a 429 status code with a `Retry-After` header.

## Webhooks
AcmeCRM can send webhooks for events like `deal.created`, `deal.updated`, and `contact.created`. Configure the endpoint URL under Settings -> Webhooks. We retry failed deliveries up to 5 times with exponential backoff.

## Integration with HubSpot
The HubSpot integration syncs contacts and deals in both directions every 15 minutes. Enable it under Settings -> Integrations -> HubSpot.
