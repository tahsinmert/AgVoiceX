import json
import os
from pathlib import Path
from urllib import request


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SEED_FILE = Path(__file__).resolve().parents[1] / "database" / "seed_knowledge.json"


def main() -> None:
    items = json.loads(SEED_FILE.read_text())
    for item in items:
        payload = json.dumps(item).encode()
        http_request = request.Request(
            f"{API_BASE_URL}/api/v1/knowledge",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"Failed to seed {item['title']}: HTTP {response.status}")
        print(f"Seeded: {item['title']}")


if __name__ == "__main__":
    main()
