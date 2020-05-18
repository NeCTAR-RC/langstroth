import setuptools

from pbr.packaging import parse_requirements


setuptools.setup(
    name='langstroth',
    version='0.1',
    description=('Status page for the NeCTAR Research Cloud'),
    author='NeCTAR',
    author_email='',
    url='https://github.com/NeCTAR-RC/langstroth',
    license='GPLv3',
    packages=[
        'langstroth',
        'nectar_allocations',
        'nectar_status',
        'user_statistics',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=parse_requirements(),
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
        + 'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
)

