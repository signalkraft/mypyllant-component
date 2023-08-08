# Contributing

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

### Contributing to the underlying mypyllant library

See https://github.com/signalkraft/mypyllant#contributing