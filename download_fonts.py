import os
import requests
import re
from urllib.parse import urljoin

OUTPUT_DIR = "optimized_site"
WEBFONTS_DIR = os.path.join(OUTPUT_DIR, "webfonts")
CSS_DIR = os.path.join(OUTPUT_DIR, "css")
FONTS_DIR = os.path.join(OUTPUT_DIR, "fonts")

os.makedirs(WEBFONTS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

def download_file(url, dest_path):
    try:
        print(f"Downloading {url} to {dest_path}")
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def download_font_awesome():
    base_url = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.6.3/webfonts/"
    fonts = [
        "fa-brands-400.woff2",
        "fa-regular-400.woff2",
        "fa-solid-900.woff2",
        "fa-brands-400.woff",
        "fa-regular-400.woff",
        "fa-solid-900.woff",
        "fa-brands-400.ttf",
        "fa-regular-400.ttf",
        "fa-solid-900.ttf"
    ]
    
    for font in fonts:
        download_file(base_url + font, os.path.join(WEBFONTS_DIR, font))

def download_google_fonts():
    # Google Fonts URL
    css_url = "https://fonts.googleapis.com/css?family=Roboto:100,100i,300,300i,400,400i,500,500i,700,700i,900,900i"
    
    # Download CSS content
    response = requests.get(css_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    css_content = response.text
    
    # Find all font URLs
    # src: url(https://fonts.gstatic.com/s/roboto/v30/KFOlCnqEu92Fr1MmEU9fBBc4.woff2) format('woff2');
    matches = re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css_content)
    
    local_css_content = css_content
    
    for i, url in enumerate(matches):
        filename = f"roboto-{i}.woff2"
        filepath = os.path.join(FONTS_DIR, filename)
        
        if download_file(url, filepath):
            # Replace URL in CSS
            local_css_content = local_css_content.replace(url, f"../fonts/{filename}")
            
    # Save the new CSS file
    with open(os.path.join(CSS_DIR, "roboto.css"), "w", encoding="utf-8") as f:
        f.write(local_css_content)

if __name__ == "__main__":
    download_font_awesome()
    download_google_fonts()
