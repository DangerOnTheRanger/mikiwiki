#!/usr/bin/env python

import os
import sys
import cgi
import urlparse
import cgitb
cgitb.enable()


DATA_ROOT = os.path.abspath(os.path.join(os.curdir, '_data'))
ARTICLE_ROOT = os.path.abspath(os.path.join(os.curdir, 'articles'))
ARTICLE_EXTENSION = '.txt'
DEFAULT_PAGE = 'MainPage'
NOT_FOUND_PAGE = 'PageNotFound' + ARTICLE_EXTENSION
ARTICLE_TEMPLATE = os.path.abspath(os.path.join(DATA_ROOT, 'page-template.html'))
PRE_PAGE_MESSAGE = '''Content-Type: text/html
'''


def get_article_body(name):

    try:
        article_file = open(os.path.join(ARTICLE_ROOT, name + ARTICLE_EXTENSION))
        article_data = parse_markdown(article_file.read())
        return article_data
    except IOError:
        error_page = open(os.path.join(ARTICLE_ROOT, NOT_FOUND_PAGE))
        error_page_data = parse_markdown(error_page.read())
        return error_page_data


def get_page_for_article(name):

    article_body = get_article_body(name)
    article_template = open(ARTICLE_TEMPLATE).read()

    
    final_article = article_template % {'article_name' : name, 'article_body' : article_body}
    return final_article % {'article_name' : name}


def write_page(name, data):

    article_file = open(os.path.join(ARTICLE_ROOT, name + ARTICLE_EXTENSION), 'w')
    article_file.write(data)
    article_file.close()


def serve():

    print PRE_PAGE_MESSAGE
    query_string = urlparse.parse_qs(os.environ['QUERY_STRING'])

    if query_string.get('page'):
        page = query_string['page'][0]
        print get_page_for_article(page)
    elif query_string.get('new'):
        upload_form = open(os.path.join(DATA_ROOT, 'upload-form.html')).read()
        article_name = query_string['new'][0]
        print upload_form % {'article_name' : article_name, 'article_content' : 'Content goes here.'}
    elif query_string.get('edit'):
        edit_form = open(os.path.join(DATA_ROOT, 'edit-form.html')).read()
        article_name = query_string['edit'][0]
        article_file = open(os.path.join(ARTICLE_ROOT, article_name + ARTICLE_EXTENSION))
        print edit_form  % {'article_name' : article_name, 'article_content' : article_file.read()}
    elif query_string.get('save'):
        article_name = query_string['save'][0]
        form = cgi.FieldStorage()
        data = form['articlecontent'].value
        write_page(article_name, data)
        print get_page_for_article(article_name)
    else:
        print get_page_for_article(DEFAULT_PAGE)


def _parse_markdown_line(line):

    output = ''
    bold_enabled = False
    italics_enabled = False
    article_enabled = False
    header_enabled = False
    header_level = 1
    pos = 0
    
    while pos < len(line):
        current_char = line[pos]
        if pos > 0:
            previous_char = line[pos - 1]
        else:
            previous_char = None

        if current_char == '*':
            if pos + 1 < len(line) and line[pos + 1] == '*':
                if bold_enabled is False:
                    bold_enabled = True
                    output += '<b>'
                    pos += 1
                else:
                    bold_enabled = False
                    output += '</b>'
                    pos += 1
            else:
                if italics_enabled is False and pos + 1 < len(line):
                    italics_enabled = True
                    output += '<i>'
                elif italics_enabled is True:
                    italics_enabled = False
                    output += '</i>'
        elif current_char == '#' and header_enabled is False:
            header_enabled = True
            if line[1] == '#':
                while line[pos+header_level] == '#':
                    header_level += 1

            output += '<h%d>' % header_level
            pos += header_level - 1

        elif current_char == '[':
            link_offset = 1
            article_name = ''
            while line[pos+link_offset] != ']':
                link_char = line[pos + link_offset]
                article_name += link_char
                link_offset += 1
            output += '<a href="%s">' % ('/cgi-bin/miki.py?page=' + article_name)
            output += article_name
            output += '</a>'
            pos += link_offset
        else:
            output += current_char

        pos += 1

    if header_enabled is True:
        output += '</h%d>' % header_level

    return output


def parse_markdown(data):
    
    lines = data.split('\n')
    paragraph_enabled = False
    list_enabled = False
    code_enabled = False
    output = '<p>'
    while lines:
        unparsed_line = lines.pop(0)
        if not unparsed_line.strip() and code_enabled is False:
            output += '</p><p>'
            continue
        if unparsed_line.startswith('    '):
            if code_enabled is False:
                code_enabled = True
                output += '<pre>'
                output += unparsed_line[4:] + '\n'
                continue
            else:
                output += unparsed_line[4:] + '\n'
                continue
        else:
            if code_enabled is True:
                output += '</pre>'
                code_enabled = False
        list_element_enabled = False
        if unparsed_line.startswith(' *'):
            if list_enabled is False:
                list_enabled = True
                output += '<ul>'
            list_element_enabled = True
            output += '<li>'
            unparsed_line = unparsed_line[2:]
        else:
            if list_enabled is True:
                output += '</ul>'
                list_enabled = False
        parsed_line = _parse_markdown_line(unparsed_line)
        output += parsed_line

        if list_element_enabled is True:
            output += '</li>'

        output += '\n'

    output += '</p>'
    return output


if __name__ == '__main__':
    serve()
