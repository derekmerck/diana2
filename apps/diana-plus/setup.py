import setuptools

with open("README.md") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    reqs = f.read().splitlines()

metadata = {
    'name': "diana-plus",
    'version': "2.1.0",
    'author': "Derek Merck",
    'author_email': "derek_merck@brown.edu",
}

setuptools.setup(
    name=metadata.get("name"),
    version=metadata.get("version"),
    author=metadata.get("author"),
    author_email=metadata.get("author_email"),
    description="Command line interface for DIANA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/derekmerck/diana2",
    pymodules="diana_plus",
    packages=setuptools.find_packages(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    license='MIT',
    install_requires=reqs,
    entry_points='''
        [console_scripts]
        diana-plus=diana_plus:cli
    ''',
)