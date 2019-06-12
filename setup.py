import setuptools

with open("README.md", "r") as fd:
    long_description = fd.read()

with open("VERSION", "r") as fd:
    version = fd.read().strip()

setuptools.setup(
    name="regexp",
    version=version,
    author="Julien Castiaux",
    author_email="julien.castiaux@gmail.com",
    description="Finite automatons and grep-like tools.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Julien00859/regexp",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
    ],
)