# Bulk Image Converter
A simple tool to convert images between the formats JPG/JPEG, PNG, WEBP, BMP and TIFF. This tool ignores animated images like GIF and videos, I made this tool like this at purpose because I was needing a tool to do these specific tasks.

<img src="https://files.catbox.moe/3bx7he.png" width="700"/>

<img src="https://files.catbox.moe/x3r9ik.png" width="700"/>


## Portable Version:
If you don't want to install the stuff below to use the script you can download this portable version ready for usage.


<p align="center">
  👉<a href="https://www.mediafire.com/file/nmnnzhoipw73b4d/BulkImageConverter.7z/file"><strong>DOWNLOAD HERE</strong></a>👈
</p>


## Usage:

1. Double-click on _BulkImageConverter.exe_ to launch the converter.
2. Click on `Browse...`, navigate to the folder containing the images you want to convert and select it.
3. Select the Output Format and Output Method you want and click on `Convert`.
4. Click on `Open Folder` to go to the folder with the images you converted.




### Features:

`Output Format`: You can select the conversion format between the available options (JPG/JPEG, PNG, WEBP, BMP and TIFF).

`Output Method`: You can select between two options:

        - *Create new folder for converted images*: With this option the converter creates a new folder "converted_to_{selected format}" in the same folder where the images to be converted are located, and proceeds to save the converted images there.
        - *Replace original images with converted*: With this option the converter proceeds to convert and save the converted images in the same location than the original images, deleting the original images leaving only the converted ones after they were converted successfully.

`Convert`: Start the conversion.

`Open Folder`: Open the folder you selected for the images conversion.





## Requirements to use the script:


  - Double-click on _install_requirements.bat_ to install the required dependencies and Python 3.13
  
  
## Script Usage:

1. Double-click on _BulkImageConverter.bat_ to launch the converter.
2. Click on `Browse...`, navigate to the folder containing the images you want to convert and select it.
3. Select the Output Format and Output Method you want and click on `Convert`.
4. Click on `Open Folder` to go to the folder with the images you converted.


## How to build the executable with PyInstaller:

Double-click on _build.bat_ to build the .exe automatically, and go to the folder "dist" to get the executable when the build finished.


