import re
import os
import shutil
import logging
import urllib.parse
from bs4 import BeautifulSoup

space = 'ConfluenceSpace'
source_folder = 'source' + space 
index_rst = '<RST.md>\n'
rst_title = 'RST Title'

destination_folder = 'path/to/destination/folder' + space 
index_file = source_folder + '/index.html'
allowed_formats = ['.jpg', '.jpeg', '.png', '.gif', '.svg']


class HTMLToMarkdownConverter:
    def __init__(self, url_table):
        self.markdown = ""
        self.url_table = url_table
        self.headerlevel = 1
        self.baseheaderlevel = 0
        self.columns = 0

    def convertStart(self, html,file_name):
        # print("")

        # prepare html
        # split <p>
        matches = re.findall(r'<p.+?<\/p>',html)
        for match in matches:
            replace = re.sub(r'(<.+?>)',r'</md>\1<md>',match)
            replace = replace[5:len(replace)-4].replace('<md></md>','')
            html = html.replace(match,replace)
        # split <a>
        matches = re.findall(r'<a>.+?<\/a>',html)
        for match in matches:
            replace = re.sub(r'(<.+?>)',r'</md>\1<md>',match)
            replace = replace[5:len(replace)-4].replace('<md></md>','')
            html = html.replace(match,replace)
        # split <h?>
        matches = re.findall(r'<h[1-9] .+?<\/h[1-9]>',html)
        for match in matches:
            replace = re.sub(r'(<.+?>)',r'</md>\1<md>',match)
            replace = replace[5:len(replace)-4].replace('<md></md>','')
            html = html.replace(match,replace)
        # split <li
        matches = re.findall(r'<li.+?<\/li>',html)
        for match in matches:
            replace = re.sub(r'(<.+?>)',r'</md>\1<md>',match)
            replace = replace[5:len(replace)-4].replace('<md></md>','')
            html = html.replace(match,replace)

        # split <th
        matches = re.findall(r'<th.+?<\/th>',html)
        for match in matches:
            replace = re.sub(r'(<.+?>)',r'</md>\1<md>',match)
            replace = replace[5:len(replace)-4].replace('<md></md>','')
            html = html.replace(match,replace)
        # split <td
        matches = re.findall(r'<td.+?<\/td>',html)
        for match in matches:
            replace = re.sub(r'(<.+?>)',r'</md>\1<md>',match)
            replace = replace[5:len(replace)-4].replace('<md></md>','')
            html = html.replace(match,replace)



        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted sections:
        self.convertRemove(soup)

        # Get page title
        h1 = soup.find('span', id="title-text")
        if h1 is None:
            title = "<no title>"
        else:
            title = h1.get_text().strip()
            match = re.search(r'[^:]+:\s(.*?)$', title)
            if match:
                title = match.group(1)

        # Add page information
        header = ''
        header += "```{eval-rst} meta data\n"
        header += ":page_owner: Owner Name\n"
        header += ":page_url: `" + self.url_table[file_name] + "`\n"
        header += ":page_urlname: Confluence\n"
        updated = 'unknown'
        metadata = soup.find('div', {"class": "page-metadata"})
        if not metadata is None:
            updated = metadata.get_text().strip()
        header += ":page_updated: " + updated + "\n"
        header += "```\n"
        self.markdown += header +"\n"
        self.markdown += '# ' + title + "\n\n"

        # Find start entry
        starttag = soup.find('div', id="main-content")
        if starttag is None:
            starttag = soup.find('body')

         
        # Convert text tags        
        self.convertTags(starttag)

        # Convert structure tags
        self.convertStructure(starttag,'',0,-1)

    def convertRemove(self, entrytag):

        # Remove unwanted sections:
        breadcrumb = entrytag.find('div', id="breadcrumb-section")
        if (breadcrumb):
            breadcrumb.decompose()
        page_sections = entrytag.find_all("div", {"class": "pageSection"})
        attachments = entrytag.find_all(
            "div", {"class": "plugin_attachments_container"})
        if (page_sections):
            for div in page_sections:
                div.decompose()
        if (attachments):
            for div in attachments:
                div.decompose()
        footer = entrytag.find('div', id="footer")
        if (footer):
            footer.decompose()
        for tag in entrytag.find_all("ul", {'class': 'toc-indentation'}):
            tag.decompose()
        for tag in entrytag.find_all("ul", {'class': 'childpages-macro'}):
            tag.decompose()

    def convertTags(self, entrytag):

        for tag in entrytag.find_all('br'):
            tag.name = 'md'
            tag.string = "<br/>"

        for tag in entrytag.find_all('a'):
            text = tag.get_text().replace('\n',' ').replace('  ',' ').strip()
            if tag.has_attr('href'):
                link_href = tag.get('href')
                if link_href.startswith('swap:') or link_href.startswith('mailto:') or (link_href.startswith('http') and not link_href.startswith('https://confluence.companyName.com/')):
                    text = f" [{text}]({link_href})"
                elif link_href.startswith('/download/attachments') or link_href.startswith('attachments'):
                    text = f" *(removed attachment)* "
                elif link_href.startswith('file://'):
                    text = f" *(removed file)* "          
                elif text != "" :
                    link_href = parse_link_url(link_href)                        
                    if link_href in self.url_table:
                        link_href = self.url_table[link_href]
                    text = f"[{text}]({link_href})"
            tag.name = 'md'
            tag.string = text

        for tag in entrytag.find_all():
            text = tag.get_text().replace('\n',' ').replace('  ',' ').strip()
            if text != "":
                if tag.name == "em":
                    tag.name = 'md'
                    tag.string = "*" + text + "*"
                elif tag.name == "strong":
                    tag.name = 'md'
                    tag.string = "**" + text + "**"
                elif tag.name == "code":
                    tag.name = 'md'
                    tag.string = "`" + text + "`"
                elif tag.name == "s":
                    tag.name = 'md'
                    tag.string = "~~" + text + "~~"
                elif tag.name == "i":
                    tag.name = 'md'
                    tag.string = "__" + text + "__"
                elif tag.name == "hr":
                    tag.name = 'md'
                    tag.string = "\n* * *\n"
            elif tag.name == "img":
                alt_text = tag.get("alt")
                if alt_text is None:
                    alt_text = ''
                src_href = tag.get('src')
                src_href = parse_image_url(src_href)
                if src_href != '':
                    text = f" ![{alt_text}]({src_href}) "
                    tag.name = 'md'
                    tag.string = text                 
 
    def convertStructure(self, entrytag, cellprefix, colspan, listlevel):

        for tag in entrytag.find_all(recursive=False):
            text = tag.get_text().replace('\n',' ').replace('  ',' ')

            # DEBUG
            #if 'td' in tag.name or 'mk' in tag.name or 'li' in tag.name or 'ul' in tag.name:
            #    self.markdown += '\n::' + tag.name + ' = ' + tag.text + '::\n'

            if tag.name == "h1" or tag.name == "h2" or tag.name == "h3" or tag.name == "h4" or tag.name == "h5" or tag.name == "h6":
                if cellprefix == "":              
                    thisheaderlevel = int(tag.name[1:]) + 1
                    self.markdown += f"\n{'#'*thisheaderlevel} "
                    # if self.baseheaderlevel == 0:
                    #     self.baseheaderlevel = thisheaderlevel
                    # deltaheaderlevel = thisheaderlevel - self.baseheaderlevel
                    # if deltaheaderlevel < 0:
                    #     deltaheaderlevel = 0
                    # if deltaheaderlevel > 4:
                    #     deltaheaderlevel = 4
                    # if deltaheaderlevel > 0:
                    #     self.headerlevel += 1
                    # elif deltaheaderlevel < 0:
                    #     self.headerlevel -= 1
                    # self.markdown += f"\n{'#'*self.headerlevel} "
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
                    self.markdown += "\n\n"
            elif tag.name == "p":
                if cellprefix == '':
                    self.markdown += cellprefix
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
                    self.markdown += "\n\n"
                else:
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
                    self.markdown += "<br/>"
            elif tag.name == "ul":
                listlevel += 1
                self.convertStructure(tag, cellprefix, colspan, listlevel)
                listlevel -= 1
            elif tag.name == "li":
                if cellprefix == "":
                    self.markdown += "\n" + ("   "*listlevel) + "* "
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
                else:
                    self.markdown += '¤ ' # + text
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
                    self.markdown += "<br/>"
            elif tag.name == "table":
                # remove sub tables, not handled yet
                tables = tag.find_all("table")
                for table in tables:
                    table.decompose()

                rows = tag.find_all("tr")
                actualrows = 0
                max_columns = 0
                for row in rows:
                    if len(row.find_all(["th", "td"])) > 1:
                        actualrows += 1
                        columncounter = 0
                        columns = row.find_all(["th", "td"])
                        for column in columns:
                            if column.has_attr('colspan'):                  
                               columncounter += max(int(column.get("colspan")),1)
                            else:
                               columncounter += 1
                        max_columns = max(max_columns,columncounter)

                if actualrows > 0:
                    table_title = tag.caption.get_text().strip() if tag.caption else ""
                    self.markdown += f"\n\n:::{{list-table}} {table_title}\n"
                    header_rows = int(tag.get("data-header-rows", "1"))
                    self.markdown += f":header-rows: {header_rows}\n\n"
                    self.convertStructure(tag, cellprefix, max_columns, listlevel)
                    self.columns = max_columns               
                    if actualrows == 1:
                        self.markdown += "*   - \n" 
                        if max_columns > 1:
                            self.markdown += ('    - \n')*(max_columns - 1)
                    self.markdown += ":::\n\n"
            elif tag.name == "tr":
                if len(tag.find_all(["th", "td"])) > 1:
                    cellprefix = "*   - "
                    self.columns = 0
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
                    if self.columns < colspan:
                        self.markdown += ('    - \n')*(colspan - self.columns)
            elif tag.name == "td" or tag.name == "th":
                self.markdown += cellprefix
                self.convertStructure(tag, 'nocellprefix', 0, listlevel)
                self.markdown += "\n"
                if tag.has_attr('colspan'):                  
                    self.markdown += ('    - \n')*(int(tag.get("colspan")) -1)
                    self.columns += max(int(tag.get("colspan")),1)
                else:
                    self.columns += 1
            elif tag.name == 'div' and tag.has_attr('class'):
                if cellprefix == '' and tag.attrs["class"][0] == 'confluence-information-macro-body':
                    if text != '' or len(tag.find_all(recursive=False)) > 0:
                        self.markdown += "\n\n```{note}\n"
                        if len(tag.find_all(recursive=False)) == 0:
                            self.markdown += text
                        else:
                            self.convertStructure(tag, cellprefix, colspan, listlevel)
                        self.markdown += "\n```\n\n"
                else:
                    self.convertStructure(tag, cellprefix, colspan, listlevel)
            elif tag.name == "md":
                if text.startswith('-'):
                    text = '\\' + text
                self.markdown += text
            else:
                self.convertStructure(tag, cellprefix, colspan, listlevel)

            if cellprefix == '*   - ':
                cellprefix = '    - '
        cellprefix = ''

