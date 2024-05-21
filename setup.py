from setuptools import setup, find_packages

setup(
    name="zipper",
    version="1.0.0",
    author="Caio Maia",
    author_email="caio.maia@usp.br",
    description="Handle file zipping for Gatekeeper",
    url="https://github.com/ardc-brazil/zipper",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        "Development Status :: 1 - Beta",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
