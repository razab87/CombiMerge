# CombiMerge

CombiMerge is a python plugin for GIMP 3.0 (requires python3). When you have a GIMP session with several grouped layers, CombiMerge selects one layer from each group, merges them together and exports the result as image. This is done for every possible combination. For a detailed description of how it works, see the "Usage" section below.

Tested on Linux Mint 22 but should also work on other Linux distros as well as on Windows and macOS.

**Installation**

- Download the .zip-file from the [release section](https://github.com/razab87/CombiMerge/releases/tag/v1.0).
- Extract the .zip-file and copy the folder "combi_merge" found in CombiMerge-1-0/ to your .../GIMP/3.0/plug-ins folder.
- In GIMP, CombiMerge should then be visible under "Filters". (If not, it may be necessary to make the .py file from combi_merge/ executable, using chmod on linux or equivalent methods on other platforms).
- The .zip also contains two example .xcf-files showing how to properly set up a GIMP session so that CombiMerge can be applied.
- Note: When downloading the plugin via the green "Code" button, you may have to make the .py file executable before using it.


**Usage**

You need a GIMP session consisting of groups where each group may contain several image layers. CombiMerge then takes one image layer from each group, merges them together and exports the image. This is done for all possible combinations. For example, your GIMP session might have the following structure:

\- GroupA <br>
--- layerA1 <br>
--- layerA2 <br>
--- layerA3 <br>
\- GroupB <br>
--- layerB1 <br>
--- layerB2 <br>
--- layerB3 <br>
--- layerB4 <br>
\- GroupC <br>
--- layerC1 <br>
--- layerC2 <br>

All image layers must be part of a group. Nested groups are not allowed (i.e. no groups which contain other groups).

When your GIMP session is set up correctly, go to Filter -> CombiMerge. You can then choose the output directory and output format for your images. Click "Ok" to start the process. Since layers are merged in every combination, the above setting will result in 3&times;4&times;2=24 images for example. The images are stored in a folder called CombiMergeImgs which is created in the chosen output directory.

Naming of the resulting images is done by appending the layer names, separated by a "_". You can enforce specific naming conventions by naming your layers appropriately. For example, in the above setting, you will get an image called "layerA1_layerB1_layerC1.png", an image called "layerA1_layerB1_layerC2.png" and so on (in case you choose png when exporting).

Check the two example .xcf-files to see how you have to set up your GIMP session.


**Note**

The execution of CombiMerge may take some time since it is a combinatorial process and GIMP's image export can be time-consuming. For example, only 5 groups with 5 layers each will result in 5⁵=3125 images to be exported. On my system, CombiMerge takes around 30 minutes for this task. Still much faster than doing all this by hand. (My system: AMD Ryzen 5 1600, GeForce GTX 1060 6GB, 16GB RAM, SSD hard drive.)

While the process is running, do not change anything in your GIMP session (but you can cancel the process if desired).
