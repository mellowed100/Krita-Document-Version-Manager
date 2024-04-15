# What is it?
**Krita Document Version Manager (KDVM)** is a plugin to help manage the different versions of a Krita image file. Instead of using multiple Krita image files and embedding the version into its filename like "artwork_v0001.kra ... artwork_v0009.kra" or "portrait_2024_04_11_a.kra ... portrait_2024_04_12_c.kra", simply use a single image file and name it without any version info and let the plugin manage the rest, i.e. "artwork.kra" or "portrait.kra".


<video autoplay loop playsinline width=300 src="https://github.com/mellowed100/Krita-Document-Version-Manager/assets/55254872/09aeaf5a-0343-47b8-a8e8-dbb0f2703c55"> video </video>




# How does it do this?
Behind the scenes, **KDVM** works by storing and managing the different versions of a Krita file in the filesystem. First, **KDVM** creates a directory to store the different versions. The name of the directory is the same name as the original Krita image file with a ".d" appended to it. 

For example:

|Krita Filename|**KVDM** directory name|
|--------------|-----------------------|
|artwork.kra   | artwork.kra.d         |
|landscape.kra | landscape.kra.d       |

Next, **KDVM** stores each new version of the Krita image in its own subdirectory and generates a thumbnail image for it.

![dir_struct](https://github.com/mellowed100/Krita-Document-Version-Manager/assets/55254872/9df3a03b-0cc7-49f9-935c-0dd65b81cd27)



