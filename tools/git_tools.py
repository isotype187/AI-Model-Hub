import subprocess


def git_status() -> str:
    """
    Returns the current git repository status.
    """

    result = subprocess.run(
        [
            "git",
            "status"
        ],
        cwd="D:/AI_Model_Hub",
        capture_output=True,
        text=True
    )


    return (
        result.stdout +
        result.stderr
    )
