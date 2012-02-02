==============
django-pancake
==============

By Adrian Holovaty <adrian@holovaty.com>

Library for "flattening" Django templates.

Run "make_pancakes.py" with an output directory name, and it will fill that
directory with a "flat" version of each template -- a pancake. A pancake is a
template in which:

* Template inheritance is fully expanded. {% extends %} and {% block %} tags
  are gone, and the parent templates are fully folded in.

* {% include %} tags are gone, with their contents fully folded in.

* Template comments are removed: {% comment %} syntax and {# short syntax #}.

Pancakes behave exactly the same as the original templates. But they render
more quickly, because they avoid the overhead of template inheritance and
template includes at rendering time.

Think of it as "denormalizing" your templates, as a database administrator
might denormalize SQL tables for performance. You give up the DRY principle
but make up for it in faster application speed.

Obviously, pancakes are very redundant -- each of them includes all of the
markup from the base template(s), etc. You shouldn't check pancakes into
revision control or hand-edit them. They're purely for performance and should
be handled as any automatically generated code.

Pros and cons
=============

Pros:

* Makes run-time template rendering faster. In some cases, the rendering is
  significantly faster. See "How fast is the speed improvement?" below.

* Not a huge commitment. Give it a shot and see whether it makes things faster
  for you.

Cons:

* Makes your deployment more complex, as you now have to manage generated
  templates and run django-pancake to generate them whenever you deploy.

* May require you to change the way you write templates, specifically by
  removing dynamic {% include %} and {% extends %} tags. See "Limitations"
  below.

* (Philosophical.) Django really should do this in memory rather than compiling
  to templates on the filesystem. See "Related projects" below.

How fast is the speed improvement?
==================================

It depends on what you're doing in templates.

If you're just using basic template inheritance and includes, you should expect
a tiny/negligible performance improvement -- on the order of 10 milliseconds
for a single template render. In this case, it may not be worth the added
complexity it introduces to your deployment environment.

But if you're doing crazy things -- say, having a template with a template tag
that loads other templates, within a loop, with each subtemplate being in an
inheritance structure three levels deep -- then you might see a significant
benefit that makes it worth the complexity.

At EveryBlock, we found it sped a certain type of page up by 200 milliseconds,
which is pretty great.

Usage
=====

1. Generate the pancakes. Pass it the directory that contains your source
   templates and the directory you want pancakes to be generated in.

    python test_pancake.py /path/to/source/directory /path/to/pancake/directory

2. Point Django at the pancake directory:

    TEMPLATE_DIRS = [
        '/path/to/pancake/directory',
    ]

3. Enjoy faster template performance.

Limitations
===========

If you want django-pancake to work with your templates, make sure your
templates do the following:

* Avoid using block.super in anything but a standalone variable. This is OK:

      {{ block.super }}

  But these statements are not:

      {% if block.super %}
      {{ block.super|lower }}
      {% some_other_tag block.super %}

  If you use block.super in one of these prohibited ways, django-pancake will
  not detect it and will generate your templates as if everything is OK. But
  you'll likely get odd behavior when the template is rendered. The problem is
  that "block" is no longer a variable in the pancakes, so it'll be evaluated
  as False.

* Avoid dynamic {% extends %} tags -- that is, when the parent template name is
  a variable. Example: {% extends my_template_name %} (note the lack of quotes
  around my_template_name). If you do this, django-pancake will raise a
  PancakeFail exception.

* Likewise, avoid dynamic {% include %} tags. Example:
  {% include some_include %}. If you do this, django-pancake will raise a
  PancakeFail exception.

* Don't use the "only" keyword in {% include %} tags. If you do, django-pancake
  won't raise an exception, but it'll merely output the same {% include %} tag,
  so you don't get the benefit of flattening.

Related projects
================

Ideally, django-pancake wouldn't exist, and Django would do this "flattening"
itself, along with providing a more robust template compilation step. That's a
significantly harder problem, and we're working on it. The goal is for
django-pancake not to have to exist.

But, in the meantime, here are some related projects that have gone down that
road:

* templatetk
  https://github.com/mitsuhiko/templatetk/

* django-template-preprocessor
  https://github.com/citylive/django-template-preprocessor/
