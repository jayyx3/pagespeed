import os
import glob
from PIL import Image
from csscompressor import compress
from jsmin import jsmin
from bs4 import BeautifulSoup
import re

OUTPUT_DIR = "."
CSS_DIR = os.path.join(OUTPUT_DIR, "css")
JS_DIR = os.path.join(OUTPUT_DIR, "js")
IMG_DIR = os.path.join(OUTPUT_DIR, "images")

def optimize_images():
    print("Optimizing images...")
    image_map = {}
    for filepath in glob.glob(os.path.join(IMG_DIR, "*")):
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            webp_filename = f"{name}.webp"
            webp_filepath = os.path.join(IMG_DIR, webp_filename)
            
            try:
                with Image.open(filepath) as img:
                    img.save(webp_filepath, "WEBP", quality=80, optimize=True)
                
                image_map[filename] = webp_filename
                print(f"Converted {filename} to {webp_filename}")
                
                # Remove original file to save space/confusion, or keep it? 
                # Let's keep it for now but the HTML will point to webp
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")
    return image_map

def minify_css():
    print("Minifying CSS...")
    for filepath in glob.glob(os.path.join(CSS_DIR, "*.css")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add font-display: swap
            content = re.sub(r'@font-face\s*{', r'@font-face { font-display: swap; ', content)
            
            minified = compress(content)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(minified)
            print(f"Minified {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Failed to minify {filepath}: {e}")

def minify_js():
    print("Minifying JS...")
    for filepath in glob.glob(os.path.join(JS_DIR, "*.js")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            minified = jsmin(content)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(minified)
            print(f"Minified {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Failed to minify {filepath}: {e}")

def update_html(image_map):
    print("Updating HTML...")
    html_path = os.path.join(OUTPUT_DIR, "index.html")
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except UnicodeDecodeError:
        with open(html_path, "r", encoding="latin-1") as f:
            soup = BeautifulSoup(f, "html.parser")

    # Update Images to WebP
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith("images/"):
            filename = os.path.basename(src)
            if filename in image_map:
                img["src"] = f"images/{image_map[filename]}"
                
    # Update meta og:image
    meta_image = soup.find("meta", property="og:image")
    if meta_image:
        content = meta_image.get("content")
        if content and content.startswith("images/"):
            filename = os.path.basename(content)
            if filename in image_map:
                meta_image["content"] = f"images/{image_map[filename]}"

    # Update link rel="image_src"
    link_image = soup.find("link", rel="image_src")
    if link_image:
        href = link_image.get("href")
        if href and href.startswith("images/"):
            filename = os.path.basename(href)
            if filename in image_map:
                link_image["href"] = f"images/{image_map[filename]}"

    # Ensure all JS is deferred or async
    for script in soup.find_all("script"):
        if script.get("src"):
            # If it's not already async or defer, make it defer
            if not script.get("async") and not script.get("defer"):
                script["defer"] = ""

    # --- CSS OPTIMIZATION STRATEGY ---
    # 1. Inline ONLY site.css (Critical Layout)
    # 2. Preload Bootstrap, FontAwesome, Roboto (Non-Critical / Large)
    
    print("Optimizing CSS Delivery...")
    
    # Inline site.css
    site_css_path = os.path.join(CSS_DIR, "site.css")
    if os.path.exists(site_css_path):
        with open(site_css_path, "r", encoding="utf-8") as f:
            site_css_content = f.read()
            # Add font-display: swap
            site_css_content = re.sub(r'@font-face\s*{', r'@font-face { font-display: swap; ', site_css_content)
            
        style_tag = soup.new_tag("style")
        style_tag.string = site_css_content
        soup.head.append(style_tag)
        
        # Remove the link to site.css
        link_tag = soup.find("link", href="css/site.css")
        if link_tag:
            link_tag.decompose()
            
        # Remove @import for site.css
        for style in soup.find_all("style"):
            if style.string and 'css/site.css' in style.string:
                if style.string.strip() == '@import url("css/site.css");':
                    style.decompose()
                else:
                    style.string = style.string.replace('@import url("css/site.css");', "")

    # Preload other CSS files
    other_css_files = ["bootstrap.min.css", "bootstrap-formhelpers.min.css", "roboto.css", "all.min.css"]
    for css_file in other_css_files:
        # Find the existing link tag
        link_tag = soup.find("link", href=f"css/{css_file}")
        if link_tag:
            # Change it to preload
            link_tag["rel"] = "preload"
            link_tag["as"] = "style"
            link_tag["onload"] = "this.onload=null;this.rel='stylesheet'"
            # Add noscript fallback
            noscript = soup.new_tag("noscript")
            link_fallback = soup.new_tag("link", rel="stylesheet", href=f"css/{css_file}")
            noscript.append(link_fallback)
            soup.head.append(noscript)

    # --- LCP OPTIMIZATION ---
    # Find the logo (LCP candidate) and remove lazy loading
    # It's usually the first image or the one with "logo" in src/class
    print("Optimizing LCP...")
    logo_img = soup.find("img", src=re.compile(r"chimney|logo", re.I))
    if logo_img:
        if "loading" in logo_img.attrs:
            del logo_img["loading"]
        # Add preload link
        preload_link = soup.new_tag("link", rel="preload", href=logo_img["src"], as_="image")
        soup.head.insert(0, preload_link)
        print(f"Preloaded LCP image: {logo_img['src']}")

    # Also remove the Google Fonts link if it exists (we are using local roboto.css)
    google_fonts_link = soup.find("link", href=re.compile(r"fonts\.googleapis\.com"))
    if google_fonts_link:
        google_fonts_link.decompose()

    # Minify HTML
    html_content = str(soup)
    # Remove comments
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
    # Remove whitespace between tags
    html_content = re.sub(r'>\s+<', '><', html_content)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML updated and minified.")

if __name__ == "__main__":
    image_map = optimize_images()
    minify_css()
    minify_js()
    update_html(image_map)
