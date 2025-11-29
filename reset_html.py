import requests
import os

url = "https://cz.gamcore.com/advertise"
try:
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    response.raise_for_status()

    output_path = os.path.join("optimized_site", "index.html")
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Reset index.html from live site. Size: {len(response.text)} bytes")
except Exception as e:
    print(f"Failed to reset HTML: {e}")
    exit(1)