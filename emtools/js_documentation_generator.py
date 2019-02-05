# Copyright 2019 J Kyle Medley

import re
from jinja2 import Template, Environment, DictLoader

jinja_env = Environment(loader=DictLoader(dict(
    class_wrapper=\
'''{{ docstring }}
export class {{ symbol }} {}
''',
    module=\
'''{{ module_docstring }}
{% for class in classes %}
{{ class }}
{% endfor %}
''',
)))
jinja_env.trim_blocks = True
jinja_env.lstrip_blocks = True

class Interface:

    def __init__(self, symbol, docstring_lines):
        self.symbol = symbol
        self.docstring_lines = docstring_lines


    def render(self):
        return jinja_env.get_template('class_wrapper').render(
            docstring = '\n'.join(self.docstring_lines),
            symbol = self.symbol,
        )

class JSDocumentationGenerator:

    def __init__(self):
        self.module_docstring_lines = tuple()
        self.interfaces = []
        self.space_re           = re.compile(r'^[\s]*$')
        self.prefix_re          = re.compile(r'^[\s]*\[Prefix="[^"]+"\][\s]*$')
        self.docstring_start    = re.compile(r'^[\s]*/\*\*.*$')
        self.docstring_continue = re.compile(r'^[\s]*\*.*$')
        self.docstring_stop     = re.compile(r'^[\s]*\*/[\s]*$')


    def collect_docstring_lines_reversed(self,l,lines):
        if l < 0:
            return
        while True:
            l -= 1
            line = lines[l]
            if l < 0:
                return
            space = self.space_re.match(line)
            if space is not None:
                continue
            # print('test prefix against',line)
            prefix = self.prefix_re.match(line)
            if prefix is not None:
                # print('match prefix for',line)
                continue
            if self.docstring_stop.match(lines[l]) is not None:
                # print('stop matched for',line)
                yield line
                break
            else:
                return
        while True:
            l -= 1
            line = lines[l]
            if l < 0:
                return
            cont = self.docstring_continue.match(line)
            start = self.docstring_start.match(line)
            if cont is not None or start is not None:
                yield line
            else:
                return


    def parseInterfaceAtLoc(self, interface, lineno, input):
        '''
        Parses the documentation string preceding the interface
        at the given line number.
        '''
        lines = input.splitlines()
        def collect_docstring_lines(l):
            return reversed(tuple(self.collect_docstring_lines_reversed(l,lines)))

        docstring_lines = tuple(collect_docstring_lines(lineno-1))
        # print('lines for',interface)
        # print('\n'.join(docstring_lines))
        self.interfaces.append(Interface(interface, docstring_lines))


    def parseModuleHeader(self, input):
        '''
        Parses the documentation for the module itself.
        '''
        lines = input.splitlines()

        def collect_module_docstring_lines(l):
            while True:
                line = lines[l]
                if self.docstring_start.match(line) is not None:
                    yield line
                    while True:
                        l += 1
                        line = lines[l]
                        if self.docstring_stop.match(lines[l]) is not None:
                            yield line
                            return
                        elif self.docstring_continue.match(line) is not None:
                            yield line
                        else:
                            raise RuntimeError('Unrecognized module docstring')
                else:
                    return

        self.module_docstring_lines = tuple(collect_module_docstring_lines(0))


    def render(self):
        return jinja_env.get_template('module').render(
            module_docstring = '\n'.join(self.module_docstring_lines),
            classes = tuple(i.render() for i in self.interfaces),
        )
