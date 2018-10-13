import setuptools

setuptools.setup(
    name="tornado-jsonrpc2",
    version="0.1.dev",
    author="Niko Wenselowski",
    author_email="niko@nerdno.de",
    description="A handler for JSON-RPC for Tornado.",
    url="https://github.com/okin/tornado-jsonrpc2",
    packages=setuptools.find_packages(),
    install_requires=['tornado>=5.0'],
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
