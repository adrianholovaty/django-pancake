from distutils.core import setup

setup(
    name='django-pancake',
    version='0.1',
    description='Library for "flattening" Django templates.',
    author='Adrian Holovaty',
    author_email='adrian@holovaty.com',
    url='https://github.com/adrianholovaty/django-pancake',
    license='MIT',
    classifiers = [
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=['django_pancake'],
)
