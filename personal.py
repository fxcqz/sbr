from datetime import datetime
import json
from os import listdir
import re


GLOBALSFILE = "globals.json"
OUTPUTDIR   = "output/"
POSTSDIR    = "_posts/"
SITEDIR     = "_site/"

def load_globals():
    with open(GLOBALSFILE, 'r') as handle:
        glob = handle.read()
    return json.loads(glob)


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
        self.content = content.strip()

    def __repr__(self):
        return "Post {}".format(self.source_file)


class OutputFile(object):

    def __init__(self, source_file, global_vals):
        self.source_file = source_file
        self.global_vals = global_vals

    def sub_glob(self, match):
        return self.global_vals[match.group(1)][match.group(2)]

    def write(self):
        with open(SITEDIR + self.source_file, 'r') as handle:
            page_data = handle.read()
        page_data = re.sub(r'{{ globals\.(.*)\.(.*) }}', self.sub_glob, page_data)
        print(page_data)


if __name__ == '__main__':
    global_vals = load_globals()
    posts = [Post(file) for file in listdir(POSTSDIR)]
    posts = sorted(posts, key=lambda p: datetime.strptime(p.meta['time'], "%Y-%m-%d %H:%M"))
    pages = [OutputFile(file, global_vals) for file in listdir(SITEDIR)]
    for page in pages:
        page.write()
