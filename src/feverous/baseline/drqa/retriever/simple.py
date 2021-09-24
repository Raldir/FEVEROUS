class Simple(object):
    def __init__(self, lines):
        self.lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def path(self):
        return None

    def get_doc_ids(self):
        return list(range(len(self.lines)))

    def get_doc_text(self, line):
        return self.lines[line]

    def close(self):
        pass
