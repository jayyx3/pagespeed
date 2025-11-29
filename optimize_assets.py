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

# Critical CSS extracted from site.css to prevent CLS while keeping HTML size low
CRITICAL_CSS = """
body{background:#141414;font-family:'Roboto',sans-serif;font-size:14px;color:#fff}
#wrapper{width:100%;float:left;overflow:hidden}
.mycontainer{padding:0 15px;margin:0 auto;max-width:1140px;width:100%;position:relative}
#headerCntr{padding:20px 20px 0 20px;width:100%;float:left;background:#2a2a2a}
.logoArea{margin:5px 0 0 0;float:left}
.logoArea a{display:block}
.logoArea a img{width:195px}
.headerRight{float:right}
.menuArea{padding:20px 0 0 0;width:100%;float:left}
.menuArea ul{list-style:none}
.menuArea li{margin-right:35px;float:left}
.menuArea li a{padding-bottom:14px;display:block;font-size:16px;color:#fff;font-weight:500;text-decoration:none;border-bottom:2px solid transparent}
#middleCntr{width:100%;float:left}
.middleBox{padding:50px 0;width:100%;float:left}
.list_sideBar{width:100%;float:left}
.midcontent{padding:0;width:100%;float:left}
.d-none{display:none!important}
.d-block{display:block!important}
@media(min-width:768px){.d-md-block{display:block!important}.d-md-none{display:none!important}}
@media(min-width:992px){.d-lg-block{display:block!important}}
@media(min-width:1200px){.d-xl-block{display:block!important}}
"""

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
    # 1. Inline bootstrap-grid.min.css (Layout Structure)
    # 2. Inline Critical CSS (Header/Layout)
    # 3. Preload site.css and others
    
    print("Optimizing CSS Delivery...")
    
    # Inline bootstrap-grid.min.css FIRST (to establish layout)
    # Check if already inlined to avoid duplicates
    grid_already_inlined = False
    for style in soup.find_all("style"):
        if style.string and "Bootstrap Grid" in style.string:
            grid_already_inlined = True
            break
            
    if not grid_already_inlined:
        grid_css_path = os.path.join(CSS_DIR, "bootstrap-grid.min.css")
        if os.path.exists(grid_css_path):
            with open(grid_css_path, "r", encoding="utf-8") as f:
                grid_css_content = f.read()
            
            grid_style_tag = soup.new_tag("style")
            grid_style_tag.string = grid_css_content
            soup.head.insert(0, grid_style_tag) # Insert at the very top of head
            print("Inlined bootstrap-grid.min.css")
    else:
        print("Bootstrap Grid already inlined, skipping.")

    # Inline Critical CSS
    # Check if already inlined
    critical_already_inlined = False
    for style in soup.find_all("style"):
        if style.string and "#headerCntr" in style.string and "Bootstrap Grid" not in style.string:
            critical_already_inlined = True
            break
            
    if not critical_already_inlined:
        critical_style_tag = soup.new_tag("style")
        critical_style_tag.string = compress(CRITICAL_CSS)
        soup.head.append(critical_style_tag)
        print("Inlined Critical CSS")
    else:
        print("Critical CSS already inlined, skipping.")

    # Preload site.css and others
    # Ensure site.css is linked (if it was removed in previous runs, we need to add it back)
    # But since we are running on the source file (or a copy), we assume the link might be there or we add it.
    # The previous script removed it. Let's check if it exists, if not add it.
    
    css_files_to_preload = ["site.css", "bootstrap.min.css", "bootstrap-formhelpers.min.css", "roboto.css", "all.min.css"]
    
    # First, remove existing links to these files to avoid duplicates/conflicts
    for css_file in css_files_to_preload:
        link_tag = soup.find("link", href=f"css/{css_file}")
        if link_tag:
            link_tag.decompose()
            
    # Now add them back as preload
    for css_file in css_files_to_preload:
        link_tag = soup.new_tag("link", rel="preload", href=f"css/{css_file}", as_="style")
        link_tag["onload"] = "this.onload=null;this.rel='stylesheet'"
        soup.head.append(link_tag)
        
        # Add noscript fallback
        noscript = soup.new_tag("noscript")
        link_fallback = soup.new_tag("link", rel="stylesheet", href=f"css/{css_file}")
        noscript.append(link_fallback)
        soup.head.append(noscript)

    # Remove @import for site.css if it exists in any style tag
    for style in soup.find_all("style"):
        if style.string and 'css/site.css' in style.string:
            if style.string.strip() == '@import url("css/site.css");':
                style.decompose()
            else:
                style.string = style.string.replace('@import url("css/site.css");', "")

    # --- JS OPTIMIZATION ---
    # Replace the inline script block with deferred js/config.js
    # Look for the script containing FGJSRAND
    for script in soup.find_all("script"):
        if script.string and "FGJSRAND=" in script.string:
            print("Found inline config script. Replacing with deferred js/config.js")
            new_script = soup.new_tag("script", src="js/config.js", defer="")
            script.replace_with(new_script)

    # --- LCP OPTIMIZATION ---
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
    # We assume images are already optimized or we run it again
    # image_map = optimize_images() 
    # For speed in this iteration, let's just get the map without re-converting if possible
    # But optimize_images is fast if files exist.
    image_map = optimize_images()
    minify_css()
    minify_js()
    update_html(image_map)
