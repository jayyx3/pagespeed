from bs4 import BeautifulSoup
import os

html_path = "index.html"
with open(html_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Remove all style tags (cleaning up my previous inlining)
for style in soup.find_all("style"):
    style.decompose()

# Remove all preload/stylesheet links to our known CSS files
css_files = ["site.css", "bootstrap.min.css", "bootstrap-formhelpers.min.css", "roboto.css", "all.min.css", "bootstrap-grid.min.css"]
for link in soup.find_all("link"):
    href = link.get("href", "")
    for css in css_files:
        if css in href:
            link.decompose()

with open(html_path, "w", encoding="utf-8") as f:
    f.write(str(soup))

print("Cleaned CSS from index.html")
