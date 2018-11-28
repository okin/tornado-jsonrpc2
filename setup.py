import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tornado-jsonrpc2",
    version="0.3",
    author="Niko Wenselowski",
    author_email="niko@nerdno.de",
    description="JSON-RPC request handler for Tornado.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="tornado jsonrpc jsonrpc2 rpc json requesthandler",
    url="https://github.com/okin/tornado-jsonrpc2",
    project_urls={
        "Source": "https://github.com/okin/tornado-jsonrpc2",
    },
    packages=setuptools.find_packages(exclude=["examples", "tests"]),
    python_requires='>=3.6',
    install_requires=['tornado>=5.0'],
    extras_require={
        'test': ['pytest-tornado'],
    },
    tests_require=['pytest-tornado'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
