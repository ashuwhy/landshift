# Short Write-up: GIS Class Diagram for Murakata and Sankrail

**Assignment 2 | Group 08 | Based on our Assignment 1 QGIS project**

## What we modelled

In Assignment 1, our group made a QGIS map of Murakata and Sankrail. It uses nine shapefile layers: boundary, bareland, cropland, drainage, forest, landmarks, roads, settlement and waterbody. For Assignment 2, we drew a UML class diagram to show how the project and its geographic data fit together. The diagram has 15 classes and nine enumerations.

## Project and map layers

We used `GISProject` for the QGIS project and `MapLayer` for each shapefile. The project contains nine map layers, one for each source layer. A map layer stores its name, source file, geometry type and feature count. It also represents the spatial features in that file. Keeping these classes separate makes it clear which details belong to the project and which belong to an individual layer.

## Geographic features

`SpatialFeature` is an abstract class for information shared by mapped features, including geometry and an optional identifier. We made the identifier optional because the boundary layer has no ID field. We grouped the feature classes by shape using the abstract classes `PolygonFeature`, `PointFeature` and `LineFeature`. `StudyArea`, `Bareland`, `Cropland`, `Drainage`, `Forest`, `Settlement` and `Waterbody` are polygon features; `Landmark` is a point feature; and `Road` is a line feature.

Feature attributes keep the field names from the DBF tables, such as `NAME`, `VILL_NAME`, `AREA`, `bareland_t`, `forest_typ`, `landmark_t` and `road_type`. Cropland has no extra thematic field in the source data, so it has no extra attribute in the diagram.

## Categories and relationships

We used nine enumerations for fixed categories in the data, including road type, forest type, waterbody type and construction material. Their values follow the QML category definitions and the values recorded in the shapefiles.

The filled diamond shows that the `GISProject` contains its nine `MapLayer` objects. The open diamond shows that a `MapLayer` can represent many `SpatialFeature` objects. The shapefiles do not have keys linking records across layers, so we did not add claims such as a road connecting a settlement. Spatial relationships can be checked from the feature geometries when needed.

## Why we chose this structure

The diagram follows the data from our Assignment 1 project. It keeps the source field names, groups features by geometry and shows the available categories. The Enterprise Architect XMI file contains the same classes and relationships, along with the saved diagram layout.
