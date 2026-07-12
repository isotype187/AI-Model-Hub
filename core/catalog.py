from core.discovery import (
    discover_ollama,
    discover_hf,
    discover_github
)

from core.db import (
    upsert_model,
    get_all
)


def normalize_model(model):

    return {
        "id": model.get("id"),
        "name": model.get("name", "unknown"),
        "source": model.get("source", "unknown"),
        "type": model.get("type", "unknown"),

        "provider": model.get(
            "provider",
            model.get("source", "unknown")
        ),

        "size": model.get(
            "size",
            "Unknown"
        ),

        "hash": model.get(
            "id",
            ""
        ),

        "installed": bool(
            model.get(
                "installed",
                False
            )
        ),

        "favorite": bool(
            model.get(
                "favorite",
                False
            )
        )
    }



def build_catalog():

    models = []

    models.extend(
        discover_ollama()
    )

    models.extend(
        discover_hf()
    )

    models.extend(
        discover_github()
    )


    cleaned = []

    seen = set()


    for model in models:

        model = normalize_model(
            model
        )

        key = (
            model["source"],
            model["name"]
        )


        if key in seen:
            continue


        seen.add(key)

        cleaned.append(
            model
        )


    return cleaned



def sync_catalog(force=False):

    catalog = build_catalog()


    for model in catalog:

        upsert_model(
            model
        )


    return catalog



def get_catalog():

    rows = get_all()


    catalog = []


    for row in rows:

        catalog.append(
            {
                "id": row[0],
                "name": row[1],
                "source": row[2],
                "type": row[3],
                "installed": bool(row[4]),
                "favorite": bool(row[5])
            }
        )


    return catalog
