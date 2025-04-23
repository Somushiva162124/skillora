from setuptools import setup, Extension

# Read README with UTF-8 encoding
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sentencepiece',
    version='0.1',
    packages=['sentencepiece'],
    long_description=long_description,  # Use the correctly read content
    long_description_content_type='text/markdown',
    install_requires=[
        # any other dependencies
    ],
    python_requires='>=3.6',
    # other setup parameters
)
