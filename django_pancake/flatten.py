from django.template.base import Lexer
import os
import re

class ParsedTemplate(object):
    def __init__(self, name):
        self.name = name
        self.parent = None # A ParsedTemplate object, or None if there's no parent.
        self.blocks = {}
        self.content = []

    def __repr__(self):
        return '<ParsedTemplate: %r>' % self.name

class TemplateDirectory(object):
    "Dictionary-like object that maps template names to template strings."
    def __init__(self, directory):
        self.directory = directory

    def __getitem__(self, template_name, default=None):
        filename = os.path.join(self.directory, template_name)
        return open(filename).read()

class Parser(object):
    def parse(self, template_name, templates):
        """
        Returns a ParsedTemplate object, handling template inheritance.
        """
        self.templates = templates # Maps template names to template sources.
        self.result = ParsedTemplate(template_name)
        self.current_block_name = None
        self.current_block = []

        self.tokens = Lexer(templates[template_name], 'django-pancake').tokenize()
        while self.tokens:
            token = self.next_token()

            if token.token_type == 0: # TOKEN_TEXT
                self.current_block.append(token.contents)

            elif token.token_type == 1: # TOKEN_VAR
                self.current_block.append('{{ %s }}' % token.contents)

            elif token.token_type == 2: # TOKEN_BLOCK
                try:
                    tag_name, arg = token.contents.split(None, 1)
                except ValueError:
                    tag_name, arg = token.contents.strip(), None
                method_name = 'do_%s' % tag_name
                if hasattr(self, method_name):
                    getattr(self, method_name)(arg)
                else:
                    self.current_block.append('{%% %s %%}' % token.contents)

        if self.current_block:
            self.result.content = self.current_block
        return self.result

    def next_token(self):
        return self.tokens.pop(0)

    def do_block(self, text):
        if not text:
            raise ValueError('{% block %} without a name')
        self.current_block_name = text

    def do_endblock(self, text):
        self.result.blocks[self.current_block_name] = self.current_block
        self.current_block_name = None
        self.current_block = []

    def do_extends(self, text):
        if not text:
            raise ValueError('{% extends %} without an argument')
        if text[0] in ('"', "'"):
            parent_name = text[1:-1]
            self.result.parent = Parser().parse(parent_name, self.templates)
        else:
            raise ValueError('Variable {% extends %} tags not supported')

def flatten_parsed_template(template):
    "Given a ParsedTemplate object, returns a string of flattened template text."
    # First, make a list from the template inheritance structure -- the family.
    # This will be in order from broad to specific.
    family = []
    while 1:
        family.insert(0, template)
        if template.parent is None:
            break
        template = template.parent

    print family

    # result = family[0]
    # for name, value in result.blocks.items():
    #     for other in family[1:]:
    #         if name in family.blocks:
    #             value = family.blocks[name]

def flatten(source, templates):
    f = Flattener()
    result = f.flatten(source, templates)
    return result

if __name__ == "__main__":
    #from django_pancake.flatten import Parser, TemplateDirectory
    p = Parser()
    tp = p.parse('newsitem_list/neighbor-events.html', TemplateDirectory('/Users/adrian/code/everyblock/everyblock/everyblock/templates/site'))
    flatten_parsed_template(tp)
