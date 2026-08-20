
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment
import markdown


TEMPLATE_FILE = "template.html"


def slugify(text):
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text


def process_video_macros(md):
    """Process video embedding macros"""
    # Handle local videos: [VIDEO <path>]
    def replace_local_video(match):
        path = match.group(1)
        return f'<video class="videoEmbed" controls type="video/mp4" src="{path}" preload="metadata"></video>'
    
    md = re.sub(r'\[VIDEO\s+(.+?)\]', replace_local_video, md, flags=re.IGNORECASE)
    
    # Handle external videos: [IFRAME <video id>]
    def replace_external_video(match):
        video_id = match.group(1)
        return f'<iframe class="youtubeEmbed" src="https://www.youtube.com/embed/{video_id}"></iframe>'
    
    md = re.sub(r'\[IFRAME\s+(.+?)\]', replace_external_video, md, flags=re.IGNORECASE)
    return md


def markdown_to_html(md):
    # Process video macros before markdown conversion
    md = process_video_macros(md)

    html = markdown.markdown(
        md,
        extensions=[
            "extra",
            "sane_lists",
        ],
    )

    article = BeautifulSoup(html, "html.parser")
    for img in article.find_all("img"):
        wrapper = article.new_tag("div")
        wrapper["class"] = "articleRight"

        inner = article.new_tag("div")
        inner["class"] = "articleRightInner"

        new_img = article.new_tag("img")
        new_img["src"] = img.get("src", "")

        # Preserve other attributes if present
        if img.get("title"):
            new_img["title"] = img["title"]

        if img.get("width"):
            new_img["width"] = img["width"]

        if img.get("height"):
            new_img["height"] = img["height"]

        inner.append(new_img)
        wrapper.append(inner)

        alt = img.get("alt", "")
        if alt:
            wrapper.append(alt)

        img.replace_with(wrapper)

    h1 = article.find("h1")
    page_title = h1.get_text() if h1 else "Untitled"

    sections = []
    current = None

    for child in list(article.children):
        if getattr(child, "name", None) == "h2":
            sid = slugify(child.get_text())

            section = article.new_tag("section")
            section["id"] = sid

            child.extract()
            section.append(child)

            article.append(section)

            current = section
            sections.append((sid, child.get_text()))
            continue

        if current is not None:
            child.extract()
            current.append(child)

    return page_title, article, sections


def refresh_file(file_path):
    """Regenerate HTML from markdown and save the file"""
    # Read the HTML file
    html_content = Path(file_path).read_text(encoding="utf8")
    
    # Parse it to find embedded markdown
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Find the markdown comment
    markdown_comment = None
    for node in soup.find_all(string=lambda t: isinstance(t, Comment)):
        text = str(node)
        if text.startswith("MARKDOWN\n") and text.endswith("\nMARKDOWN"):
            markdown_comment = text
            break
    
    if not markdown_comment:
        print(f"Error: No embedded markdown found in {file_path}")
        return False
    
    # Extract markdown content
    md = markdown_comment[len("MARKDOWN\n"):-len("\nMARKDOWN")]
    md = md.replace("--&gt;", "-->")
    
    # Read template
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Error: Template file '{TEMPLATE_FILE}' not found")
        return False
    
    # Convert back to HTML
    title, article, toc = markdown_to_html(md)
    soup = BeautifulSoup(template, "html.parser")
    
    # Set title
    soup.title.string = title if title else "Untitled"
    
    # Add markdown comment back
    md = md.replace("-->", "--&gt;")
    comment = Comment("MARKDOWN\n" + md + "\nMARKDOWN")
    if soup.html:
        soup.html.insert(0, comment)
    else:
        soup.insert(0, comment)
    
    # Replace article content
    article_div = soup.find("div", class_="article")
    if article_div:
        article_div.clear()
        for element in list(article.contents):
            article_div.append(element)
    
    # Update table of contents
    ul = soup.find("div", class_="contentsPanel").find("ul")
    if ul:
        ul.clear()
        for i, (sid, name) in enumerate(toc, start=1):
            li = soup.new_tag("li")
            span = soup.new_tag("span")
            span.string = str(i)
            a = soup.new_tag("a", href="#" + sid)
            a.string = name
            li.append(span)
            li.append(a)
            ul.append(li)
    
    # Save the updated HTML
    Path(file_path).write_text(str(soup), encoding="utf8")
    print(f"Refreshed {file_path}")
    return True


def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print("Usage: python refresh_page.py page.html")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if the file exists
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' does not exist")
        sys.exit(1)
    
    # Refresh the file
    success = refresh_file(file_path)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
