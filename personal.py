#!/usr/bin/env python
import argparse
from datetime import datetime
from docutils.core import publish_parts
from functools import partial
import json
import os
from os import listdir
import re
import shutil


GLOBALSFILE    = "globals.json"
PAGE_TYPES     = ('html', 'css')
EXCLUDED_FILES = ("base.html",)
COPY_ONLY      = ('js', 'svg')

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
        self.html_file = ""

        self.parse_source()

    def parse_source(self):
        with open(POSTSDIR + self.source_file, 'r') as handle:
            post_data = handle.read()

        _, body = post_data.split('.meta')
        meta, content = body.split('.content')

        meta_parser = MetaParser(meta)
        self.meta = meta_parser.parse()
        self.content = publish_parts(content.strip(), writer_name="html")['html_body']

    def format_output(self, author="anonymous", no_header_link=False):
        if no_header_link or not self.html_file:
            header = self.meta['title']
        else:
            header = '<a href="{}">{}</a>'.format(self.html_file, self.meta['title'])
        return ('<div class="post">\n'
                '  <div class="post-title">\n'
                '    <span class="pull-right">Posted by {} on {}</span>\n'
                '    <h4>{}</h4>\n'
                '  </div>\n'
                '  <div class="post-content">\n'
                '    {}\n'
                '  </div>\n'
                '</div>\n'
                '<hr />\n').format(author, self.meta['time'], header, self.content)

    @staticmethod
    def create_static_pages(posts, global_vals):
        base_filename = global_vals['processing'].get('post_base', '_site/base.html')
        with open(base_filename, 'r') as handle:
            page_data = handle.read()
        page_data = re.sub(
            r'{{\s*globals\.(.*)\.(.*?)\s*}}',
            lambda m: global_vals[m.group(1)][m.group(2)],
            page_data
        )

        def _sub_post_data(post, match):
            value = match.group(1)
            if value.startswith('meta'):
                key = value.split('.')[-1]
                return post.meta.get(key)
            else:
                return post.__dict__.get(value)

        for post in posts:
            new_page = page_data
            new_page = re.sub( r'{{\s*post\.(.*?)\s*}}', partial(_sub_post_data, post), new_page)

            output_file = global_vals['fs']['outputdir'] + post.source_file[:-5] + '.html'
            with open(output_file, 'w+') as handle:
                print("writing page for: {}".format(output_file))
                handle.write(new_page)
                post.html_file = output_file.split('/')[-1]

    def __repr__(self):
        return "Post {}".format(self.source_file)


class OutputFile(object):

    def __init__(self, source_file, posts, global_vals):
        self.source_file = source_file
        self.posts = posts
        self.global_vals = global_vals

    def write(self):
        with open(self.source_file, 'r') as handle:
            page_data = handle.read()
        page_data = re.sub(
            r'{{\s*globals\.(.*)\.(.*?)\s*}}',
            lambda m: self.global_vals[m.group(1)][m.group(2)],
            page_data
        )
        if "{{ static }}" in page_data:
            page_data = re.sub(r'{{\s*static\s*}}\n?', '', page_data)
            print("skipping non globals processing: file is static")
        elif '{{ posts }}' in page_data:
            # indexing
            page_data = re.sub(r'{{\s*posts\s*}}', '\n'.join(post.format_output(
                            author=self.global_vals['main']['author']
                        ) for post in self.posts), page_data)
        else:
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


def make_missing_dirs(*dirs):
    for directory in dirs:
        if not os.path.exists(directory):
            print("Missing directory {}... Creating it.".format(directory))
            os.makedirs(directory)


if __name__ == '__main__':
    print("loading globals")
    global_vals = load_globals()

    OUTPUTDIR = global_vals['fs'].get('outputdir', 'output/')
    POSTSDIR = global_vals['fs'].get('postsdir', '_posts/')
    SITEDIR = global_vals['fs'].get('sitedir', '_site/')

    make_missing_dirs(OUTPUTDIR, POSTSDIR, SITEDIR)

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

    Post.create_static_pages(posts, global_vals)

    for dirpath, dirs, files in os.walk(SITEDIR):
        for file in files:
            filename = os.path.join(dirpath, file)
            if filename.endswith(COPY_ONLY):
                # copy files across
                out_file = OUTPUTDIR + filename[filename.find('/') + 1:]
                out_dir = os.path.dirname(out_file)
                if not os.path.exists(out_dir):
                    print("creating dir: {}".format(out_dir))
                    os.makedirs(out_dir)
                print("copying file: {} to {}".format(filename, out_file))
                shutil.copyfile(filename, out_file)
                continue
            elif not filename.endswith(PAGE_TYPES) or filename.endswith(EXCLUDED_FILES):
                continue
            page = OutputFile(filename, posts, global_vals)
            page.write()

    print("done")
