from setuptools import setup, find_packages

setup(
    name='mpwrapper',
    version='1.2.3',
    description='A simple wrapper written to make the use of Python multiprocessing easy to use',
    author='Shaun Lodder',
    author_email='shaun.lodder@gmail.com',
    url='https://github.com/lodder/python_mpwrapper',
    keywords=['multiprocessing'],
    classifiers=[
        "Programming Language :: Python"
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'setuptools',
        'numpy'
    ],
    extras_require={
        'develop': ['nose']
    }
)
