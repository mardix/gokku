"""
Koka

"""

from setuptools import setup, find_packages


__summary__ = "A package to deploy sites in virtualenv, run scripts, and deploy workers with supervisor"
__uri__ = "http://github.com/mardix/koka/"
setup(
    name="koka",
    version="0.0.1",
    license="MIT",
    author="Mardix",
    author_email="mcx2082@gmail.com",
    description="A package to deploy python application (Flask/Django), run workers and scripts using Pipenv and Supervisor",
    long_description=__doc__,
    url="http://github.com/mardix/koka/",
    download_url='http://github.com/mardix/koka/tarball/master',
    py_modules=['koka'],
    entry_points=dict(console_scripts=['koka=koka:main']),
    packages=find_packages(),
    install_requires=[
        'virtualenv',
        'uwsgi',
        'click',
    ],
    keywords=['deploy', 'koka', 'flask', 'gunicorn', 'django', 'workers', 'deploy sites', 'deployapp'],
    platforms='any',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe=False
)
