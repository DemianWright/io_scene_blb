# Blender BLB Exporter #
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://img.shields.io/badge/License-GPL%20v2-blue.svg)

A [Blender](https://www.blender.org/) add-on written in Python 3 for exporting [Blockland](http://blockland.us/) bricks (.<abbr title="Blockland brick">BLB</abbr> files) directly from Blender 2.67 and newer without the need for intermediary formats or external programs.
It works on the principle of "what you see is what you get", the brick will look exactly the same in-game as it does in the 3D viewport<sup>[__*__](#exporter-fn-1)</sup>.

The add-on does not support importing .BLB files yet.

## Table of Contents ##
1. [Features](#features)
   1. [Planned Features](#planned-features)
1. [Installation](#installation)
   1. [Updating](#updating)
1. [Terminology](#terminology)
1. [Brick Scale](#brick-scale)
1. [Definition Tokens](#definition-tokens)
   1. [Mesh Definition Tokens](#mesh-definition-tokens)
      1. [Defining Quad Sections & Coverage](#defining-quad-sections--coverage)
      1. [Defining Colors](#defining-colors)
         1. [RGBA Color Format](#rgba-color-format)
1. [Definition Objects](#definition-objects)
   1. [Defining Collision](#defining-collision)
   1. [Defining Brick Grid](#defining-brick-grid)
1. [Brick Textures](#brick-textures)
1. [UV Mapping](#uv-mapping)
1. [Rounded Values](#rounded-values)
1. [Export Properties](#export-properties)
   1. [Blender Properties](#blender-properties)
      1. [Bricks to Export](#bricks-to-export)
      1. [Brick Name from (Single Export)](#brick-name-from-single-export)
      1. [Export Only (Single Export)](#export-only-single-export)
      1. [Brick Names from (Multiple Export)](#brick-names-from-multiple-export)
      1. [Bricks Defined by (Multiple Export)](#bricks-defined-by-multiple-export)
      1. [Export Bricks in (Multiple Export)](#export-bricks-in-multiple-export)
      1. [Forward Axis](#forward-axis)
      1. [Scale](#scale)
      1. [Apply Modifiers](#apply-modifiers)
      1. [Custom Definition Tokens](#custom-definition-tokens)
   1. [BLB Properties](#blb-properties)
      1. [Custom Collision](#custom-collision)
      1. [Fallback Collision](#fallback-collision)
      1. [Calculate Coverage](#calculate-coverage)
      1. [Automatic Quad Sorting](#automatic-quad-sorting)
      1. [Use Material Colors](#use-material-colors)
      1. [Use Vertex Colors](#use-vertex-colors)
      1. [Parse Object Colors](#parse-object-colors)
      1. [Calculate UVs](#calculate-uvs)
      1. [Store UVs](#store-uvs)
      1. [Round Normals](#round-normals)
      1. [Precision](#precision)
   1. [File Properties](#file-properties)
      1. [Pretty Print](#pretty-print)
      1. [Write Log](#write-log)
      1. [Only on Warnings](#only-on-warnings)
      1. [Terse Mode](#terse-mode)
1. [Troubleshooting](#troubleshooting)
   1. [Automatically calculated UV coordinates for brick textures are distorted](#automatically-calculated-uv-coordinates-for-brick-textures-are-distorted)
   1. [Automatically calculated UV coordinates for brick textures are rotated incorrectly](#automatically-calculated-uv-coordinates-for-brick-textures-are-rotated-incorrectly)
   1. [The TOP brick texture has incorrect rotation in Blender](#the-top-brick-texture-has-incorrect-rotation-in-blender)
1. [Warning & Error Log Messages](#warning--error-log-messages)
   1. [Warnings](#warnings)
   1. [Errors](#errors)
      1. [Fatal Errors](#fatal-errors)
      1. [Non-Fatal Errors](#non-fatal-errors)
1. [Contributors](#contributors)

## Features ##
The exporter supports all BLB features.
- [x] Brick size
   - Automatic calculation or manually defined
- [x] Brick grid
   - Automatic calculation (full brick only) or manually defined
- [x] Coverage
   - Manually define hiding own and adjacent brick quads
   - Automatic area calculation for arbitrary brick grid shapes
   - Automatic and/or manual quad sorting
- [x] Collision boxes
   - Automatic calculation (full brick only) or manually defined
- [x] Textures
   - Automatic (side texture only) or manual brick texture definition
- [x] Quads
   - Triangles are automatically converted to quads
   - N-gons are ignored
- [x] UV coordinates
   - Manually define UV coordinates
   - Automatic UV calculation for all brick textures
- [x] Colors
   - Multiple ways to define colors: materials, object names, vertex paint
   - Per-vertex coloring
   - Transparency
   - Additive and subtractive colors
- [x] Flat and smooth shading
- [x] Save and load export settings
- [x] Export multiple bricks from the same file
- [x] Vertices are all relative to the defined or calculated brick bounds
   - Object centers (orange dot) are irrelevant: calculations are performed using vertex world coordinates
   - Object locations relative to the origin of the world are irrelevant: the calculated center of the brick bounds acts as the new world origin
   - Object locations relative to the Blender grid are irrelevant: the brick bounds define the brick grid origin (however it is highly recommended to align the brick bounds object with the Blender grid for ease of use)
   - This allows you to easily create multiple bricks in the same file in any location in the 3D space and the bricks still export correctly as expected
   - Arbitrary brick grid rotation, however, is not supported
- [x] Selective object export: selection, visible layers, entire scene
- [x] Change brick rotation during export: does not affect objects in the .BLEND file
- [x] Change brick scale during export: does not affect objects in the .BLEND file
- [x] Apply modifiers (e.g. edge split) during export: does not affect objects in the .BLEND file
- [x] Terse file writing: exclude optional lines from the BLB file
- [x] Pretty .BLB files: extraneous zeros are not written at the end of floating point values and if possible, they are written as integers
- [x] Logging with descriptive error and warning messages to help you correct problems with the brick
- [x] Customizable floating point accuracy
- [ ] Exporting DTS collision is not yet supported.

### Planned Features ###
These features may or may not be implemented at some unspecified time in the future.
Listed below approximately in the order they are planned to be implemented in.

1. Exporting DTS collision using Nick Smith's [io_scene_dts](https://github.com/qoh/io_scene_dts) Blender add-on.
1. Importing .BLB files.
1. Automatic rendering of the brick preview icon.
1. Export-time brick rotation on the Z-axis.

## Installation ##
1. Download the add-on using one of them methods below:
    1. **The cutting edge:** [download the latest version of the develop branch](https://github.com/DemianWright/io_scene_blb/archive/develop.zip) or go to the [develop branch page](https://github.com/DemianWright/io_scene_blb/tree/develop) and press `Clone or download > Download ZIP`.
        * The develop branch contains the newest features still under active development. Some functionality may be broken or only half-implemented.
    1. **The latest version:** [download the latest version of the master branch](https://github.com/DemianWright/io_scene_blb/archive/master.zip) or go to the [front page](https://github.com/DemianWright/io_scene_blb) of the repository and press `Clone or download > Download ZIP`.
    1. **A specific version:** [go to the releases page](https://github.com/DemianWright/io_scene_blb/releases) and follow the instructions on the specific release.
1. Open Blender and go to `File > User Preferences > Add-ons`.
1. Press the `Install from File...` button at the bottom of the dialog and find the downloaded .ZIP file.
1. Press `Install from File...` again.
1. Enable the add-on in the add-ons list and press `Save User Settings` to keep the add-on enabled the next time you start Blender.
1. The export option is under `File > Export > Blockland Brick (.blb)`.

### Updating ###
1. Open Blender and go to `File > User Preferences > Add-ons`.
1. Quickly find the add-on by typing `blb` into the search field.
1. Expand the add-on by clicking the white triangle on the left, press the `Remove` button, and confirm the removal.
1. Follow the installation instructions above.

## Terminology ##
A list of more or less technical terms used in this document.
The definitions are in the context of Blockland, Blender, and this exporter and may vary from their mathematical definitions.
<dl>
<dt><a name="def-aap">Axis-Aligned Plane</a></dt>
<dd>A <strong>plane</strong> whose vertices have the same coordinate on exactly one coordinate axis.
When this two-dimensional plane is viewed from either of the other two coordinate axes it disappears from view.</dd>

<dt><a name="def-aabb"><a href="https://en.wikipedia.org/wiki/Minimum_bounding_box#Axis-aligned_minimum_bounding_box">Axis-Aligned Bounding Box</a></a> / Axis-Aligned Minimum Bounding Box</dt>
<dd>A <a href="#def-cuboid">cuboid</a> that completely encompasses all vertices of one or more <a href="#def-mesh-object">mesh objects</a>.
The faces of this cuboid are parallel with the coordinate axes.</dd>

<dt><a name="def-aac">Axis-Aligned Cuboid</a></a></dt>
<dd>A <a href="#def-cuboid">cuboid</a> whose faces are parallel with the coordinate axes.</dd>

<dt><a name="def-brick-grid">Brick Grid</a></dt>
<dd><ol>
<li>The three-dimensional space of the game divided into 1x1x1 brick plates</li>
<li>The blocks of <code>u</code>, <code>x</code>, <code>-</code>, and other characters near the top of the .BLB file that define the brick's placement rules.
See <a href="#defining-brick-grid">Defining Brick Grid</a>.</li<
</ol></dd>

<dt><a name="def-brick">Brick</a></dt>
<dd><ol>
<li>A collection of <a href="#def-mesh">meshes</a> that acts as a single object in Blockland and all the non-visual data it contains such as collision information.</li>
<li>The BLB file itself.</li>
<li>The Blender <a href="#def-object">objects</a> that when exported produce a BLB file.</li>
</ol>
</dd>

<dt><a name="def-coverage">Coverage</a> (System)</dt>
<dd><ol>
<li>The Blockland coverage system describes how to hide faces on a brick and any adjacent bricks.</li>
<li>The six pairs of integers near the top of a BLB file.</li>
</ol>
</dd>

<dt><a name="def-cuboid">Cuboid</a></dt>
<dd>More specifically a <strong>right cuboid</strong> in the context of Blockland bricks.
A <a href="https://en.wikipedia.org/wiki/Convex_polytope">convex polyhedron</a> with 6 faces that are all at right angles to each other.
I.e. a regular cube or a cube that is elongated on one axis.</dd>

<dt><a name="def-definition-object">Definition Object</a></dt>
<dd>An <a href="#def-object">object</a> that has a specific <a href="#def-definition-token">definition token</a> in its name.
These objects cannot be seen in-game.
They exist to tell the exporter how to create the <a href="#def-brick">brick</a>.
There are three different definition objects:
<ul>
	<li>a <a href="#definition-objects-bounds">bounds definition object</a>,</li>
	<li>a <a href="#definition-objects-collision">collision definition object</a>,</li>
	<li>and a <a href="#defining-brick-grid">brick grid definition object</a>.</li>
</ul></dd>

<dt><a name="def-definition-token">Definition Token</a></dt>
<dd>A special <a href="#def-token">token</a> in an <a href="#def-object">object's</a> name that tells the exporter additional information about that object or the entire brick.</dd>

<dt><a name="def-face">Face</a></dt>
<dd>A visible surface that is rendered in game and in the Blender viewport.
The surface must be bound by or created by at least three vertices (making it a <a href="#def-tri">tri</a>) or in deed any number of vertices (also called an <a href="#def-n-gon">n-gon</a>).

:exclamation: Blockland bricks only support faces made from exactly four vertices: <a href="#def-quad">quads</a>.</dd>

<dt><a name="def-mesh">Mesh</a></dt>
<dd>The vertices, edges, and faces that make up a 3D <a href="#def-model">model</a>.</dd>

<dt><a name="def-mesh-object">Mesh Object</a></dt>
<dd>A Blender object that contains vertices, edges, and <a href="#def-face">faces</a>.
Commonly just referred to as an <a href="#def-object">object</a>.</dd>

<dt><a name="def-model">Model</a></dt>
<dd>One or more <a href="#def-object">objects</a> that make up a <a href="#def-brick">brick</a>.</dd>

<dt><a name="def-n-gon">N-gon</a></dt>
<dd>Technically any <a href="https://en.wikipedia.org/wiki/Polygon">polygon</a> but in this document used to refer to a single face formed from more than four vertices.
N-gons are not necessarily <a href="#def-plane">planes</a>.

:exclamation: These are not supported by the exporter or Blockland: the faces will be ignored.</dd>

<dt><a name="def-object">Object</a></dt>
<dd>Usually a <a href="#def-mesh-object">mesh object</a>.
Technically refers to all the meshes, cameras, lights, empties, and everything else you see in the 3D viewport.
Blender objects contain data about vertices, materials, groups, object names, and more.</dd>

<dt><a name="def-plane">Plane</a></dt>
<dd>A flat two-dimensional surface in 3D space.
A particular type of <a href="#def-face">face</a>.</dd>

<dt><a name="def-quad">Quad</a></dt>
<dd>A <a href="#def-face">face</a> with four vertices.
Quads are not necessarily <a href="#def-plane">planes</a>.</dd>

<dt><a name="def-string">String</a></dt>
<dd>A sequence of letters.
Usually a word.</dd>

<dt><a name="def-token">Token</a></dt>
<dd>A <a href="#def-string">string</a> surrounded with a <a href="#def-whitespace">whitespace character</a> on one or both sides.</dd>

<dt><a name="def-tri"><abbr title="Triangle">Tri</abbr></a></dt>
<dd>A <a href="#def-face">face</a> with three vertices.
Triangles are always <a href="#def-plane">planes</a>.

:exclamation: These are not supported by Blockland bricks and they are converted to <a href="#def-quad">quads</a> automatically.</dd>

<dt><a name="def-visible-object">Visible Object</a></dt>
<dd>Any <a href="#def-mesh-object">mesh object</a> that is not a <a href="#def-definition-object">definition object</a>.
Visible objects are rendered and are seen in-game as a <a href="#def-brick">brick</a>.</dd>

<dt><a name="def-volume">Volume</a></dt>
<dd>A section of 3D space, usually <a href="#def-cuboid">cuboidal</a> in shape in the context of this exporter.</dd>

<dt><a name="def-whitespace"><a href="https://en.wikipedia.org/wiki/Whitespace_character">Whitespace</a></a> (Character)</dt>
<dd>In Blender, commonly a space or a tab character.</dd>
</dl>

## Brick Scale ##
This add-on defines a `1x1x1` Blockland brick to be exactly `1.0 1.0 1.2` Blender units on the X, Y, and Z axes.
Likewise a `1x1f` Blockland plate is defined to be exactly `1.0 1.0 0.4` Blender units.
However, the final scale of the exported brick can be changed with the [Scale](#scale) property.
For example setting the [Scale](#scale) property to `150%` means that during the exporting process, the [objects](#def-object) are scaled by `1.5`.
This is particularly useful when exporting 3D models created for another BLB exporter/converter that has defined the size of a `1x1f` plate to be different from this exporter.

## Definition Tokens ##
[Definition tokens](#def-definition-token) are special [strings](#def-string) added to the names of [objects](#def-object), materials, vertex color layers, and other Blender data objects that have a name.
A name field may contain other text in addition to definition tokens as long as the tokens themselves are separated from other tokens and text by one [whitespace character](#def-whitespace) such as a space.
The definition tokens may be changed from the defaults by selecting [Custom Definition Tokens](#custom-definition-tokens) in the export dialog.

:bulb: Blender adds a running index (e.g. `.003`) to the end of duplicate object, material, etc. names.
This is handled correctly, you need not worry about it.
The logic for removing the index simply checks if `.` is the fourth last character in the name and simply removes it an everything after it.

:exclamation: Each definition token may only appear once in a name field.

Below is a full list of all default definition tokens with a brief description.
For more information on what each of them do, see the specific section of the readme that relates to that token.
Note that not all definition tokens change the object into a [definition object](#definition-objects).

Default Token | Category | Usable In | Is a [Definition Object](#def-definition-object) | Meaning
--------------|----------|-----------|:----------------------:|--------
`bounds` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | This is a bounds definition object.
`collision` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | This is a collision definition object.
`gridb` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | Write brick grid `b` symbol in this [volume](#def-volume).
`gridd` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | Write brick grid `d` symbol in this [volume](#def-volume).
`gridu` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | Write brick grid `u` symbol in this [volume](#def-volume).
`grid-` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | Write brick grid `-` symbol in this [volume](#def-volume).
`gridx` | [Definition objects](#definition-objects) | [Object](#def-object) name | Yes | Write brick grid `x` symbol in this [volume](#def-volume).
`qt` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the top section.
`qb` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the bottom section.
`qn` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the north section.
`qe` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the east section.
`qs` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the south section.
`qw` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the west section.
`qo` | [Quad sorting](#defining-quad-sections--coverage) | [Object](#def-object) name | No | Sort these [faces](#def-face) in the omni section.
`c` | [Colors](#defining-colors) | [Object](#def-object) name | No | The next four numbers define the color for these [faces](#def-face).
`blank` | [Colors](#defining-colors) | Material name | No | Do not write a color for [faces](#def-face) using this material: use the in-game spray can color as is.
`cadd` | [Colors](#defining-colors) | Material name, vertex color layer name | No | Add the material/vertex color of these [faces](#def-face) to the in-game spray can color.
`csub` | [Colors](#defining-colors) | Material name, vertex color layer name | No | Subtract the material/vertex color of these [faces](#def-face) from the in-game spray can color.

### Mesh Definition Tokens ###
Mesh definition tokens are a sub-category of [definition tokens](#definition-tokens) that can only be used in the names of [objects](#def-objects) but do not change the object into an invisible [definition object](#definition-objects).
Objects that have one or more of these definition tokens are treated as [visible objects](#def-visible-object) and they govern some aspect of the [faces](#def-face) of the [mesh](#def-mesh) in that object.

:exclamation: Each definition token may only appear once in a name field but a name may contain both definition tokens.

Definition | Default Token | Requirements | Maximum Count/Brick | Description 
-----------|---------------|--------------|--------------------:|------------
<a name="mesh-definition-tokens-color">Color</a> | `c` <red> <green> <blue> <alpha> | See [Defining Colors](#defining-colors) | Unlimited | Defines the color of the [faces](#def-face).
Coverage | See [Defining Quad Sorting & Coverage](#defining-quad-sections--coverage) | Must contain a [face](#def-face) | Unlimited |  Assigns the object's quads into a specific section in the brick.

#### Defining Quad Sections & Coverage ####
BLB files allow [mesh](#def-mesh) [faces](#def-face) to be sorted into seven sections: top, bottom, north, east, south, west, and omni.
Quads in these sections may then be automatically hidden in-game using the [coverage system](#def-coverage), if it is defined in a meaningful way in the BLB file.

The coverage system allows the game to skip rendering quads that are completely covered by adjacent bricks improving the frame rate when a large number of bricks are on the screen at once.
Quads are sorted into these sections by using one of the tokens below in the name of the [object](#def-object) containing the faces to be sorted into that section.
If a [visible object](#def-visible-object) has no quad sorting token specified, the omni section is used.

Default Token | Section
--------------|--------
`qt` | Top
`qb` | Bottom
`qn` | North
`qe` | East
`qs` | South
`qw` | West
`qo` | Omni ("any" or "none", **default**)

:exclamation: Sorting quads in this manner is pointless unless the [Coverage](#coverage) property in the export dialog is enabled and at least one option is enabled.

:exclamation: Due to how Blockland handles .blb files, ensure that north is assigned to faces facing the +Y direction, east is assigned to faces facing the +X direction, with south and west corresponding to -Y and -X respectively.

In the export dialog [Coverage](#coverage) properties there are two options for each section/side of the brick:

Option | Description
-------|------------
Hide Self | For example when enabled for the top section, the game will not render the [quads](#def-quad) in the **top** section of **this brick** when the top area of this brick is completely covered.
Hide Adjacent | For example when enabled for the top section, the game will not render the [quads](#def-quad) in the **bottom** section of **adjacent bricks** on top of this brick if the coverage rules for those adjacent bricks are fulfilled.

#### Defining Colors ####
The exporter supports three methods for defining brick colors.
To allow faces to be colored using the spray can tool in game do not assign a color those faces.
See [RGBA Color Format](#rgba-color-format) for a detailed explanation of how to write an RGBA color value.

Method | Overrides | Extent of Coloring | RGB Values | Alpha Value | Notes
-------|-----------|--------------------|------------|-------------|------
Object Colors | In-game paint color | Entire object (color & alpha)| In [object](#def-object) name after the [Color token](#mesh-definition-tokens-color) | In object name after the red, green, and blue values | Implemented only to support legacy brick [models](#def-model), **not recommended for use**.
Material Colors | Object Colors | Assigned faces (color & alpha) | In `Material` tab as `Diffuse Color` | In `Material` tab under `Transparency` in `Alpha` slider| The **recommended method** for defining color. Multiple materials may be used in a single object.
<a name="vertex-colors">Vertex Colors</a> | Material Colors | Entire [object](#def-object) (per-vertex color), entire object (alpha) | In `Data` tab under `Vertex Color` as a vertex color layer, modified using the `Vertex Paint` mode | In `Data` tab under `Vertex Color` as the name of the vertex color layer | Creating a vertex color layers will color the entire object white, but the color of individual vertices may be changed.

There are three definition tokens that are specific to dealing with colors.

Token | Usable In | Description
------|-----------|------------
<a name="defining-colors-blank">`blank`</a> | Material name | Ignore the material's color and do not write any color for the faces with this material assigned so they can be colored by the spray can in-game. This feature exists because an [object](#def-object) that has a material, cannot have faces that do not have a material assigned to them.
<a name="defining-colors-cadd">`cadd`</a> | Material name, vertex color layer name | Use this color as an additive color: add the values of this color to the spray can color in-game. For example to make the spray can color **a little lighter** use a **dark gray** color.
<a name="defining-colors-csub">`csub`</a> | Material name, vertex color layer name | Use this color as a subtractive color: subtract the values of this color from the spray can color in-game. For example to make the spray can color **a lot darker** use a **light gray** color.

##### RGBA Color Format #####
The exporter understands two ways of defining an RGBA color using text.

:exclamation: Please note that you **must** use a comma character (`,`) as the decimal separator for floating point numbers.

1. The commonly used method of writing 4 integers that are in the range 0–255, where 0 is black, separated with a whitespace character such as a space.
For example `127 255 10 191` for a yellow-green color that is 25% transparent.
A full [object](#def-object) name could be for example `glass c 240 255 255 128.001`.
   - In the above example the running index `.001` that Blender added at the end would be removed by the exporter.
1. Writing 4 decimals in the range 0.0–1.0, where 0.0 is black, separated with a whitespace character such as a space.
An [object](#def-object) could have a name such as `c 0,125 0,0 0,5 1,0 flower`, for example.
   - The leading zero may be omitted.
   - Up to 16 decimals are supported.

## Definition Objects ##
When a specific definition token is read in an [object's](#def-object) name it is treated as a definition object.
Definition objects contain non-visual data about the [brick](#def-brick) and as such are not exported as [visual objects](#def-visual-object)

Definition Object | Default Token | Requirements | Maximum Count/Brick | Must Be Within [**Bounds**](#definition-objects-bounds)  | Axis-Aligned | Brick Grid Aligned | Can Overlap | Description
------------------|---------------|--------------|--------------------:|:-------------------:|:------------:|:------------------:|:-----------:|------------
<a name="definition-objects-bounds">Bounds</a> | `bounds` | At least two vertices, must have volume | 1 | N/A | Yes [**(1)**](#definition-objects-fn-1) | Yes | N/A | Defines the dimensions or the size of the brick.
<a name="definition-objects-collision">Collision</a> | `collision` | At least two vertices, must have volume | 10 | Yes [**(2)**](#definition-objects-fn-2) | Yes | No | Yes | Defines a collision [cuboid](#def-cuboid). See [Defining Collision](#defining-collision) for more info.
Brick Grid | See [Defining Brick Grid](#defining-brick-grid) | At least two vertices, must have volume | Unlimited | Yes | Yes [**(1)**](#definition-objects-fn-1) | Yes | Yes [**(3)**](#definition-objects-fn-4) | Defines a volume in the brick grid to fill with a specific brick grid symbol.

<a name="definition-objects-fn-1">**(1)**</a> It is highly recommended to use [axis-aligned cuboids](#def-aac) to define bounds and the [brick grid](#def-brick-grid).
However, if you insist on defining the size of your brick in monkey heads, you can.
Only the [axis-aligned bounding box](#def-aabb) of the bounds and brick grid objects are used.

<a name="definition-objects-fn-2">**(2)**</a> Collision boxes outside brick bounds are technically not invalid and the brick will function in-game.
This behavior is not allowed by the exporter because collision outside brick bounds is horribly broken as it was never intended work in that manner.

<a name="definition-objects-fn-3">**(3)**</a> See [Defining Brick Grid](#defining-brick-grid) for the specific rules about overlapping brick grid definitions.

### Defining Collision ###
Blockland bricks only supports [AABB collision](https://en.wikipedia.org/wiki/Minimum_bounding_box#Axis-aligned_minimum_bounding_box).
In other words brick collision may only be defined using [cuboids](#def-cuboid) of varying sizes that align with the coordinate axes.
You can rotate said cuboids however you want but that will not lead to rotated collision cuboids in-game.
Only the the [axis-aligned bounding box](#def-aabb) of the collision definition objects are used.

:bulb: Using any other shape than an axis-aligned cuboid to define collision is not recommended as it makes the Blender file more difficult to understand and also breaks the "what you see is what you get" principle.

### Defining Brick Grid ###
Brick grid definitions represent a 3D volume in the 3D space the brick grid encompasses.
You can imagine it as if the entire cuboidal shape of the brick would be filled with 1x1f plates and these volumes define the properties of all the 1x1f plates within that volume.
Each brick grid definition has their own priority.
When two or more brick grid definition objects overlap in 3D space, the one with the **higher** priority takes precedence and will overwrite the symbols in the brick grid that any definitions with lower priorities would have written.

:exclamation: Be aware that if your brick does not contain a `brickd` definition on the bottom of the brick, the brick cannot be planted on other bricks or the ground.

Default Token | Brick Grid Symbol | Description
--------------|:-----------------:|------------
`gridb` | `b` | Bricks may be placed above and below this volume. This brick can be planted on the ground.
`gridd` | `d` | Bricks may be placed below this volume. This brick can be planted on the ground.
`gridu` | `u` | Bricks may be placed above this volume.
`grid-` | `-` | Bricks may be placed inside this volume. (I.e. empty space.) This is the default symbol, any volume that does not have a brick grid definition uses this symbol.
`gridx` | `x` | Bricks may not be placed inside this volume.

## Brick Textures ##
Defining brick textures is done using Blender materials.
To assign a brick texture to a face, assign a material to it containing a valid brick texture name (case insensitive):
- `bottomedge`
- `bottomloop`
- `print`
- `ramp`
- `side`
- `top`

If no brick texture is defined, `side` is used.
Material name may contain other words as long as the brick texture name is separated from them with one whitespace character such as a space.
A common combination is to define a brick texture name and the [definition token `blank`](#defining-colors-blank) (e.g. `blank ramp` or `side blank`) to allow the player to color the face in-game using the spray can.

## UV Mapping ##
Manually defined UV coordinates must be stored in one or more UV layers that do not share a name with one of the automatically generated UV layers:
- `TEX:BOTTOMEDGE`
- `TEX:BOTTOMLOOP`
- `TEX:PRINT`
- `TEX:RAMP`
- `TEX:TOP`

Any data in UV layers with one the names above will the overwritten during automatic UV calculation.

:exclamation: Note that BLB files only support storing quads.
As such, any tris with UV coordinates will have their last UV coordinate duplicated to transform it into a quad.
This may or may not cause visual distortion in the UV mapping.

If the [Calculate UVs](#calculate-uvs) property is enabled, UV coordinates will be automatically calculated based on the dimensions of the quad and the name of the material assigned to it.
(See [Brick Textures](#brick-textures) to learn how to define brick textures with materials.)
The generated coordinates are only guaranteed to be correct for strictly rectangular quads, for any other shapes the results may not be satisfactory.
If using brick textures on non-rectangular quads it is recommended to manually define the UV coordinates for best results.

## Rounded Values ##
Floating point numbers (numbers with a decimal point) contain [inherent inaccuracies](https://en.wikipedia.org/wiki/Floating_point#Accuracy_problems).
For example when exporting a 1x1x1 brick [model](#def-model) at the maximum accuracy the vertex coordinate of one of the corners is `0.5 0.5 1.5000000596046448`.
This causes the 1x1x1 brick to be `3.00000011920928955078125` plates tall instead of exactly `3.0` like it should.
The only way to get fix this error is to round the vertex coordinates.
Practically speaking it is impossible to visually discern the difference between a brick that is 3 plates tall versus one that is `3.00000011920928955078125` plates tall in the game.
The only real benefit that comes from the rounding is nicer looking .BLB files.

The default value of `0.000001` was chosen through manual testing.
Rest assured that the rounding will cause no visual oddities whatsoever because the value is so small.
This was manually confirmed with a sphere brick made from 524288 quads.
Moving the camera as close to the surface of the brick as the game was capable of rendering, the surface of the sphere appeared mathematically perfect because the distance between the vertices was less than the size of a single pixel.

:exclamation: The exporter will only ever write up to 16 decimal places regardless of the precision of the value.

Floating Point Value | Rounded
---------------------|:------:
[Visible object](#def-visible-object) vertex coordinates | Yes
[Bounds object](#definition-objects-bounds) vertex coordinates | Yes
[Collision object](#definition-objects-collision) vertex coordinates | Yes
[Brick grid object](#defining-brick-grid) vertex coordinates | Yes
Normal vectors | [Optional](#round-normals)
[RGBA color](#defining-colors) values | No
[UV coordinates](#uv-mapping) | No

## Export Properties ##
The following user properties are present in the current version of the exporter.

### Blender Properties ###

#### Bricks to Export ####
How many bricks to export in one go from the file.

Value | Description
------|------------
Single | Export only one brick. **(Default)**
Multiple | Export one or more bricks. Shows additional settings when selected.

#### Brick Name from (Single Export) ####
Where the .BLB file name is defined.

Value | Description
------|------------
Bounds | Brick name is defined in the [Bounds object](#definition-objects-bounds) after the bounds definition token, separated with a whitespace character. Export file dialog is only used set to directory. **(Default)**
File | Brick name is the same as the file name. Can be manually set in the export file dialog.

#### Export Only (Single Export) ####
Which [objects](#def-object) to process and export to the .BLB file.

Value | Description
------|------------
Selection | Objects that are selected and have an orange outline. **(Default)**
Layers | All objects in the layers that are currently visible, regardless of selection.
Scene | All objects in the current scene. I.e. all objects in all layers regardless of the layer visibility.

#### Brick Names from (Multiple Export) ####
Where the names of the .BLB files are defined.

Value | Description
------|------------
Bounds | Brick names are defined in the [Bounds object](#definition-objects-bounds) after the bounds definition token, separated with a whitespace character. Export file dialog is only used set to directory. **(Default)**
Groups | Brick names are the same as the names of the groups name. Export file dialog is only used set to directory.

#### Bricks Defined by (Multiple Export) ####
How is a single brick defined.

Value | Description
------|------------
Groups | Each brick is in its own group. [Objects](#def-object) in multiple groups belong to multiple bricks. **(Default)**
Layers | Each brick is in its own layer. [Objects](#def-object) in multiple layers belong to multiple bricks. When selected brick names must be defined in the [Bounds object](#definition-objects-bounds).

#### Export Bricks in (Multiple Export) ####
Which bricks to process and export to .BLB files.

Value | Description
------|------------
Layers | Export all bricks in the layers that are currently visible. **(Default)**
Scene | Export all bricks in the current scene. I.e. all bricks in all layers regardless of the layer visibility.

#### Forward Axis ####
The Blender coordinate axis that will point forwards in-game when the player plants the brick directly in front of them without rotating it.
Does not change the rotation of the [objects](#def-object) in the Blender scene.

Value | Description
------|------------
+X | Positive X-axis
+Y | Positive Y-axis **(Default)**
-X | Negative X-axis
-Y | Negative Y-axis

#### Scale ####
The scale of the brick in-game.
Values outside the the range of 0.001–400.0 may be typed in manually.
Does not change the scale of the [objects](#def-object) in the Blender scene.
See [Brick Scale](#brick-scale) for additional information.
(Default: `100%`)

#### Apply Modifiers ####
Applies any modifiers on the [object](#def-object) before exporting.
Does not change the modifiers of the objects in the Blender scene.
(Default: `True`)

#### Custom Definition Tokens ####
Allows you to specify the definition tokens the exporter uses.
See [Definition Tokens](#definition-tokens) for more information.
(Default: `False`)

:bulb: Enabling this property shows additional properties.

### BLB Properties ###

#### Custom Collision ####
Export custom collision definitions if there are any.
See [Defining Collision](#defining-collision).
(Default: `True`)

#### Fallback Collision ####
The type of collision to calculate for the brick if no custom collision definitions are found.
Enabling this property shows additional properties.

Value | Description
------|------------
Bounds | Use the defined or calculated [bounds](#definition-objects-bounds) of the brick as the collision cuboid. **(Default)**
AABB | Calculate the [axis-aligned bounding box](#def-aabb) of all [visible objects](#def-visible-object) and use that as the collision cuboid.

#### Calculate Coverage ####
Enable coverage calculations.
This is pointless unless [Automatic Quad Sorting](#automatic-quad-sorting) is enabled or at least one [object](#def-object) has a quad sorting definition.
See [Defining Quad Sorting & Coverage](#defining-quad-sections--coverage) for more information.
(Default: `False`)

:bulb: Enabling this property shows additional properties.

#### Automatic Quad Sorting ####
Automatically calculate the correct section for quads that in the same plane as the bounding planes of the bounds object.
This is pointless unless [Coverage](#coverage) is enabled.
(Default: `True`)

#### Use Material Colors ####
Assign [face](#def-face) colors from [object](#def-object) materials.
(Default: `False`)

#### Use Vertex Colors ####
Assign [face](#def-face)  colors from vertex color layers.
(Default: `False`)

#### Parse Object Colors ####
Assign [face](#def-face) colors from [object](#def-object) names.
(Default: `False`)

#### Calculate UVs ####
Automatically calculate correct UV coordinates based on the brick texture name specified in the material name.
See [UV Mapping](#uv-mapping) for more information.
(Default: `True`)

#### Store UVs ####
Write calculated UVs into Blender [objects](#def-object).
Data in existing generated UV layers will be overwritten.
See [UV Mapping](#uv-mapping) for a list of generated UV layer names.
(Default: `True`)

#### Round Normals ####
Round vertex normals to the user-defined floating point value precision.
If disabled normals will be written as accurately as possible but extraneous zeros will still be removed.
(Default: `False`)

#### Precision ####
Allows you to specify a custom precision for floating point numbers.
See [Rounded Values](#rounded-values) for more details.
(Default: `0.000001`)

### File Properties ###

#### Pretty Print ####
When enabled does not write extraneous zeros to the end of floating point numbers.
Additionally if a numerical value is exactly equal to an integer, no decimal places are written.
If disabled will write all floating point numbers using as many decimal places as used in the [Precision](#precision) property. 
(Default: `True`)

#### Write Log ####
Write a log file to the same folder as the exported brick detailing the export process.
Shows additional settings when selected.
(Default: `True`)

#### Only on Warnings ####
Write a log file only if warnings or errors occurred during the export process.
(Default: `True`)

#### Terse Mode ####
When enabled does not write optional lines to the .BLB file such as the lines marking the different quad sections.
Using this option is not recommended as it makes the .BLB file harder to read and understand.
Although the file is shorter, the difference in file size is negligible.
(Default: `False`)

## Troubleshooting ##
Solutions to common issues with the BLB Exporter.
If you have another issue with the exporter be sure to enable the [Write Log](#write-log) property and export again.
The log file may contain warnings or errors describing issues with the [objects](#def-object) and how to fix them.
Additional instructions on how to fix specific issues are detailed in the [Warning & Error Log Messages](#warning--error-log-messages) section.

### Automatically calculated UV coordinates for brick textures are distorted ###
The automatic UV calculation is only designed to work with rectangular quads.
Manually define UV coordinates for non-rectangular quads.

### Automatically calculated UV coordinates for brick textures are rotated incorrectly ###
The quad with incorrectly rotated UV coordinates (e.g. the lightest side of the SIDE texture pointing sideways instead of up) is not a perfect rectangle.
Even one vertex being off by some minuscule, visually indistinguishable amount from a perfectly rectangular shape can cause the automatic UV calculation to incorrectly determine the rotation of the quad.
Double check all 4 coordinates of the quad and manually correct any floating point errors.
If working on axis-aligned quads or if the vertices should be on grid points snapping the coordinates of the problem quad to grid coordinates by selecting `Mesh > Snap > Snap Selection to Grid` in the 3D viewport toolbar usually fixes floating point errors.

### The TOP brick texture has incorrect rotation in Blender ###
Blockland automatically performs rotations on the UV coordinates of the TOP brick texture during runtime so that the lightest side of the texture is always facing towards the sun.
Because of this there is no correct way of representing the TOP brick texture in Blender.
As a compromise the exporter will rotate the lightest side of the TOP brick texture to face towards the axis select in the [Forward Axis](#forward-axis) property.
This means the UV coordinates of the TOP brick texture in Blender may not match those in the written BLB file.

## Warning & Error Log Messages ##
Detailed explanations of the warning and error messages logged by the program and directions on how to solve the associated issues.
In the messages listed in this section the `#` character is used to represent a variable numerical value.
Text in `code tags` describes a variable alphanumeric value, commonly the name of a Blender object.

### Warnings ###
Warning log messages can be ignored as the issues are automatically corrected, but the resulting brick may not behave or look as excepted.
It is recommended to manually adjust the brick until no warning messages are present in the output log.
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW000</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Calculated bounds have a non-integer size <code>#</code> <code>#</code> <code>#</code>, rounding up.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>No <a href="#definition-objects-bounds">bounds object</a> was defined and the <a href="#def-aabb">axis-aligned bounding box</a> calculated from the <a href="#def-visible-object"visible objects</a> has non-integer dimensions when converted to brick space.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Brick dimensions of the calculated bounding box will be rounded up to ensure that <a href="#definition-objects-collision">collision cuboids</a> (if any) still fit within the bounds.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td><ol>
			<li><strong>Recommended:</strong> Manually define a bounds object.</li>
			<li>Manually ensure that the <a href="#def-visible-object">visible objects</a> of your brick <a href="#def-model">model</a> form an <a href="#def-aabb">axis-aligned bounding box</a> that has a valid size for a brick.</li>
		</ol></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW001</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Defined bounds have a non-integer size <code>#</code> <code>#</code> <code>#</code>, rounding to a precision of <code>#</code>.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The axis-aligned bounding box calculated from the defined <a href="#definition-objects-bounds">bounds object</a> has non-integer dimensions as a brick.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The brick dimensions will be rounded to the specified precision.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that the defined bounds object aligns with the brick grid.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW002</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick name was supposed to be in the bounds definition object but no such object exists, file name used instead.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The "Brick Name(s) from" <a href="#export-properties">export property</a> (either in <a href="#brick-name-from-single-export">single</a> or <a href="#brick-names-from-multiple-export">multiple</a> brick export mode) value was set to <strong>Bounds</strong> but no manually defined <a href="#definition-objects-bounds">bounds object</a> was found.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The file name specified in the export dialog is used as the name of the BLB file instead.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Create a bounds object and in the name of the <a href="#def-object">object</a> separate the name of the BLB file from the bounds <a href="#definition-tokens">definition token</a> with a whitespace character.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW003</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick name was supposed to be in the bounds definition object but no name (separated with a space) was found after the definition token, file name used instead.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The "Brick Name(s) from" <a href="#export-properties">export property</a> (either in <a href="#brick-name-from-single-export">single</a> or <a href="#brick-names-from-multiple-export">multiple</a> brick export mode) value was set to <strong>Bounds</strong> but no string was found after the bounds <a href="#definition-tokens">definition token</a> in the name of the <a href="#definition-objects-bounds">bounds object</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The file name specified in the export dialog is used as the name of the BLB file instead.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Separate the name of the BLB file from the bounds definition token with a whitespace character, such as a space.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW004</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>No brick grid definitions found. Full cuboid brick grid may be undesirable.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>There are no <a href="#defining-brick-grid">brick grid definition objects</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>A full block brick grid will be generated.
		Brick will act as if it were a basic cuboid brick of that size.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Create brick grid definitions for the <a href="#def-model">model</a>.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW005</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp><code>#</code> brick grid definition(s) found but was/were not processed. Full cuboid brick grid may be undesirable.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>An error occurred for all <a href="#defining-brick-grid">brick grid definition objects</a> when converting into a brick placement rule.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>A full block brick grid will be generated.
		Brick will act as if it were a basic cuboid brick of that size.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Create valid brick grid definitions for the <a href="#def-model">model</a>.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW006</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp><code>#</code> collision definition(s) found but was/were not processed.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>An error occurred for all <a href="#definition-objects-collision">collision definition objects</a> when calculating their dimensions.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The fallback collision will be used.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td><ol>
			<li>Manually define valid collision objects.</li>
			<li>Enable the Calculate Collision export property.</li>
		</ol></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW007</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>No brick bounds definition found. Calculated brick size may be undesirable.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>Brick did not have a <a href="#definition-objects-bounds">bounds definition object</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The axis-aligned bounding box of all <a href="#def-visible-object">visible objects</a> will rounded to the nearest brick dimensions and used as the brick bounds.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Create a bounds definition object.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW008</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Object '<code>object name</code>' has <code>#</code> vertex color layers, only using the first.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The <a href="#def-object">object</a> had more than one <a href="#vertex-colors">vertex color layer</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Only the first vertex color layer is used.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Delete the additional vertex color layers.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW009</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Face has UV coordinates but no brick texture was set in the material name, using SIDE by default.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The material assigned to a face had no <a href="#brick-textures">brick texture</a> defined but the face had UV coordinates.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The <code>side</code> brick texture is used for the face.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Manually define brick textures in the names of the materials that are assigned to UV mapped faces.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW010</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>No alpha value set in vertex color layer name, using 1.0.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The color defined in the <a href="#vertex-colors">vertex color layer</a> did not contain an alpha value.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Alpha of <code>1.0</code> is used resulting in an opaque color.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Define the alpha value in the vertex color layer name.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW011</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp><code>#</code> triangles converted to quads.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#def-mesh">mesh</a> contained a triangle.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The triangle is forcefully converted into a quad by copying the first vertex and using that as the last vertex of a quad.
		This conversion has three different outcomes:
		<ul>
			<li>If flat shading is used for the face there is no change visually and the face will look like a triangle in game.</li>
			<li>If the face and adjacent connected faces are planar and smooth shading is used there are no visual anomalies.</li>
			<li>If the face and adjacent connected faces are <em>not planar</em> and smooth shading is used there may be shading errors.</li>
		</ul></td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Do not use triangles in any <a href="#def-mesh">meshes</a>.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW012</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp><code>#</code> n-gons skipped.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#def-mesh">mesh</a> contained a <a href="#def-face">face</a> made from more than 4 vertices.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Faces made from more than 4 vertices are not exported.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Manually rebuild faces made from more than 4 vertices using quads.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBW013</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Precision has too many decimal digits, using 16 instead.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The precision value set in the <a href="#precision">Precision</a> property had more than 16 decimal digits.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>If <a href="#pretty-print">Pretty Print</a> is disabled the number of decimal digits written to the BLB file is clamped to 16.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Only write up to 16 decimal places in the <a href="#precision">Precision</a> value.</td>
	</tr>
</table>

### Errors ###
Errors are separated into two categories: fatal and non-fatal errors.
* Fatal errors cause the program execution to stop as there is insufficient or incorrect input data to process into a Blockland brick.
* Non-fatal errors occur when the exporter attempts to do something (due to invalid input data) that would have caused an error when loading or using the exported brick in game.
Alternatively the user has attempted to do something that is explicitly not allowed by the exporter or would lead to a mathematical error.

It is recommended to manually adjust the brick until no error messages are present in the output log.

#### Fatal Errors ####
Fatal errors always lead to the program execution stopping.
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF000</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>When exporting multiple bricks in separate layers, a bounds definition object must exist in every layer. It is also used to provide a name for the brick.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The following <a href="#export-properties">export properties</a> are set:
			<table>
				<thead>
					<tr>
						<th>Property</th>
						<th>Value</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td><a href="#bricks-to-export">Bricks to Export</a></td>
						<td>Multiple</td>
					</tr>
					<tr>
						<td><a href="#brick-names-from-multiple-export">Brick Names from (Multiple Export)</a></td>
						<td>Bounds</td>
					</tr>
					<tr>
						<td><a href="#bricks-defined-by-multiple-export">Bricks Defined by (Multiple Export)</a></td>
						<td>Layers</td>
					</tr>
				</tbody>
			</table>
			And a visible layer did not contain a <a href="#definition-objects-bounds">bounds definition object</a>.
		</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>In the interest of promoting good workflow practices this is considered a fatal error instead of automatically naming the brick by the index of the layer it is contained in.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that there is exactly one valid bounds definition object in every visible layer.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF001</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>When exporting multiple bricks in separate layers, the brick name must be after the bounds definition token (separated with a space) in the bounds definition object name.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The following <a href="#export-properties">export properties</a> are set:
			<table>
				<thead>
					<tr>
						<th>Property</th>
						<th>Value</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td><a href="#bricks-to-export">Bricks to Export</a></td>
						<td>Multiple</td>
					</tr>
					<tr>
						<td><a href="#brick-names-from-multiple-export">Brick Names from (Multiple Export)</a></td>
						<td>Bounds</td>
					</tr>
					<tr>
						<td><a href="#bricks-defined-by-multiple-export">Bricks Defined by (Multiple Export)</a></td>
						<td>Layers</td>
					</tr>
				</tbody>
			</table>
			And a <a href="#definition-objects-bounds">bounds definition object</a> name did not contain the name of the brick.
		</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>In the interest of promoting good workflow practices this is considered a fatal error instead of automatically naming the brick by the index of the layer it is contained in.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that each bounds definition object contains the name of that brick.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF002</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Unable to store UV coordinates in object '<code>object name</code>' while it is in edit mode.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The <a href="#store-uvs">Store UVs</a> property is enabled and the exporter attempted to write UV coordinates to a Blender <a href="#def-object">object</a> that is currently in edit mode.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>The authors have not bothered to find a way to automatically disable and re-enable the edit mode.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Confirm that you are not in the edit object interaction mode by changing to the <strong>Object Mode</strong> in the 3D viewport.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF003</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick has no volume, brick could not be rendered in-game.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The <a href="#definition-objects-bounds">bounds definition object</a> or the automatically calculated axis-aligned bounding box of the brick was smaller than 1 brick on one or more axis.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>A brick size cannot be zero on any axis.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td><ul>
		<li><strong>Recommended:</strong> Ensure that the manually defined <a href="#definition-objects-bounds">bounds definition object</a> is larger than a 1x1f plate brick.</li>
		<li>Ensure that the <a href="#def-visible-object">visible objects</a> of the brick form an <a href="#def-aabb">axis-aligned bounding box</a> that is larger than a 1x1f plate brick.</li>
		</ul></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF004</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick size (<code>#</code>x<code>#</code>x<code>#</code>) exceeds the maximum brick size of 64 wide 64 deep and 256 plates tall.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The <a href="#definition-objects-bounds">bounds definition object</a> or the automatically calculated axis-aligned bounding box of the brick is larger than maximum brick size supported by Blockland.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>The maximum size of a single Blockland brick is 64 plates wide 64 plates deep and 256 plates tall.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Make your brick bounds smaller, while keeping in mind the rules regarding other <a href="#definition-objects">definition objects</a>.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF005</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>No faces to export.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>None of the <a href="#def-visible-object"visible objects</a> had any faces.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Creating a brick with no visible faces is pointless.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that there is at least one face to export.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF006</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>No objects to export.</samp></td>
	</tr>
	<tr>
		<th>Causes</th>
		<td>Depends on the values of various <a href="#export-properties">export properties</a>.
			<table>
				<thead>
					<tr>
						<th><a href="#bricks-to-export">Bricks to Export</a></th>
						<th><a href="#export-only-single-export">Export Only (Single Export)</a></th>
						<th>Cause</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td rowspan="3">Single</td>
						<td>Selection</td>
						<td>No <a href="#def-object">objects</a> were selected.
						Selected objects have an orange outline.</td>
					</tr>
					<tr>
						<td>Layers</td>
						<td>There are no objects in the currently visible layers.</td>
					</tr>
					<tr>
						<td>Scene</td>
						<td>None of the layers in the current scene contained any objects.</td>
					</tr>
				</tbody>
			</table>
			<table>
				<thead>
					<tr>
						<th><a href="#bricks-to-export">Bricks to Export</a></th>
						<th><a href="#export-bricks-in-multiple-export">Export Bricks in (Multiple Export)</a></th>
						<th><a href="#bricks-defined-by-multiple-export">Bricks Defined by (Multiple Export)</a></th>
						<th>Cause</th>
					</tr>
				</thead>
					<tr>
						<td rowspan="4">Multiple</td>
						<td rowspan="2">Layers</td>
						<td>Groups</td>
						<td>None of the groups in the current scene had any <a href="#def-object">objects</a> in the visible layers.</td>
					</tr>
					<tr>
						<td>Layers</td>
						<td>None of the visible layers contained any objects.</td>
					</tr>
					<tr>
						<td rowspan="2">Scene</td>
						<td>Groups</td>
						<td>None of the groups in the current scene contained any objects.</td>
					</tr>
					<tr>
						<td>Layers</td>
						<td>None of the layers in the current scene contained any objects.</td>
					</tr>
				</tbody>
			</table>
		</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>No data to export, nothing to do.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td>Depends on the values of various <a href="#export-properties">export properties</a>.
			<table>
				<thead>
					<tr>
						<th><a href="#bricks-to-export">Bricks to Export</a></th>
						<th><a href="#export-only-single-export">Export Only (Single Export)</a></th>
						<th>Solution</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td rowspan="3">Single</td>
						<td>Selection</td>
						<td>Select some objects.</td>
					</tr>
					<tr>
						<td>Layers</td>
						<td>Select one or more layers with objects.</td>
					</tr>
					<tr>
						<td>Scene</td>
						<td>Add <a href="#def-object">objects</a> to a layer in the scene or check that you are not in the wrong scene.</td>
					</tr>
				</tbody>
			</table>
			<table>
				<thead>
					<tr>
						<th><a href="#bricks-to-export">Bricks to Export</a></th>
						<th><a href="#export-bricks-in-multiple-export">Export Bricks in (Multiple Export)</a></th>
						<th><a href="#bricks-defined-by-multiple-export">Bricks Defined by (Multiple Export)</a></th>
						<th>Solution</th>
					</tr>
				</thead>
					<tr>
						<td rowspan="4">Multiple</td>
						<td rowspan="2">Layers</td>
						<td>Groups</td>
						<td>Ensure that your groups have <a href="#def-object">objects</a> assigned to them and that you have selected layers with objects in them.</td>
					</tr>
					<tr>
						<td>Layers</td>
						<td>Select layers with objects.</td>
					</tr>
					<tr>
						<td rowspan="2">Scene</td>
						<td>Groups</td>
						<td>Add objects to a group in the current scene.</td>
					</tr>
					<tr>
						<td>Layers</td>
						<td>Add objects to a layer in the scene or check that you are not in the wrong scene.</td>
					</tr>
				</tbody>
			</table>
		</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF007</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Two or more brick grid definitions had the same priority.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>Two or more <a href="#custom-definition-tokens">user defined</a> <a href="#defining-brick-grid">brick grid definition tokens</a> had the same priority number.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>The user-intended priority order of the tokens cannot be automatically determined.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that all custom brick grid definition tokens have a unique priority number.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF008</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>No groups to export in the current scene.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The following <a href="#export-properties">export properties</a> are set:
			<table>
				<thead>
					<tr>
						<th>Property</th>
						<th>Value</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td><a href="#bricks-to-export">Bricks to Export</a></td>
						<td>Multiple</td>
					</tr>
					<tr>
						<td><a href="#bricks-defined-by-multiple-export">Bricks Defined by (Multiple Export)</a></td>
						<td>Groups</td>
					</tr>
				</tbody>
			</table>
			And the current scene does not contain any groups with <a href="#def-object">objects</a> in visible layers.
		</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>No data to export, nothing to do.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>When exporting multiple bricks in groups, ensure that there are groups to export.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF009</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Nothing to export in the visible layers of the current scene.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The following <a href="#export-properties">export properties</a> are set:
			<table>
				<thead>
					<tr>
						<th>Property</th>
						<th>Value</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td><a href="#bricks-to-export">Bricks to Export</a></td>
						<td>Multiple</td>
					</tr>
					<tr>
						<td><a href="#bricks-defined-by-multiple-export">Bricks Defined by (Multiple Export)</a></td>
						<td>Layers</td>
					</tr>
				</tbody>
			</table>
			And the current scene does not contain any <a href="#def-object">objects</a> in visible layers.
		</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>No data to export, nothing to do.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>When exporting multiple bricks in groups, ensure that there are groups to export.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBF010</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Invalid floating point value given for floating point precision property.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The <a href="#def-string">string</a> specified in the <a href="#precision">Precision</a> property was not a numerical value.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>The numerical values that are <a href="#rounded-values">rounded</a> to combat floating point inaccuracies cannot be rounded unless the floating point precision is set.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Write a numerical value as the <a href="#precision">Precision</a> property.</td>
	</tr>
</table>

#### Non-Fatal Errors ####
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE000</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick grid definition object '<code>object name</code>' has vertices outside the calculated brick bounds. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#defining-brick-grid">brick grid definition object</a> had vertices outside the automatically calculated brick bounds.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Blockland does not allow brick grid definitions outside the bounds of a brick.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The brick grid definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td><ul>
		<li><strong>Recommended:</strong> Manually create a <a href="#definition-objects-bounds">bounds definition object</a> that properly fits around the defined brick grid.</li>
		<li>Ensure that the specified brick grid definition object is fully contained within the <a href="#def-aabb">axis-aligned bounding box</a> of the <a href="#def-visible-object"visible objects</a>.</li>
		</ul></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE001</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick grid definition object '<code>object name</code>' has vertices outside the bounds definition object '<code>object name</code>'. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#defining-brick-grid">brick grid definition object</a> had vertices outside the <a href="#definition-objects-bounds">bounds object</a>.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Blockland does not allow brick grid definitions outside the bounds of a brick.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The brick grid definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td><ul>
		<li>Ensure that the specified brick grid definition object is fully contained within the bounds object.</li>
		<li>Make the bounds definition object larger.</li>
		</ul></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE002</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Brick grid definition object '<code>object name</code>' has no volume. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The axis-aligned bounding box of a <a href="#defining-brick-grid">brick grid definition object</a> was either a plane or a point.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>A brick grid definition with no volume does not produce any brick placement rules when calculating the brick grid.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The brick grid definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that the specified brick grid definition object is not a point or a plane and has some volume.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE003</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp><code>#</code> collision cuboids defined but 10 is the maximum, only using the first 10.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>More than 10 <a href="#definition-objects-collision">collision definition objects</a> were found.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>A BLB file may have a maximum of 10 collision boxes.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Only the 10 oldest <a href="#def-object">objects</a> marked as collision definitions will be used.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Delete the additional collision definition objects.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE004</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Collision definition object '<code>object name</code>' has less than 2 vertices. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#definition-objects-collision">collision definition object</a> had 1 or 0 vertices.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>At least two points are required to specify a volume in three-dimensional space.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The specified collision definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that the specified collision definition object has at least 2 vertices.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE005</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Collision definition object '<code>object name</code>' has no volume. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The axis-aligned bounding box of a <a href="#definition-objects-collision">collision definition object</a> was either a plane or a point.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>A two-dimensional collision box does nothing in game.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The collision definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Ensure that the specified collision definition object is not a point or a plane and has some volume.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE006</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Collision definition object '<code>object name</code>' has vertices outside the calculated brick bounds. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#definition-objects-collision">collision definition object</a> had vertices outside the automatically calculated brick bounds.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Collision boxes outside the bounds of a brick cause strange behavior in game.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The collision definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td><ul>
		<li><strong>Recommended:</strong> Manually create a <a href="#definition-objects-bounds">bounds definition object</a> that properly fits around the defined collision definition objects.</li>
		<li>Ensure that the specified brick grid definition object is fully contained within the <a href="#def-aabb">axis-aligned bounding box</a> of the <a href="#def-visible-object"visible objects</a>.</li>
		</ul></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE007</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Collision definition object '<code>object name</code>' has vertices outside the bounds definition object '<code>object name</code>'. Definition ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A <a href="#definition-objects-collision">collision definition object</a> had vertices outside the <a href="#definition-objects-bounds">bounds object</a>.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Collision boxes outside the bounds of a brick cause strange behavior in game.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The collision definition object is discarded.</td>
	</tr>
	<tr>
		<th>Solutions</th>
		<td><ul>
		<li>Ensure that the specified collision definition object is fully contained within the bounds object.</li>
		<li>Make the bounds definition object larger.</li>
		</ul></td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE008</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Object '<code>object name</code>' cannot be used to define bounds, must be a mesh.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A non-<a href="#def-mesh-object>mesh object</a> such as a camera had a bounds <a href="#definition-tokens">definition token</a> in its name.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Non-<a href="#def-mesh-object>mesh objects</a> do not contain data that can be used to calculate an <a href="#def-aabb">axis-aligned bounding box</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The specified <a href="#def-object">object</a> is ignored.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Remove the bounds definition token from the name of the object.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE009</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Object '<code>object name</code>' cannot be used to define brick grid, must be a mesh.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A non-<a href="#def-mesh-object>mesh object</a> such as a camera had a brick grid <a href="#definition-tokens">definition token</a> in its name.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Non-<a href="#def-mesh-object>mesh objects</a> do not contain data that can be used to calculate an <a href="#def-aabb">axis-aligned bounding box</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The specified <a href="#def-object">object</a> is ignored.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Remove the brick grid definition token from the name of the object.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE010</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Object '<code>object name</code>' cannot be used to define collision, must be a mesh.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A non-<a href="#def-mesh-object>mesh object</a> such as a camera had a collision <a href="#definition-tokens">definition token</a> in its name.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Non-<a href="#def-mesh-object>mesh objects</a> do not contain data that can be used to calculate an <a href="#def-aabb">axis-aligned bounding box</a>.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The specified <a href="#def-object">object</a> is ignored.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Remove the collision definition token from the name of the object.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE011</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Bounds already defined by '<code>object name</code>', bounds definition '<code>object name</code>' ignored.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>One brick contained more than one <a href="#definition-objects-bounds">bounds definition object</a>.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>Although it is technically possible to calculate the <a href="#def-aabb">axis-aligned bounding box</a> of multiple bounds definitions and use that as the final bounds of the brick a feature like this would be confusing for beginner users and breaks the "what you see is what you get" principle of the exporter.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>The oldest bounds definition object is used and the rest are discarded.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Delete the additional bounds definition objects.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE012</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Multiple brick grid definitions in object '<code>object name</code>', only the first one is used.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>A single <a href="#definition-objects">definition object</a> contained more than one <a href="#defining-brick-grid">brick grid definition token</a>.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>One brick grid definition object may only be used to define one brick placement rule.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Only the first brick grid definition token is used.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Delete the additional brick grid definition tokens.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE013</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>More than 4 color values defined for object '<code>object name</code>', only the first 4 values (RGBA) are used.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>Object name contained more than 4 color values.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>An RGBA <a href="#defining-colors">color</a> is be defined by exactly 4 numerical values: red, green, blue, and alpha.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Only the first 4 numbers are used as color values.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Remove the additional numbers.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE014</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>Object '<code>object name</code>' has <code>#</code> section definitions, only using the first one: <code>section name</code></samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The object had more than one <a href="#defining-quad-sections--coverage">quad section definition token</a>.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>A single face cannot be in multiple quad sorting sections at the same time.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Only the first section definition token is used.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Delete the additional section definition tokens.</td>
	</tr>
</table>
<table>
	<tr>
		<th>Code</th>
		<td>IOBLBE015</td>
	</tr>
	<tr>
		<th>Message</th>
		<td><samp>More than one brick texture name found in material '<code>material name</code>', only using the first one.</samp></td>
	</tr>
	<tr>
		<th>Cause</th>
		<td>The material name contained more than one <a href="#brick-textures">brick texture</a> name.</td>
	</tr>
	<tr>
		<th>Reason</th>
		<td>A single face cannot have multiple brick textures at the same time.</td>
	</tr>
	<tr>
		<th>Effect</th>
		<td>Only the first brick texture name is used.</td>
	</tr>
	<tr>
		<th>Solution</th>
		<td>Delete the additional brick texture names.</td>
	</tr>
</table>

## Contributors ##
- [Nick Smith](https://github.com/qoh) - The original source code for reading, processing, and writing Blender data into the .BLB format.
A majority of his code has been rewritten since.
- [Demian Wright](https://github.com/DemianWright) - Significant extensions and rewrites to Nick's original code and all additional features.

<a name="exporter-fn-1">__*__</a> There's always a footnote, see the issue with [the TOP brick texture](#the-top-brick-texture-has-incorrect-rotation-in-blender).

[:arrow_up: Back to Table of Contents](#table-of-contents)
