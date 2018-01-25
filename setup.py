from distutils.core import setup
setup(
    name='steem',
    version='0.18.103',
    description='Official Python Steem Library',
    # long_description = file: README.rst
    keywords=['steem', 'steemit', 'cryptocurrency', 'blockchain'],
    license='MIT',
    url='https://github.com/steemit/steem-python',
    maintainer='steemit_inc',
    maintainer_email='john@steemit.com',
    py_modules=[
	'steem',
	'steem.cli',
	'steem.steem',
    ],
    entry_points = {
        'console_scripts': ['steempy=steem.cli:legacy'],
    },
    classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Development Status :: 4 - Beta']
)
