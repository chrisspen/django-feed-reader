import os
import setuptools

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ''


def get_reqs(*fns):
    lst = []
    for fn in fns:
        with open(os.path.join(CURRENT_DIR, fn), encoding='utf-8') as fin:
            for package in fin.readlines():
                package = package.strip()
                if not package:
                    continue
                lst.append(package.strip())
    return lst


setuptools.setup(
    name='django-feed-reader',
    version='0.2.4',
    description='An RSS feed reading library for Django.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Chris Spencer',
    author_email='chrisspen@gmail.com',
    url='https://github.com/chrisspen/django-feed-reader',
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'feeds': [
            'testdata/*.*',
        ],
    },
    install_requires=get_reqs('requirements.txt'),
    tests_require=get_reqs('requirements-test.txt'),
    include_package_data=True,
    zip_safe=False,
)
