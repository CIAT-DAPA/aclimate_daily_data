from setuptools import setup, find_packages

setup(
    name="aclimate_daily_data",
    version='v0.0.5',
    author="christianfeil",
    author_email="h.sotelo@cgiar.com",
    description="Daily data download module",
    url="https://github.com/CIAT-DAPA/aclimate_resampling",
    download_url="https://github.com/CIAT-DAPA/aclimate_resampling",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    keywords='daily data aclimate',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'aclimate_daily_data=aclimate_daily_data.aclimate_run:main',
        ],
    },
    install_requires=[
        "annotated-types==0.5.0",
        "certifi==2023.7.22",
        "charset-normalizer==3.2.0",
        "dnspython==2.4.2",
        "idna==3.4",
        "mypy-extensions==1.0.0",
        "numpy==1.26.0",
        "pydantic==2.3.0",
        "pydantic_core==2.6.3",
        "pymongo==4.5.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "tomli==2.0.1",
        "typing_extensions==4.8.0",
        "urllib3==2.0.4"

    ]
)