from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request
import webbrowser

from medrag.api import main


def open_browser_when_ready() -> None:
    url = "http://127.0.0.1:8090/"
    for _ in range(120):
        try:
            with urllib.request.urlopen(f"{url}health", timeout=1):
                webbrowser.open(url)
                return
        except (OSError, urllib.error.URLError):
            time.sleep(1)


if __name__ == "__main__":
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    main()
