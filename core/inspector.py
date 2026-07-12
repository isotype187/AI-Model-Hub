from core.hardware import estimate_model_cost, get_specs
from core.categories import categorize


def inspect_model(model):
    """
    MODULE: Model Inspector

    PURPOSE:
    Creates a complete information profile for a model.

    OUTPUT:
    Data used by the UI model details panel.

    DEPENDS ON:
    Hardware detection and categories.

    NEVER:
    Modifies models or downloads files.
    """

    specs = get_specs()

    category = categorize(model)

    return {
        "id": model.get("id"),
        "name": model.get("name"),
        "provider": model.get("provider"),
        "type": model.get("type"),
        "source": model.get("source"),
        "size": model.get("size"),
        "installed": model.get("installed", False),
        "favorite": model.get("favorite", False),

        "category": category,

        "cost": estimate_model_cost(model),

        "hardware": {
            "system_ram": specs["ram_gb"],
            "system_cpu": specs["cpu"],
            "gpu": specs["gpu"],
            "vram": specs["vram_mb"]
        },

        "summary":
            f"{model.get('name')} is a {category} model "
            f"from {model.get('source')}."
    }
