from django_pancake.flatten import flatten

TESTS = {
    # template_name: (template_source, pancake_source),
    'test1': ('Some text here', 'Some text here'),
    'test2': ('{% unknown_block_tag %}Text here', '{% unknown_block_tag %}Text here'),

    'base1': ('<html><title>{% block title %}{% endblock %}</title></html>', '<html><title></title></html>'),
    'child1': ('{% extends "base1" %} {% block title %}It worked{% endblock %}', '<html><title>It worked</title></html>'),

    # {% load %} statements get bubbled up and combined.
    'loadbase1': ('{% load webdesign %}<html><title>{% block title %}</title></html>', '{% load webdesign %}<html><title></title></html>'),
    'load1': ('{% extends "base1" %}{% load humanize %}{% block title %}Load 1{% endblock %}', '{% load humanize %}<html><title>It worked</title></html>'),
    'load2': ('{% extends "loadbase1" %}{% load humanize %}{% block title %}Load 2{% endblock %}', '{% load humanize webdesign %}<html><title>Load 2</title></html>'),
}
TEMPLATES = dict((k, v[0]) for k, v in TESTS.items())

def test_flatten():
    for template_name, (template_source, pancake_source) in TESTS.items():
        yield check_flatten, template_name, pancake_source

def check_flatten(template_name, expected):
    result = flatten(template_name, TEMPLATES)
    assert result == expected, 'expected %r, got %r' % (expected, result)
