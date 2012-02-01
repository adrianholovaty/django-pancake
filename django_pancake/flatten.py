from django.template.base import Lexer
import os
import re

class ASTNode(object):
    "A node in the AST."
    def __init__(self, name):
        self.name = name
        self.leaves = [] # Each leaf can be a string or another ASTNode.

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def sub_nodes(self):
        for child in self.leaves:
            if isinstance(child, ASTNode):
                yield child
                for subnode in child.sub_nodes():
                    yield subnode

class Template(ASTNode):
    "Root node of the AST. Represents a template, which may or may not have a parent."
    def __init__(self, name):
        super(Template, self).__init__(name)
        self.parent = None # Template object for the parent template, if there's a parent.
        self.blocks = {} # Maps block names to objects in self.leaves for quick lookup.

class Block(ASTNode):
    "Represents a {% block %}."
    pass

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
        Creates an AST for the given template. Returns a Template object.
        """
        self.templates = templates # Maps template names to template sources.
        self.root = Template(template_name)
        self.stack = [self.root]
        self.current = self.root
        self.tokens = Lexer(templates[template_name], 'django-pancake').tokenize()
        while self.tokens:
            token = self.next_token()

            if token.token_type == 0: # TOKEN_TEXT
                self.current.leaves.append(token.contents)

            elif token.token_type == 1: # TOKEN_VAR
                self.current.leaves.append('{{ %s }}' % token.contents)

            elif token.token_type == 2: # TOKEN_BLOCK
                try:
                    tag_name, arg = token.contents.split(None, 1)
                except ValueError:
                    tag_name, arg = token.contents.strip(), None
                method_name = 'do_%s' % tag_name
                if hasattr(self, method_name):
                    getattr(self, method_name)(arg)
                else:
                    self.current.leaves.append('{%% %s %%}' % token.contents)

        return self.root

    def next_token(self):
        return self.tokens.pop(0)

    def do_block(self, text):
        if not text:
            raise ValueError('{% block %} without a name')
        self.current.leaves.append(Block(text))
        self.root.blocks[text] = self.current = self.current.leaves[-1]
        self.stack.append(self.current)

    def do_endblock(self, text):
        self.stack.pop()
        self.current = self.stack[-1]

    def do_extends(self, text):
        if not text:
            raise ValueError('{% extends %} without an argument')
        if text[0] in ('"', "'"):
            parent_name = text[1:-1]
            self.root.parent = Parser().parse(parent_name, self.templates)
        else:
            raise ValueError('Variable {% extends %} tags not supported')

def flatten_parsed_template(template):
    "Given an AST as returned by the parser, returns a string of flattened template text."
    # First, make a list from the template inheritance structure -- the family.
    # This will be in order from broad to specific.
    family = []
    while 1:
        family.insert(0, template)
        if template.parent is None:
            break
        template = template.parent

    # Now, starting with the base template, loop downward over the child
    # templates (getting more specific). For each child template, fill in the
    # blocks in the parent template.
    result = family[0]
    for child in family[1:]:
        for block in child.sub_nodes():
            if block.name in result.blocks:
                result.blocks[block.name].leaves = block.leaves
    return result

def flatten(source, templates):
    f = Flattener()
    result = f.flatten(source, templates)
    return result

if __name__ == "__main__":
    from django_pancake.flatten import Parser, TemplateDirectory, flatten_parsed_template
    p = Parser()
    tp = p.parse('newsitem_list/neighbor-events.html', TemplateDirectory('/Users/adrian/code/everyblock/everyblock/everyblock/templates/site'))
    result = flatten_parsed_template(tp)
