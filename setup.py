import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
setup(
  name="autoran",
  version="0.0.1",
  description="Automatic deployment of open RAN softwares using Python",
  long_description=README,
  long_description_content_type="text/markdown",
  author="Seyed Samie Mostafavi",
  author_email="samiemostafavi@gmail.com",
  license="MIT",
  packages=find_packages(),
  zip_safe=False
)
