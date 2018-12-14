from setuptools import find_packages, setup


with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='hera-py',
    version='0.3.0',
    description=(
        'Interpreter for the Haverford Educational RISC Architecture (HERA) '
        'assembly language'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
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
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Topic :: Software Development :: Assemblers',
    ],
)
