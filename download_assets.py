import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Base URL for resolving relative links
BASE_URL = "https://cz.gamcore.com/advertise"

# Output directory
OUTPUT_DIR = "optimized_site"
CSS_DIR = os.path.join(OUTPUT_DIR, "css")
JS_DIR = os.path.join(OUTPUT_DIR, "js")
IMG_DIR = os.path.join(OUTPUT_DIR, "images")
FONTS_DIR = os.path.join(OUTPUT_DIR, "fonts")

for d in [CSS_DIR, JS_DIR, IMG_DIR, FONTS_DIR]:
    os.makedirs(d, exist_ok=True)

def download_file(url, dest_folder, filename=None):
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = urljoin(BASE_URL, url)
    
    if not filename:
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = "resource"
            
    # Clean filename
    filename = re.sub(r'[?].*', '', filename)
    
    filepath = os.path.join(dest_folder, filename)
    
    try:
        print(f"Downloading {url} to {filepath}")
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filename
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def process_html():
    try:
        with open(os.path.join(OUTPUT_DIR, "index.html"), "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except UnicodeDecodeError:
        with open(os.path.join(OUTPUT_DIR, "index.html"), "r", encoding="latin-1") as f:
            soup = BeautifulSoup(f, "html.parser")

    # Process CSS
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            filename = download_file(href, CSS_DIR)
            if filename:
                link["href"] = f"css/{filename}"
                # Remove integrity and crossorigin attributes as we are modifying the file
                if link.has_attr("integrity"): del link["integrity"]
                if link.has_attr("crossorigin"): del link["crossorigin"]

    # Process Inline CSS Imports
    style_tags = soup.find_all("style")
    for style in style_tags:
        if style.string:
            import_match = re.search(r'@import url\("([^"]+)"\);', style.string)
            if import_match:
                url = import_match.group(1)
                filename = download_file(url, CSS_DIR)
                if filename:
                    style.string = style.string.replace(import_match.group(0), f'@import url("css/{filename}");')

    # Process JS
    for script in soup.find_all("script", src=True):
        src = script.get("src")
        if src:
            filename = download_file(src, JS_DIR)
            if filename:
                script["src"] = f"js/{filename}"
                if script.has_attr("integrity"): del script["integrity"]
                if script.has_attr("crossorigin"): del script["crossorigin"]

    # Process Images
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            filename = download_file(src, IMG_DIR)
            if filename:
                img["src"] = f"images/{filename}"
                # Add lazy loading
                img["loading"] = "lazy"
                # Add width and height if missing (placeholder, ideally should be real dims)
                if not img.has_attr("width"): img["width"] = "100"
                if not img.has_attr("height"): img["height"] = "100"

    # Process Favicon
    link_icon = soup.find("link", rel="shortcut icon")
    if link_icon:
        href = link_icon.get("href")
        if href:
            filename = download_file(href, IMG_DIR)
            if filename:
                link_icon["href"] = f"images/{filename}"

    # Process og:image
    meta_image = soup.find("meta", property="og:image")
    if meta_image:
        content = meta_image.get("content")
        if content:
            filename = download_file(content, IMG_DIR)
            if filename:
                meta_image["content"] = f"images/{filename}"
    
    link_image_src = soup.find("link", rel="image_src")
    if link_image_src:
        href = link_image_src.get("href")
        if href:
            filename = download_file(href, IMG_DIR)
            if filename:
                link_image_src["href"] = f"images/{filename}"


    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(str(soup))

if __name__ == "__main__":
    process_html()
