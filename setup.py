import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="polyfoto",
    version="0.1.0",
    author="Shane Drabing",
    author_email="shane.drabing@gmail.com",
    packages=setuptools.find_packages(),
    url="https://github.com/shanedrabing/polyfoto",
    description="Create image mosaics.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    data_files=[
        ("", ["LICENSE.txt"])
    ],
    install_requires=[
        "cv2", "imageio", "numpy"
    ]
)
