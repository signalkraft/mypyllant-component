import re
from pathlib import Path


async def test_mypyllant_versions():
    """
    Make sure myPyllant library is set to the same versions in all important files
    """
    files = [
        Path(".").parent / ".pre-commit-config.yaml",
        Path(".").parent / "requirements.test.txt",
        Path(".").parent / "custom_components/mypyllant/manifest.json",
    ]
    p = re.compile(r"myPyllant==(.*?)[\"\n]")
    matches = [re.findall(p, f.read_text()) for f in files]
    assert all(
        m == matches[0] for m in matches
    ), f"myPyllant versions are not the same in all files: {matches}"
