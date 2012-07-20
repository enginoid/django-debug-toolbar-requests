from setuptools import setup

setup(
    name='django-debug-toolbar-requests',
    version='0.0.1',
    description=('A django-debug-toolbar panel for HTTP requests made with '
        'the `requests` library.'),
    long_description=open('README.rst').read(),
    author='Fred Jonsson',
    author_email='fridrik@pyth.net',
    url='https://github.com/enginous/django-debug-toolbar-requests',
    license='BSD',
    packages=['debug_toolbar_requests'],
    package_data={'debug_toolbar_requests': ['templates/*.html']},
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)