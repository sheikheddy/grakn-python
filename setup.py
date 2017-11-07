from distutils.core import setup

setup(
    name='grakn',
    packages=['grakn'],
    version='0.7',
    description='A Python client for Grakn',
    long_description=open('README.rst').read(),
    author='Grakn Labs',
    author_email='community@grakn.ai',
    url='https://github.com/graknlabs/grakn-python',
    download_url='https://github.com/graknlabs/grakn-python/archive/v0.7.tar.gz',
    keywords=['grakn', 'database', 'graph'],
    classifiers=[
        'Development Status :: 5 - Production/Stable'
    ],
    install_requires=['requests']
)
