#!/usr/bin/env python3
import sys
from pathlib import Path

import yaml

# Translation dictionaries for table alignment
left_rule = {"<": ":", "^": ":", ">": "-"}
right_rule = {"<": "-", "^": ":", ">": ":"}


def table(file, records, headings, alignment=None):
    """
    Generate a Doxygen-flavor Markdown table from records.

    file -- Any object with a 'write' method that takes a single string
        parameter.
    records -- Iterable.  Rows will be generated from this.
    headings -- List of column headings.
    alignment - List of pairs alignment characters.  The first of the pair
        specifies the alignment of the header, (Doxygen won't respect this, but
        it might look good, the second specifies the alignment of the cells in
        the column.

        Possible alignment characters are:
            '<' = Left align (default for cells)
            '>' = Right align
            '^' = Center (default for column headings)
    """

    num_columns = len(headings)

    # Compute the table cell data
    columns = [[] for i in range(num_columns)]
    for record in records:
        for i, _ in enumerate(headings):
            columns[i].append(str(record[i]))

    # Fill out any missing alignment characters.
    extended_align = alignment if alignment is not None else []
    if len(extended_align) > num_columns:
        extended_align = extended_align[0:num_columns]
    elif len(extended_align) < num_columns:
        extended_align += [("^", "<") for i in range(num_columns - len(extended_align))]

    heading_align, cell_align = [x for x in zip(*extended_align)]

    field_widths = [
        len(max(column, key=len)) if len(column) > 0 else 0 for column in columns
    ]
    heading_widths = [max(len(head), 2) for head in headings]
    column_widths = [max(x) for x in zip(field_widths, heading_widths)]

    _ = " | ".join(
        ["{:" + a + str(w) + "}" for a, w in zip(heading_align, column_widths)]
    )
    heading_template = "| " + _ + " |"
    _ = " | ".join(["{:" + a + str(w) + "}" for a, w in zip(cell_align, column_widths)])
    row_template = "| " + _ + " |"

    _ = " | ".join(
        [
            left_rule[a] + "-" * (w - 2) + right_rule[a]
            for a, w in zip(cell_align, column_widths)
        ]
    )
    ruling = "| " + _ + " |"

    file.write(heading_template.format(*headings).rstrip() + "\n")
    file.write(ruling.rstrip() + "\n")
    for row in zip(*columns):
        file.write(row_template.format(*row).rstrip() + "\n")


def main():
    headings = ["Name", "Description", "Target", "Fields"]
    data = []
    with open(
        Path(__file__).parents[1] / "custom_components/mypyllant/services.yaml", "r"
    ) as stream:
        try:
            services = yaml.safe_load(stream)
            for name, service in services.items():
                service_fields = (
                    [f for _, f in service["fields"].items()]
                    if "fields" in service
                    else []
                )
                target = (
                    service["target"]["entity"]["domain"] if "target" in service else ""
                )
                data += [
                    (
                        f"[{service['name']}](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.{name})",
                        service["description"],
                        target,
                        ", ".join([f["name"] for f in service_fields]),
                    )
                ]
            table(sys.stdout, data, headings)
        except yaml.YAMLError as e:
            sys.stderr.write(str(e))
            sys.exit(1)


if __name__ == "__main__":
    main()
