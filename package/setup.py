import setuptools, re

with open("README.md") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    reqs = f.read().splitlines()

with open("plus_requirements.txt") as f:
    plus_reqs = f.read().splitlines()

with open("diana/__init__.py") as f:
    content = f.read()
    match = re.findall(r"__([a-z0-9_]+)__\s*=\s*\"([^\"]+)\"", content)
    print(match)
    metadata = dict(match)

setuptools.setup(
    name=metadata.get("name"),
    version=metadata.get("version"),
    author=metadata.get("author"),
    author_email=metadata.get("author_email"),
    description="DICOM analysis and archive (DIANA)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/derekmerck/diana2",
    packages=setuptools.find_packages(),
    package_data={'python-diana': ['utils/guid/us_census/*.txt']},
    classifiers=(
        'Development Status :: 3 - Alpha',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    license='MIT',
    install_requires=reqs,
    extras_require={
        'plus': plus_reqs
    },

    entry_points='''
        [console_scripts]
        diana-cli=diana.cli.cli:main
    '''
)