import os
from setuptools import find_packages, setup


dpath = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dpath, "README.md"), "r") as f:
    long_description = f.read()


setup(
    name="hera-py",
    version="0.8.0",
    description=(
        "Interpreter for the Haverford Educational RISC Architecture (HERA) "
        "assembly language"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    author="Ian Fisher",
    author_email="iafisher@protonmail.com",
    entry_points={"console_scripts": ["hera = hera.main:external_main"]},
    install_requires=["typing==3.6.6"],  # typing module is necessary for Python 3.4
    packages=find_packages(exclude=["tests"]),
    project_urls={"Source": "https://github.com/iafisher/hera-py"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Topic :: Software Development :: Assemblers",
    ],
)
