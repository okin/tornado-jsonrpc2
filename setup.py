import setuptools

setuptools.setup(
    name="tornado-jsonrpc2",
    version="0.1.dev",
    author="Niko Wenselowski",
    author_email="niko@nerdno.de",
    description="A handler for JSON-RPC for Tornado.",
    keywords="tornado jsonrpc jsonrpc2 rpc json",
    url="https://github.com/okin/tornado-jsonrpc2",
    project_urls={
        "Source Code": "https://github.com/okin/tornado-jsonrpc2",
    },
    packages=setuptools.find_packages(exclude=["examples", "tests"]),
    python_requires='>=3.6',
    install_requires=['tornado>=5.0'],
    tests_require=['pytest-tornado'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
