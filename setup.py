from distutils.core import setup

setup(
    name='Python Multiprocessing Wrapper',
    packages=['mpwrapper'],
    version='1.0.0',
    description='A simple wrapper written to make the use of Python multiprocessing easy to use',
    long_description=open("README.md").read(),
    author='Shaun Lodder',
    author_email='shaun.lodder@gmail.com',
    url='https://github.com/lodder/python_mpwrapper',
    download_url='download link you saved',
    keywords=['multiprocessing'],
    classifiers=[],
    install_requires=[
        'numpy'
    ],
    extras_require={
        'develop': ['nose']
    }
)
