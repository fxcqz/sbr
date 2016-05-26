#!/usr/bin/env python
import argparse
from datetime import datetime
from docutils.core import publish_parts
import json
import os
from os import listdir
import re


GLOBALSFILE    = "globals.json"
OUTPUTDIR      = "output/"
POSTSDIR       = "_posts/"
SITEDIR        = "_site/"
PAGE_TYPES     = ('html', 'css')
EXCLUDED_FILES = ("base.html",)

def load_globals():
    with open(GLOBALSFILE, 'r') as handle:
        glob = handle.read()
    return json.loads(glob)


def sort_posts_cmp(post):
    try:
        return datetime.strptime(post.meta['time'], "%Y-%m-%d %H:%M")
    except KeyError:
        return 1


class MetaParser(object):

    def __init__(self, metadata):
        self.metadata = metadata.strip()
        self.whitespace = " \n\t"

    def parse(self):
        is_id = False
        is_val = False
        is_end = False
        is_escaped = False

        current_id = []
        current_val = []

        data = {}

        for char in self.metadata:
            if is_end:
                is_id = False
                is_val = False
                is_end = False
                is_escaped = False
                data[''.join(current_id)] = ''.join(current_val)
                current_id, current_val = [], []
                continue

            if not is_id and not current_id and char not in self.whitespace:
                is_id = True

            if is_id:
                if char in self.whitespace:
                    is_id = False
                    continue
                current_id.append(char)
            elif is_val:
                if char in self.whitespace and not is_val:
                    continue
                if char == '"' and not is_escaped:
                    is_val = False
                    is_end = True
                    continue
                if char == "\\":
                    is_escaped = True
                    continue
                current_val.append(char)

            if is_escaped:
                is_escaped = False

            if char == '=':
                is_id = False
            elif char == '"' and not is_escaped:
                if is_val:
                    is_end = True
                else:
                    is_val = True

        return data


class Post(object):

    def __init__(self, source_file):
        self.source_file = source_file
        self.meta = {}
        self.content = None

        self.parse_source()

    def parse_source(self):
        with open(POSTSDIR + self.source_file, 'r') as handle:
            post_data = handle.read()

        _, body = post_data.split('.meta')
        meta, content = body.split('.content')

        meta_parser = MetaParser(meta)
        self.meta = meta_parser.parse()
        self.content = publish_parts(content.strip(), writer_name="html")['html_body']

    def format_output(self, author="anonymous"):
        return ('<div class="post">\n'
                '  <div class="post-title">\n'
                '    <div class="righty">Posted by {} on {}</div>\n'
                '   <h2>{}</h2>\n'
                '  </div>\n'
                '  <div class="post-content">\n'
                '   {}\n'
                '  </div>\n'
                '</div>\n').format(author, self.meta['time'],
                                   self.meta['title'], self.content)

    def __repr__(self):
        return "Post {}".format(self.source_file)


class OutputFile(object):

    def __init__(self, source_file, posts, global_vals):
        self.source_file = source_file
        self.posts = posts
        self.global_vals = global_vals

    def sub_glob(self, match):
        return self.global_vals[match.group(1)][match.group(2)]

    def write(self):
        with open(self.source_file, 'r') as handle:
            page_data = handle.read()
        page_data = re.sub(r'{{\s*globals\.(.*)\.(.*?)\s*}}', self.sub_glob, page_data)
        if "{{ static }}" in page_data:
            page_data = re.sub(r'{{\s*static\s*}}\n?', '', page_data)
        elif '{{ posts }}' in page_data:
            # indexing
            page_data = re.sub(r'{{\s*posts\s*}}', '\n'.join(post.format_output(
                            author=self.global_vals['main']['author']
                        ) for post in self.posts), page_data)
        else:
            # post page
            pass
        out_file = OUTPUTDIR + self.source_file[self.source_file.find('/') + 1:]
        out_dir = os.path.dirname(out_file)
        if not os.path.exists(out_dir):
            print("creating dir: {}".format(out_dir))
            os.makedirs(out_dir)
        with open(out_file, 'w+') as handle:
            print("writing file: {}".format(out_file))
            handle.write(page_data)


def new_post(title, glob):
    filename = POSTSDIR + title.replace(' ', '_') + '.post'
    if os.path.isfile(filename):
        title_filename = title.replace(' ', '_')
        num_duplicates = sum(1 for f in listdir(POSTSDIR) if f.startswith(title_filename))
        filename = POSTSDIR + title_filename + '_{}'.format(num_duplicates + 1) + '.post'

    with open(filename, 'w+') as handle:
        handle.write(('.meta\n'
                      'title = "{}";\n'
                      'author = "{}";\n'
                      'time = "{}";\n\n'
                      '.content\n').format(
                        title,
                        glob['main']['author'],
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        ))

    print("Created new post file: {}".format(filename))


if __name__ == '__main__':
    print("loading globals")
    global_vals = load_globals()

    parser = argparse.ArgumentParser(prog="./personal.py", description="Generate a website")
    parser.add_argument('--new', '-n', dest="title", help='Create a new post with a given title')
    args = parser.parse_args()

    if args.title is not None:
        # create a new post
        new_post(args.title, global_vals)
        exit()

    print("loading and sorting posts")
    posts = [Post(file) for file in listdir(POSTSDIR)]
    posts = sorted(posts, key=sort_posts_cmp, reverse=True)

    for dirpath, dirs, files in os.walk(SITEDIR):
        for file in files:
            filename = os.path.join(dirpath, file)
            if not filename.endswith(PAGE_TYPES) or filename in EXCLUDED_FILES:
                continue
            page = OutputFile(filename, posts, global_vals)
            page.write()

    print("done")
