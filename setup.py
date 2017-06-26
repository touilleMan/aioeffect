#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'effect',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='aioeffect',
    version='1.0.0',
    description="AsyncIO/Effect integration.",
    long_description=readme + '\n\n' + history,
    author="Emmanuel Leblond",
    author_email='emmanuel.leblond@gmail.com',
    url='https://github.com/touilleMan/aioeffect',
    packages=[
        'aioeffect',
    ],
    package_dir={'aioeffect':
                 'aioeffect'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='aioeffect',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='aioeffect',
    tests_require=test_requirements
)
