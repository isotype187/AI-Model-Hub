import subprocess


def get_installed_models():
    """
    MODULE: Ollama Provider

    PURPOSE:
    Connects AI_Model_Hub to the local Ollama runtime.

    INPUT:
    Ollama CLI model inventory.

    OUTPUT:
    Normalized model records.

    NEVER:
    Downloads, removes, or modifies models.
    """

    try:
        output = subprocess.check_output(
            ["ollama", "list"],
            text=True
        )

        lines = output.strip().splitlines()

        models = []

        for line in lines[1:]:
            parts = line.split()

            if len(parts) >= 4:

                name = parts[0]

                models.append(
                    {
                        "id": f"ollama:{name}",
                        "name": name,
                        "hash": parts[1],
                        "size": parts[2] + " " + parts[3],
                        "provider": "ollama",
                        "installed": True
                    }
                )

        return models

    except Exception as error:
        return [
            {
                "provider": "ollama",
                "error": str(error)
            }
        ]


def check_ollama():

    try:
        subprocess.check_output(
            ["ollama", "--version"],
            text=True
        )

        return True

    except Exception:
        return False