# ----------------- HELPERS -------------------

def parse_image_url(url):
    url = re.sub(r'(\?.*)', '', url)
    if '/thumbnail/' in url:
       url = ''
    elif 'download/resources' in url:
       url = ''
    elif 'plugins/servlet' in url:
        url = ''
    elif url is None:
        url = ''
    return url

def parse_link_url(url):
    url = re.sub(r'(\#.*)', '', url)
    if '/pages/createpage.action' in url:
        return 'http://linkremoved'
    elif 'https://confluence.companyName.com/display/~' in url:
        return 'http://linkremoved'
    elif url.startswith('ssh:'):
        return 'http://linkremoved'
    elif url.startswith('/display/'):
        return 'https://confluence.companyName.com' + url
    elif url == "":
        return 'http://linkremoved'
    return url

# ----------------- MAIN -------------------

def build_url_table():
    # Get all links (e.g. <a href="TIOC-SW-V436_368588402.html">TIOC SW V436</a>)
    # in index.rst, set all url variants with filename.md 

    url_table = {}
    max_files = 0

    index_table = {}

    with open(index_file, 'r', encoding='utf-8') as file:
        html = file.read()
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            if href not in index_table:
                index_table[href] = href

    for root, _, files in os.walk(source_folder):
        for file_name in files:
            max_files += 1

            if file_name.endswith('.html'):

                print(f"Processing: {file_name}" , end='\r')

                source_file_path = os.path.join(root, file_name)

                with open(source_file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                    soup = BeautifulSoup(html_content, "html.parser")

                    h1 = soup.find('span', id="title-text")
                    if h1 is None:
                        title = "<no title>"
                        filename_md = file_name.replace('.html','.md')
                    else:
                        title = h1.get_text().strip()
                        match = re.search(r'[^:]+:\s(.*?)$', title)
                        if match:
                            title = match.group(1)
                        filename_md = re.sub(r'[^a-zA-Z0-9]+','-',title).lower() + '.md'

                if file_name in index_table:

                    href = file_name.replace('.html','')

                    if href.isdigit():

                        # replace internal hrefs with md-name
                        url_table['https://confluence.companyName.com/pages/viewpage.action?pageId=' + href] = filename_md

                        # replace md-name with full confluence url
                        url_table[filename_md] = 'confluence.companyName.com/pages/viewpage.action?pageId=' + href

                    else:
                        href = urllib.parse.quote_plus(title,'().-')

                        # replace internal hrefs with md-name
                        url_table[href] = filename_md
                        url_table['/display/' + space+ '/' + href] = filename_md
                        url_table['https://confluence.companyName.com/display/' + space+ '/' + href] = filename_md

                        # replace md-name with full confluence url
                        url_table[filename_md] = 'confluence.companyName.com/display/' +space + '/' + href

                    # replace sourcename with md-name
                    url_table[file_name] = filename_md

    return url_table, max_files


def extract_toc_structure(html_file,url_table):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    def calculate_indentation(tag):
        indentation = 0
        parent = tag.find_parent(['ul'])
        while parent:
            indentation += 1
            parent = parent.find_parent(['ul'])
        return indentation

    toc_structure = []

    for anchor in soup.find_all('a', href=True):
        link = anchor['href']
        if link.endswith('.html'):
            text = re.sub(r' +', ' ', anchor.get_text().replace('\n', ' '))
            indentation = calculate_indentation(anchor)

            url = url_table[link]

            toc_structure.append(
                {'text': text, 'link': url, 'indentation': indentation})

    return toc_structure


def create_toc_tree(toc_structure):
    toc_tree = []
    stack = []

    for item in toc_structure:
        while stack and stack[-1]['indentation'] >= item['indentation']:
            stack.pop()

        if not stack:
            toc_tree.append(item)
        else:
            parent = stack[-1]
            if 'subitems' not in parent:
                parent['subitems'] = []
            parent['subitems'].append(item)

        stack.append(item)

    return toc_tree

def write_toctree(toc_tree, file, name):
    page = find_value_recursive(toc_tree, name)
    if page and 'subitems' in page:
        if name.startswith('proce'):
            print("write")

        file.write("\n\n```{toctree}\n")
        file.write("   :hidden:\n\n")

        for item in page['subitems']:
            text = ('   ' + item['text'] + ' <' + item['link'] + '>').replace('\n',' ') + '\n'
            file.write(text)

        file.write("```\n")


def write_index_rst(path, title):
    tree = f"{title}\n" + '=' * \
        len(title) + '\n\n' + ".. toctree::\n   :hidden:\n\n"
    tree += '   ' + path
    with open(destination_folder + '/index.rst', 'w', encoding='utf-8') as file:
        file.write(tree)


def find_value_recursive(data, target_key):
    if isinstance(data, dict):
        if 'link' in data and data['link'] == target_key:
            return data
        for key, value in data.items():
            result = find_value_recursive(value, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_value_recursive(item, target_key)
            if result is not None:
                return result
    return None     


def run_conversion():
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    os.makedirs(destination_folder)
    n = 0

    url_table, maxfiles = build_url_table()
    toc_structure = extract_toc_structure(index_file,url_table)
    toc_tree = create_toc_tree(toc_structure)
    filename_len = 20

    write_index_rst(index_rst, rst_title)

    for root, _, files in os.walk(source_folder):
        for file_name in files:
            n += 1

            print(f"[{n}/{maxfiles}] Processing: {file_name}" +
                    ' '*filename_len, end='\r')
            filename_len = len(file_name)

            source_file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(
                source_file_path, source_folder)
            destination_file_path = os.path.join(
                destination_folder, relative_path)

            os.makedirs(os.path.dirname(
                destination_file_path), exist_ok=True)

            if file_name.endswith('.html'):

                if file_name in url_table: 

                    with open(source_file_path, 'r', encoding='utf-8') as file:
                        html_content = file.read()

                    converter = HTMLToMarkdownConverter(url_table)
                    converter.convertStart(html_content,url_table[file_name])
                    markdown_content = converter.markdown

                    destination_file = destination_folder + '/' + url_table[file_name]
                    with open(destination_file, 'w', encoding='utf-8') as file:

                        file.write(markdown_content)
                        write_toctree(toc_tree, file, url_table[file_name])

                    #updated_filename = file_name
                    #if file_name in url_table:
                    #    updated_filename = url_table[file_name]
                    #    destination_file = destination_folder + '/' + updated_filename
                    #    with open(destination_file, 'w', encoding='utf-8') as file:
                    #        file.write(markdown_content)
                    #        write_toctree(toc_tree, file, url_table[file_name])

            else:
                for format in allowed_formats:
                    if file_name.endswith(format) or (file_name.isdigit() and not '.' in file_name):
                        shutil.copyfile(source_file_path,
                                        destination_file_path)
                         

    print('')
    print("HTML to Markdown conversion completed.")
 

if __name__ == '__main__':
    run_conversion()
