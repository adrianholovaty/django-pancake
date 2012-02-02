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

    def sub_text(self):
        for leaf in self.leaves:
            if isinstance(leaf, ASTNode):
                for subleaf in leaf.sub_text():
                    yield subleaf
            else:
                yield leaf

    def sub_nodes(self):
        for leaf in self.leaves:
            if isinstance(leaf, ASTNode):
                yield leaf
                for subleaf in leaf.sub_nodes():
                    yield subleaf

class Template(ASTNode):
    "Root node of the AST. Represents a template, which may or may not have a parent."
    def __init__(self, name):
        super(Template, self).__init__(name)
        self.parent = None # Template object for the parent template, if there's a parent.
        self.blocks = {} # Maps block names to objects in self.leaves for quick lookup.
        self.loads = set() # Template libraries to load.

class Block(ASTNode):
    "Represents a {% block %}."
    pass

class TemplateDirectory(object):
    "Dictionary-like object that maps template names to template strings."
    def __init__(self, directory):
        self.directory = directory

    def __getitem__(self, template_name):
        filename = os.path.join(self.directory, template_name)
        return open(filename).read()

class Parser(object):
    def __init__(self, fail_gracefully=True):
        self.fail_gracefully = fail_gracefully

    def parse(self, template_name, templates):
        """
        Creates an AST for the given template. Returns a Template object.
        """
        self.templates = templates # Maps template names to template sources.
        self.root = Template(template_name)
        self.stack = [self.root]
        self.current = self.root
        self.tokens = Lexer(self.templates[template_name], 'django-pancake').tokenize()
        while self.tokens:
            token = self.next_token()

            if token.token_type == 0: # TOKEN_TEXT
                self.current.leaves.append(token.contents)

            elif token.token_type == 1: # TOKEN_VAR
                if token.contents == 'block.super':
                    if self.root.parent is None:
                        raise ValueError('Got {{ block.super }} in a template that has no parent')

                    super_block_name = self.stack[-1].name
                    current_par = self.root.parent
                    while current_par is not None:
                        if super_block_name in current_par.blocks:
                            self.current.leaves.extend(current_par.blocks[super_block_name].leaves)
                            break
                        current_par = current_par.parent
                else:
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
            raise ValueError('{%% extends %%} without an argument (file: %r)' % self.root.name)
        if text[0] in ('"', "'"):
            parent_name = text[1:-1]
            self.root.parent = Parser().parse(parent_name, self.templates)
        else:
            raise ValueError('Variable {%% extends %%} tags are not supported (file: %r)' % self.root.name)

    def do_load(self, text):
        # Keep track of which template libraries have been loaded,
        # so that we can pass them up to the root.
        self.root.loads.update(text.split())

    def do_include(self, text):
        if ' only' in text:
            if self.fail_gracefully:
                self.current.leaves.append('{%% include %s %%}' % text)
                return
            else:
                raise ValueError('{%% include %%} tags containing "only" are not supported (file: %r)' % self.root.name)
        try:
            template_name, rest = text.split(None, 1)
        except ValueError:
            template_name, rest = text, ''
        if not template_name[0] in ('"', "'"):
            if self.fail_gracefully:
                self.current.leaves.append('{%% include %s %%}' % text)
                return
            else:
                raise ValueError('Variable {%% include %%} tags are not supported (file: %r)' % self.root.name)
        template_name = template_name[1:-1]
        if rest.startswith('with '):
            rest = rest[5:]

        if rest:
            self.current.leaves.append('{%% with %s %%}' % rest)
        self.current.leaves.extend(Parser().parse(template_name, self.templates).leaves)
        if rest:
            self.current.leaves.append('{% endwith %}')

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
    master = family[0]
    for child in family[1:]:
        for block in child.sub_nodes():
            if block.name in master.blocks:
                master.blocks[block.name].leaves = block.leaves
            else:
                # This is a new block that wasn't defined in the parent.
                # Put it in master.blocks so that its children can access it.
                master.blocks[block.name] = block
        master.loads.update(child.loads)

    result = list(master.sub_text())

    # Add the {% load %} statements from all children.
    # Put them in alphabetical order to be consistent.
    if master.loads:
        loads = sorted(master.loads)
        result.insert(0, '{%% load %s %%}' % ' '.join(loads))

    return ''.join(result)

def flatten(source, templates):
    p = Parser()
    template = p.parse(source, templates)
    return flatten_parsed_template(template)

if __name__ == "__main__":
    # from django_pancake.flatten import flatten
    print flatten('newsitem_list/neighbor-events.html', TemplateDirectory('/Users/adrian/code/everyblock/everyblock/everyblock/templates/site'))
