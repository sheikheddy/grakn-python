from distutils.core import setup

setup(
    name='grakn',
    packages=['grakn'],
    version='0.1',
    description='Python driver for Grakn',
    long_description=open('README.rst').read(),
    author='Grakn Labs',
    author_email='<whatshouldgoherewhoknows>@grakn.ai',
    url='https://github.com/graknlabs/grakn-python',
    download_url='https://github.com/graknlabs/grakn-python/archive/0.1.tar.gz',
    keywords=['<we should also add some keywords>'],
    classifiers=[],
    install_requires=['requests']
)
