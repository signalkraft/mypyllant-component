# Contributing

## Contributing to the Home Assistant Component

!!! warning

    You need at least Python 3.10.

Fork and clone this repo, then from the root directory run:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.test.txt
pre-commit install
# Make your changes
pytest
git commit ...
```

If you also need to modify the underlying [myPyllant library](https://github.com/signalkraft/mypyllant),
clone & install it in editable mode in `mypyllant-component`:

```shell
# From the root of this repository
git clone https://github.com/signalkraft/myPyllant.git ../myPyllant
pip install -e ../myPyllant
```

Now you can modify `myPyllant/src` and directly develop against these changes in `mypyllant-component`.

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

## Contributing to the underlying myPyllant library


!!! warning

    You need at least Python 3.10

I'm happy to accept PRs, if you run the pre-commit checks and test your changes:

```shell
git clone https://github.com/signalkraft/myPyllant.git
cd myPyllant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
pytest
```

### Supporting new Countries

The myVAILLANT app uses Keycloak and OIDC for authentication, with a realm for each country and brand.
There is a script to check which countries are supported:

```shell
python3 -m myPyllant.tests.find_countries
```

Copy the resulting dictionary into [https://github.com/signalkraft/myPyllant/blob/main/src/myPyllant/const.py](src/myPyllant/const.py)

### Contributing Test Data

Because the myVAILLANT API isn't documented, you can help the development of this library by contributing test data:

```shell
python3 -m myPyllant.tests.generate_test_data -h
python3 -m myPyllant.tests.generate_test_data username password brand --country country
```

..or use Docker:

```shell
docker run -v $(pwd)/test_data:/build/src/myPyllant/tests/json -ti ghcr.io/signalkraft/mypyllant:latest python3 -m myPyllant.tests.generate_test_data username password brand --country country
```

With docker, the results will be put into `test_data/`.

You can then either create a PR with the created folder, or zip it and [attach it to an issue](https://github.com/signalkraft/myPyllant/issues/new).

### Adding new API endpoints

If your myVAILLANT app has more features than this integration, chances are you have a more complex system then me.
You can reverse engineer the API endpoints and open an issue with the requests + responses.
See [Reverse Engineering](3-reverse-engineering.md) for a tutorial.