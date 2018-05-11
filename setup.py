from setuptools import setup

# Get requirements from requirements.txt, stripping the version tags
def parse_requirements(filename):
    f = open(filename, 'r')
    return [x.strip().split('=')[0] for x in f.readlines()]

extras_require = {
    'sql': parse_requirements('requirements/sql.txt'),
    'mongo' : parse_requirements('requirements/mongo.txt'),  
}
extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

requires = parse_requirements('requirements.txt')

with open('README.md') as file:
    long_description = file.read()

setup(name='strax',
      version='0.1.2',
      description='Streaming analysis for XENON',
      maintainer='Jelle Aalbers',
      maintainer_email='j.aalbers@uva.nl',
      url='https://github.com/jelleaalbers/strax',
      setup_requires=['pytest-runner'],
      install_requires=requires,
      tests_require=requires + parse_requirements('requirements/test.txt'),
      extras_require=extras_require,
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=['strax',
                'strax.processing',
                'strax.storage',
                'strax.xenon'],
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',],
      zip_safe = False,
    )
