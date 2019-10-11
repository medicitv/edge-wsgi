import re

from setuptools import setup


def get_version(filename):
    with open(filename, "r") as fp:
        contents = fp.read()
    return re.search(r"__version__ = ['\"]([^'\"]+)['\"]", contents).group(1)


version = get_version("edge_wsgi.py")


with open("README.rst", "r") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst", "r") as history_file:
    history = history_file.read()


setup(
    name="edge-wsgi",
    version=version,
    description=(
        "Wrap a WSGI application in an AWS Lambda@edge handler function for "
        + "running on Cloudfront."
    ),
    long_description=readme + "\n\n" + history,
    author="Antoine Monnet",
    author_email="amonnet@medici.tv",
    url="https://github.com/AntoineMonnet/edge-wsgi",
    project_urls={
        "Changelog": "https://github.com/AntoineMonnet/edge-wsgi/blob/master/HISTORY.rst"
    },
    py_modules=["edge_wsgi"],
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.5",
    license="ISC License",
    zip_safe=False,
    keywords="AWS, Lambda, Cloudfront, edge",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
