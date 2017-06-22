from distutils.core import setup

setup(
    name='grakn',
    packages=['grakn'],
    version='0.2',
    description='A Python client for Grakn',
    long_description=open('README.rst').read(),
    author='Grakn Labs',
    author_email='admin@grakn.ai',
    url='https://github.com/graknlabs/grakn-python',
    download_url='https://github.com/graknlabs/grakn-python/archive/v0.2.tar.gz',
    keywords=['grakn', 'database', 'graph'],
    classifiers=[],
    install_requires=['requests']
)
