"""Setup configuration for django-nexgensis-forms."""

from setuptools import setup, find_packages
import os

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='django-nexgensis-forms',
    version='1.0.0',
    description='A powerful Django app for creating and managing dynamic forms with versioning, hierarchical structures, and flexible field types',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Nexgensis',
    author_email='contact@nexgensis.com',
    url='https://github.com/nexgensis/django-nexgensis-forms',
    packages=find_packages(exclude=['tests', 'docs', 'examples']),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-django>=4.5',
            'pytest-cov>=4.0',
            'black>=23.0',
            'flake8>=6.0',
            'isort>=5.12',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    python_requires='>=3.10',
    license='MIT',
    keywords='django forms dynamic-forms form-builder workflow versioning',
    project_urls={
        'Documentation': 'https://github.com/nexgensis/django-nexgensis-forms/wiki',
        'Source': 'https://github.com/nexgensis/django-nexgensis-forms',
        'Tracker': 'https://github.com/nexgensis/django-nexgensis-forms/issues',
    },
)
