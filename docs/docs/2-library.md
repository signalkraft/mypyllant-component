# CLI & Python Library

[![PyPI](https://img.shields.io/pypi/v/myPyllant)](https://pypi.org/project/myPyllant/)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/signalkraft/myPyllant/build-test.yaml)

The [myPyllant library](https://github.com/signalkraft/mypyllant) can interact with the API behind the myVAILLANT app 
(and branded versions of it, such as the MiGo app from Saunier Duval). Needs at least Python 3.10.

Not affiliated with Vaillant, the developers take no responsibility for anything that happens to your devices because of this library.

## Installation

!!! warning

    You need at least Python 3.10

```shell
pip install myPyllant
python3 -m myPyllant.export user password brand --country country
# See python3 -m myPyllant.export -h for more options and a list of countries
```

..or use Docker:

```shell
docker run -ti ghcr.io/signalkraft/mypyllant:latest python3 -m myPyllant.export user password brand --country country
```

The `--data` argument exports historical data of the devices in your system.
Without this keyword, information about your system will be exported as JSON.

## Usage

```python
#!/usr/bin/env python3

import argparse
import asyncio
import logging
from datetime import datetime, timedelta

from myPyllant.api import MyPyllantAPI
from myPyllant.const import ALL_COUNTRIES, BRANDS, DEFAULT_BRAND

parser = argparse.ArgumentParser(description="Export data from myVaillant API   .")
parser.add_argument("user", help="Username (email address) for the myVaillant app")
parser.add_argument("password", help="Password for the myVaillant app")
parser.add_argument(
    "brand",
    help="Brand your account is registered in, i.e. 'vaillant'",
    default=DEFAULT_BRAND,
    choices=BRANDS.keys(),
)
parser.add_argument(
    "--country",
    help="Country your account is registered in, i.e. 'germany'",
    choices=ALL_COUNTRIES.keys(),
    required=False,
)
parser.add_argument(
    "-v", "--verbose", help="increase output verbosity", action="store_true"
)


async def main(user, password, brand, country):
    async with MyPyllantAPI(user, password, brand, country) as api:
        async for system in api.get_systems():
            print(await api.get_time_zone(system))
            print(await api.set_holiday(system))
            print(
                await api.set_holiday(
                    system, datetime.now(), datetime.now() + timedelta(days=7)
                )
            )
            print(await api.get_time_zone(system))
            print(await api.cancel_holiday(system))
            print(await api.set_set_back_temperature(system.zones[0], 15.5))
            print(await api.quick_veto_zone_temperature(system.zones[0], 21, 5))
            print(await api.cancel_quick_veto_zone_temperature(system.zones[0]))
            if system.domestic_hot_water:
                print(await api.boost_domestic_hot_water(system.domestic_hot_water[0]))
                print(await api.cancel_hot_water_boost(system.domestic_hot_water[0]))
                print(
                    await api.set_domestic_hot_water_temperature(
                        system.domestic_hot_water[0], 46
                    )
                )


if __name__ == "__main__":
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(args.user, args.password, args.brand, args.country))

```


## Contributing & Tests

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