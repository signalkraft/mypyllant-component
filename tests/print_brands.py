#!/usr/bin/env python3
from myPyllant.const import BRANDS, COUNTRIES


def main():
    for brand_key, brand_name in BRANDS.items():
        print(f"- {brand_name}")
        if brand_key in COUNTRIES.keys():
            for country in COUNTRIES[brand_key].values():
                print(f"    - {country}")
        else:
            print(
                "    - Does not support country selection, just leave the option empty"
            )


if __name__ == "__main__":
    main()
