from django_pancake.flatten import flatten

TESTS = {
    # template_name: (template_source, pancake_source),
    'test1': ('Some text here', 'Some text here'),
    'test2': ('{% unknown_block_tag %}Text here', '{% unknown_block_tag %}Text here'),

    'base1': ('<html><title>{% block title %}</title></html>', '<html><title></title></html>'),
    'child1': ('{% extends "base1" %} {% block title %}It worked{% endblock %}', '<html><title>It worked</title></html>'),
}
templates = dict((k, v[0]) for k, v in TESTS.items())

def test_flatten():
    for template_name, (template_source, pancake_source) in TESTS.items():
        yield check_flatten, template_source, pancake_source

def check_flatten(source, expected):
    result = flatten(source, templates)
    assert result == expected, 'expected %r, got %r' % (expected, result)
