import textwrap


WIDTH = 44


def top():
    return "╔" + ("═" * WIDTH) + "╗"


def middle():
    return "╠" + ("═" * WIDTH) + "╣"


def bottom():
    return "╚" + ("═" * WIDTH) + "╝"



def row(label, value):

    prefix = f" {label:<10}: "

    available = WIDTH - len(prefix)

    value = str(value)


    wrapped = textwrap.wrap(
        value,
        width=available
    )


    lines = []


    if not wrapped:

        wrapped = [""]


    for index, part in enumerate(wrapped):

        if index == 0:

            text = prefix + part

        else:

            text = (" " * len(prefix)) + part


        lines.append(
            "║" + text.ljust(WIDTH)[:WIDTH] + "║"
        )


    return "\n".join(lines)



def format_model(model):

    lines = []

    lines.append(top())

    lines.append(
        row(
            "MODEL",
            model.get("name", "")
        )
    )

    lines.append(middle())

    lines.append(
        row(
            "Provider",
            model.get("provider", "Unknown")
        )
    )

    lines.append(
        row(
            "Type",
            model.get("type", "")
        )
    )

    lines.append(
        row(
            "Source",
            model.get("source", "")
        )
    )

    lines.append(
        row(
            "Size",
            model.get("size", "Unknown")
        )
    )

    lines.append(
        row(
            "Hash",
            model.get("hash", "Unknown")
        )
    )

    lines.append(middle())

    lines.append(
        row(
            "Status",
            "INSTALLED"
            if model.get("installed")
            else "AVAILABLE"
        )
    )

    lines.append(
        row(
            "Favorite",
            "YES"
            if model.get("favorite")
            else "NO"
        )
    )

    lines.append(bottom())


    return "\n".join(lines)



def show_model(model):

    output = format_model(model)

    print(output)

    return output
