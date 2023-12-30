---
description: Contribution guide with setup & test instructions
hide:
  - navigation
---

# Contributing

## Cloning & Installing

!!! warning

    You need at least Python 3.10.

Fork and clone the [mypyllant-component repository](https://github.com/signalkraft/mypyllant-component), then from within the directory run:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r dev-requirements.txt
pre-commit install
# Make your changes
git commit -m ...  # Code formatting, analysis, and tests are run automatically before the commit
```

If you also need to modify the underlying [myPyllant library](https://github.com/signalkraft/mypyllant),
clone & install it in editable mode in `mypyllant-component`:

```shell
# From within the mypyllant-component directory
git clone https://github.com/signalkraft/myPyllant.git ../myPyllant
pip install -e ../myPyllant
```

Now you can modify `myPyllant/src` and directly develop against these changes in `mypyllant-component`.

### VSCode Dev Container

There's also a VSCode dev container available in `.devcontainer.json`, provided by [github.com/ml1nk](https://github.com/ml1nk).

### Debugging

When debugging or reporting issues, turn on debug logging by adding this to your `configuration.yaml` 
and restarting Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.mypyllant: debug
    myPyllant: debug
```

### Testing in Docker

To test your changes, you can spin up a quick Docker environment:

1. Follow the [cloning & installation](#cloning-installing) steps above
2. Copy `.env.sample` to `.env` and add your credentials in the new file
3. Run `docker compose up`

After HA started, open [http://localhost:8123](http://localhost:8123) in your browser and sign in with user `test` and password `test`.

The integration should be configured and show entities on the default dashboard.

![Default Dashboard Screenshot](assets/default-dashboard.png)

## Contributing to the underlying myPyllant library

!!! warning

    You need at least Python 3.10

Fork and clone the [myPyllant repository](https://github.com/signalkraft/myPyllant), then from within the directory run:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r dev-requirements.txt
pip install -e .
pre-commit install
# Make your changes
git commit -m ...  # Code formatting, analysis, and tests are run automatically before the commit
```

### Supporting new Countries

The myVAILLANT app uses Keycloak and OIDC for authentication, with a realm for each country and brand.
There is a script to check which countries are supported:

```shell
python3 -m myPyllant.tests.find_countries
```

Copy the resulting dictionary into [https://github.com/signalkraft/myPyllant/blob/main/src/myPyllant/const.py](src/myPyllant/const.py)

::: myPyllant.tests.find_countries.main
    options:
      show_source: true
      heading_level: 0

### Contributing Test Data

Because the myVAILLANT API isn't documented, you can help the development of this library by contributing test data:

=== "Home Assistant Service"
    
    [![Open your Home Assistant instance and show your service developer tools with a specific service selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_holiday)
    
    Select `mypyllant.generate_test_data` and call the service.

=== "Shell"
    
    ```shell
    python3 -m myPyllant.tests.generate_test_data -h
    python3 -m myPyllant.tests.generate_test_data username password brand --country country
    ```

=== "Docker"
    
    ```shell
    docker run -v $(pwd)/test_data:/build/src/myPyllant/tests/json -ti ghcr.io/signalkraft/mypyllant:latest python3 -m myPyllant.tests.generate_test_data username password brand --country country
    ```
    
    With docker, the results will be put into `test_data/`.

---

You can then either create a PR with the created folder, or zip it and [attach it to an issue](https://github.com/signalkraft/myPyllant/issues/new).

::: myPyllant.tests.generate_test_data.main
    options:
      show_source: true
      heading_level: 0

### Adding new API endpoints

If your myVAILLANT app has more features than this integration, chances are you have a more complex system then me.
You can reverse engineer the API endpoints and open an issue with the requests + responses.
See [Reverse Engineering](3-reverse-engineering.md) for a tutorial.

### Running commands on your Home Assistant installation in Docker

If you're using this component in a Home Assistant installation that uses docker compose, you can run these commands directly (from the folder that contains your `docker-compose.yml`):

```shell
docker compose exec homeassistant python3 -m myPyllant.tests.generate_test_data username password brand --country country
# Note the output folder
docker compose cp homeassistant:<testdata folder> .
# Test data will be copied to your current directory
```