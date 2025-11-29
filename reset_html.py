import requests

url = "https://cz.gamcore.com/advertise"
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
response.raise_for_status()

with open("optimized_site/index.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Reset index.html from live site.")