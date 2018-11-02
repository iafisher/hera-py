from setuptools import find_packages, setup


setup(
    name='hera-py',
    version='0.1.0',
    description=(
        'Interpreter for the Haverford Educational RISC Architecture (HERA) '
        'assembly language'
    ),
    license='MIT',
    author='Ian Fisher',
    author_email='iafisher@protonmail.com',
    entry_points={
        'console_scripts': [
            'hera = hera.main:main',
        ],
    },
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'docopt==0.6.2',
        'lark-parser==0.6.5',
    ],
    project_urls={
        'Source': 'https://github.com/iafisher/hera-py',
    }
)
