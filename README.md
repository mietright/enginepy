# enginepy

[![CI](https://github.com/mietright/enginepy/actions/workflows/ci.yml/badge.svg)](https://github.com/mietright/enginepy/actions/workflows/ci.yml)


`enginepy` is a Python client library for interacting with the Mietright Engine API. It provides asynchronous methods for common operations like updating documents, triggering actions, and managing requests.

## Features

*   Asynchronous client based on `aiohttp`.
*   Typed models using Pydantic for API requests and responses.
*   Configuration management via YAML files and environment variables.
*   Built-in logging and optional Logfire integration.
*   Cached client instance for efficiency.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your-github-username>/<your-repo-name>.git
    cd <your-repo-name>
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

## Configuration

Configuration is managed by `ant31box.config` and can be provided through a `config.yaml` file or environment variables.

1.  **Create a `config.yaml` file:** (or use environment variables)
    Copy the example or create your own:
    ```yaml
    # config.yaml
    logfire:
      token: "your-logfire-token" # Optional: for Logfire integration
      service_name: "enginepy-client"
      # ... other logfire settings

    engine:
      endpoint: "https://your-engine-api.example.com"
      token: "your-engine-api-token"

    sentry:
      dsn: "your-sentry-dsn" # Optional: for Sentry integration
      # ... other sentry settings

    logging:
      # ... logging configuration (see enginepy/config.py for defaults)
    ```

2.  **Environment Variables:**
    Settings can be overridden using environment variables prefixed with `ENGINEPY_`. Nested settings use double underscores (`__`).
    *   `ENGINEPY_ENGINE__ENDPOINT="https://env-engine-api.example.com"`
    *   `ENGINEPY_ENGINE__TOKEN="env-api-token"`
    *   `ENGINEPY_LOGFIRE__TOKEN="env-logfire-token"`

The application loads configuration in the following order of precedence:
1.  Environment Variables
2.  `config.yaml` file (if path is provided or found in default locations)
3.  Default values defined in `enginepy/config.py`.

## Usage

Initialize the configuration and get the client instance.

```python
import asyncio
from enginepy.config import config
from enginepy.clients import engine_client
from enginepy.models import EngineRequest, EngineTrigger, DocsResponse # Import necessary models

async def main():
    # Load configuration (looks for config.yaml by default)
    cfg = config()

    # Get the cached engine client instance
    client = engine_client()

    # Example: Check health
    try:
        health_status = await client.health()
        print(f"Engine health: {health_status}")
    except Exception as e:
        print(f"Error checking health: {e}")

    # Example: Create a request (replace with actual data)
    try:
        # NOTE: EngineRequest requires 'product', 'funnel', and 'fields'
        # Adjust the example data below to be valid for your use case
        new_request_data = EngineRequest(
            product="your_product_name",
            funnel="your_funnel_name",
            fields=[
                # Populate with EngineField objects, e.g.:
                # {"field": "customer_name", "answer": "John Doe", "type": "string"},
                # {"field": "consent_given", "answer": True, "type": "checkbox"},
            ]
            # documents="[]", # Optional: Add document info if needed
            # documents_presign=False # Optional
        )
        created_request = await client.create_request(new_request_data)
        print(f"Created request response: {created_request}")
        # Assuming the response is a dict with an 'id' or 'request_id' key
        request_id = created_request.get("request_id") # Adjust based on actual response structure

        if request_id:
            # Example: Trigger an action (replace with actual data)
            trigger_data = EngineTrigger(
                request_id=request_id,
                trigger_id="some-trigger-uuid", # Replace with a valid trigger ID
                name="example_trigger", # Optional: Add trigger name
                # client="enginepy", # Optional: Defaults in model
                # attempt=1 # Optional: Defaults in model
            )
            triggered_action = await client.action_trigger(trigger_data)
            print(f"Triggered action status: {triggered_action.status}")

            # Example: Update document OCR (replace with actual data)
            doc_id_to_update = 456 # Replace with a valid document ID
            ocr_pages_content = ["Page 1 text", "Page 2 text"]
            pdf_url = "https://example.com/path/to/searchable.pdf" # Optional
            update_success = await client.update_doc(doc_id_to_update, ocr_pages_content, pdf_url)
            print(f"Document update successful: {update_success}")

    except Exception as e:
        print(f"An API error occurred: {e}")

if __name__ == "__main__":
    # Note: Running this script requires a configured environment
    # (config.yaml or environment variables) and a running event loop.
    # You might need to adapt this runner based on your application structure.
    # For simple testing, ensure you have 'asyncio' and call asyncio.run(main())
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "cannot run event loop while another loop is running" in str(e):
            print("Note: asyncio.run(main()) cannot be called if an event loop is already running (e.g., in Jupyter).")
        else:
            raise

```

### Token Management

The `EngineClient` provides flexible token management with support for both instance-wide and specific token overrides:

#### Instance-Wide Token Override

Set a token that overrides all API calls for this client instance, regardless of specific token configurations:

```python
from enginepy.config import EngineConfigSchema, EngineTokensConfigSchema
from enginepy.engine_client import EngineClient

# Initialize with config
config = EngineConfigSchema(
    endpoint="https://engine.example.com",
    token="default-token",
    tokens=EngineTokensConfigSchema(admin="admin-specific-token")
)
client = EngineClient(config=config)

# Override all tokens for this client instance
client.set_token("new-instance-token")
# All subsequent API calls on this client instance will use "new-instance-token"
```

#### Specific Token Override

Update specific tokens (e.g., `admin`, `zieb`) without affecting the instance-wide override:

```python
# Update only the admin token
client.set_token("new-admin-token", key="admin")
# API calls requiring admin token will use "new-admin-token"
# Other calls use the default or global override token
```

#### Initialization with Token Override

Pass a token during initialization to set a global override from the start:

```python
# Legacy pattern (deprecated but still supported)
client = EngineClient(endpoint="https://engine.example.com", token="my-token")
# This sets an instance-wide override token for all API calls on this client instance
```

**Note:** Each `EngineClient` instance maintains its own token state. Token overrides only affect the specific instance they are set on, not other instances.

#### Token Resolution Priority

The client resolves tokens in the following order:
1. **Instance-wide override token** (set via `set_token()` without key or at initialization with `endpoint` and `token`)
2. **Specific tokens** from `config.tokens` (e.g., `admin`, `zieb`) if the API endpoint has token preferences
3. **Default token** from `config.token`

See `enginepy/engine_client.py` for all available client methods and `enginepy/models.py` for request/response models.

## Development

1.  **Set up the environment:**
    ```bash
    poetry install
    ```

2.  **Activate the virtual environment:**
    ```bash
    poetry shell
    ```

3.  **Run linters and formatters:**
    This project uses `ruff` for linting and formatting. Pre-commit hooks are configured to run these checks automatically.
    ```bash
    # Run checks manually
    poetry run ruff check .
    poetry run ruff format .

    # Install pre-commit hooks (optional, but recommended)
    poetry run pre-commit install
    ```

## Testing

Tests are written using `pytest` and `pytest-asyncio`.

1.  **Run all tests:**
    ```bash
    make test
    ```
    or
    ```bash
    poetry run pytest
    ```


## License

This project is closed source and copyrighted by CONNY GmbH. All rights reserved.
