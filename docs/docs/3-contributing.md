---
description: Contribution guide with setup & test instructions
hide:
  - navigation
---

# Contributing

## Debugging

When debugging or reporting issues, turn on debug logging by adding this to your `configuration.yaml`
and restarting Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.mypyllant: debug
    myPyllant: debug
```

Then you can check for errors in [System :material-arrow-right: Logs](https://my.home-assistant.io/redirect/logs/)
and attach the logs when [creating an issue](https://github.com/signalkraft/mypyllant-component/issues/new?assignees=&labels=&projects=&template=bug_report.md&title=).

If you would like to see a value added to the integration, check if it's available when you [generate test data](#contributing-test-data).


### Contributing Test Data

Because the myVAILLANT API isn't documented, you can help the development of this library by contributing test data:

=== "Home Assistant Service"

    Go to Developer Tools :material-arrow-right: Services and select `mypyllant.generate_test_data`.
    Then call the service and copy the resulting output.

    [![Open your Home Assistant instance and show your service developer tools with a specific service selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.generate_test_data)

=== "Shell"

    ```shell
    uv run -m myPyllant.tests.generate_test_data -h
    uv run -m myPyllant.tests.generate_test_data username password brand --country country
    ```

=== "Docker"

    ```shell
    docker run -v $(pwd)/test_data:/build/src/myPyllant/tests/json -ti ghcr.io/signalkraft/mypyllant:latest python3 -m myPyllant.tests.generate_test_data username password brand --country country
    ```
    
    With docker, the results will be put into `test_data/`.

You can then either create a PR with the created folder, or zip it
and [attach it to an issue](https://github.com/signalkraft/myPyllant/issues/new/choose).

## Contributing to the HA Component

!!! warning

    You need at least Python 3.13 and [uv installed](https://docs.astral.sh/uv/getting-started/installation/)

Fork and clone the [mypyllant-component repository](https://github.com/signalkraft/mypyllant-component), then from
within the directory run:

```shell
uv sync
uv run pre-commit install
# Make your changes
git commit -m ...  # Code formatting, analysis, and tests are run automatically before the commit
```

If you also need to modify the underlying [myPyllant library](https://github.com/signalkraft/mypyllant),
clone & install it in editable mode in `mypyllant-component`:

```shell
# From within the mypyllant-component directory
git clone https://github.com/signalkraft/myPyllant.git ../myPyllant
uv pip install -e ../myPyllant
```

Now you can modify `myPyllant/src` and directly develop against these changes in `mypyllant-component`.

### VSCode Dev Container

There's also a VSCode dev container available in `.devcontainer.json`, provided
by [github.com/ml1nk](https://github.com/ml1nk).

### Testing in Docker

To test your changes, you can spin up a quick Docker environment:

1. Follow the [installation](#contributing-to-the-ha-component) steps above
2. Copy `.env.sample` to `.env` and add your credentials in the new file
3. Run `docker compose up`

After HA started, open [http://localhost:8123](http://localhost:8123) in your browser and sign in with user `test` and
password `test`.

The integration should be configured and show entities on the default dashboard.

![Default Dashboard Screenshot](assets/default-dashboard.png)

## Contributing to the underlying myPyllant library

!!! warning

    You need at least Python 3.13 and [uv installed](https://docs.astral.sh/uv/getting-started/installation/)

Fork and clone the [myPyllant repository](https://github.com/signalkraft/myPyllant), then from within the directory run:

```shell
uv sync
uv run pre-commit install
# Make your changes
git commit -m ...  # Code formatting, analysis, and tests are run automatically before the commit
```

### Supporting new Countries

The myVAILLANT app uses Keycloak and OIDC for authentication, with a realm for each country and brand.
There is a script to check which countries are supported:

```shell
uv run -m myPyllant.tests.find_countries
```

Copy the resulting dictionary
into [src/myPyllant/const.py](https://github.com/signalkraft/myPyllant/blob/main/src/myPyllant/const.py)

::: myPyllant.tests.find_countries.main
    options:
        show_source: true
        heading_level: 0

### Adding new API endpoints

If your myVAILLANT app has more features than this integration, chances are you have a more complex system then me.
You can reverse engineer the API endpoints and open an issue with the requests + responses.
See [Reverse Engineering](3-reverse-engineering.md) for a tutorial.

### Running commands on your Home Assistant installation in Docker

If you're using this component in a Home Assistant installation that uses docker compose, you can run these commands
directly (from the folder that contains your `docker-compose.yml`):

```shell
docker compose exec homeassistant python3 -m myPyllant.tests.generate_test_data username password brand --country country
# Note the output folder
docker compose cp homeassistant:<testdata folder> .
# Test data will be copied to your current directory
```

## Acknowledgements

* Auth is loosely based on [ioBroker.vaillant](https://github.com/TA2k/ioBroker.vaillant)
* Most API endpoints are reverse-engineered from the myVaillant app, using [mitmproxy](https://github.com/mitmproxy/mitmproxy)
* Logo based on [Hase Icons erstellt von Freepik - Flaticon](https://www.flaticon.com/de/kostenlose-icons/hase) & [Ouroboros Icons erstellt von Freepik - Flaticon](https://www.flaticon.com/de/kostenlose-icons/ouroboros).
