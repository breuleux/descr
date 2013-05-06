from setuptools import setup

setup(
    name = 'descr',
    version = '0.1',
    packages = ['descr', 'descr.html'],
    
    # Metadata
    author = 'Olivier Breuleux',
    author_email = 'olivier@breuleux.net',
    url = 'https://github.com/breuleux/descr',
    download_url = 'https://github.com/downloads/breuleux/descr/descr.tar.gz',
    license = 'BSD',

    description = 'HTML pretty-printing of Python structures',
    long_description = (
        'Generates HTML for Python data, lists, dictionaries'
        ' and tracebacks. Meant to be used primarily interactively'
        ' with the IPython notebook. CSS selectors can be used'
        ' to customize display or highlight data of interest.'),

    keywords = 'print pretty-print',
    classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
          'Topic :: Utilities',
    ],

    requires = ['cssselect']
)
