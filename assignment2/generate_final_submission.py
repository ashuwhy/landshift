"""Build the Assignment 2 deliverables from the submitted Assignment 1 GIS data."""

from pathlib import Path
from shutil import copy2
from xml.etree import ElementTree as ET
from xml.dom import minidom
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(r"C:\Desktop\landshift\assignment2")
PDF_DIR = ROOT / "output" / "pdf"
SUBMISSION_DIR = ROOT / "final_submission"
PDF_DIR.mkdir(parents=True, exist_ok=True)
SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

DIAGRAM_PDF = PDF_DIR / "Murakata_Sankrail_UML_Class_Diagram.pdf"
WRITEUP_PDF = PDF_DIR / "Murakata_Sankrail_Class_Diagram_WriteUp.pdf"
XMI_FILE = SUBMISSION_DIR / "Murakata_Sankrail_UML_Model.xmi"
EA_XMI_FILE = ROOT / "output" / "ea" / "Murakata_Sankrail_UML_Model_EA_export.xmi"
ZIP_FILE = SUBMISSION_DIR / "Group_08_Assignment_2_Submission.zip"


CLASSES = {
    "GISProject": {
        "attrs": [("projectName", "String"), ("crs", "String"), ("sourceDirectory", "URI")],
        "ops": ["loadLayer(path : URI)", "exportMap(format : String)"],
    },
    "MapLayer": {
        "attrs": [("layerName", "String"), ("sourceFile", "URI"), ("geometryType", "GeometryType"), ("featureCount", "Integer")],
        "ops": ["setStyle()", "filter(expression : String)"],
    },
    "SpatialFeature": {
        "attrs": [("id", "Integer [0..1]"), ("geometry", "Geometry")],
        "ops": ["intersects(other : SpatialFeature) : Boolean"],
        "abstract": True,
    },
    "PolygonFeature": {
        "attrs": [],
        "ops": ["calculateArea() : Decimal", "contains(point : PointFeature) : Boolean"],
        "abstract": True,
        "parent": "SpatialFeature",
    },
    "PointFeature": {
        "attrs": [],
        "ops": ["coordinates() : Point"],
        "abstract": True,
        "parent": "SpatialFeature",
    },
    "LineFeature": {
        "attrs": [],
        "ops": ["calculateLength() : Decimal"],
        "abstract": True,
        "parent": "SpatialFeature",
    },
    "StudyArea": {
        "attrs": [("NAME", "String"), ("VILL_NAME", "String"), ("AREA", "Decimal")],
        "ops": [],
        "parent": "PolygonFeature",
    },
    "Bareland": {"attrs": [("bareland_t", "BarelandType")], "ops": [], "parent": "PolygonFeature"},
    "Cropland": {"attrs": [], "ops": [], "parent": "PolygonFeature"},
    "Forest": {"attrs": [("forest_typ", "ForestType")], "ops": [], "parent": "PolygonFeature"},
    "Settlement": {"attrs": [("settlement", "SettlementType")], "ops": [], "parent": "PolygonFeature"},
    "Waterbody": {"attrs": [("waterbody_", "WaterbodyType")], "ops": [], "parent": "PolygonFeature"},
    "Drainage": {"attrs": [("drainage_t", "DrainageType")], "ops": [], "parent": "PolygonFeature"},
    "Landmark": {"attrs": [("landmark_t", "LandmarkType")], "ops": [], "parent": "PointFeature"},
    "Road": {"attrs": [("road_type", "RoadType"), ("construct_", "ConstructionMaterial")], "ops": [], "parent": "LineFeature"},
}

ENUMERATIONS = {
    "GeometryType": ["Point", "LineString", "Polygon"],
    "BarelandType": ["grassland", "barren", "scrubland", "sand"],
    "ForestType": ["tree_area", "tree_stlmt", "tree_croplnd"],
    "SettlementType": ["residential", "commercial"],
    "WaterbodyType": ["pond_stlmt", "pond_cropland", "pond_forest", "lake", "river"],
    "DrainageType": ["canal", "drain"],
    "RoadType": ["highway", "inroad", "household_lane"],
    "ConstructionMaterial": ["metal", "non-metal"],
    "LandmarkType": ["temple", "playground", "shop", "studio", "temple_tribal"],
}


def wrap_text(c, text, max_width, font="Helvetica", size=10):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_xmi():
    xmi = "http://schema.omg.org/spec/XMI/2.1"
    uml = "http://schema.omg.org/spec/UML/2.1"
    ET.register_namespace("xmi", xmi)
    ET.register_namespace("uml", uml)
    X = f"{{{xmi}}}"

    def element(parent, tag, **attrs):
        converted = {(X + key[4:] if key.startswith("xmi:") else key): str(value) for key, value in attrs.items() if value is not None}
        return ET.SubElement(parent, tag, converted)

    root = ET.Element(X + "XMI", {X + "version": "2.1"})
    element(root, X + "Documentation", exporter="UML XMI generator", exporterVersion="2.1")
    # A UML-namespaced Model also binds the `uml` prefix used by xmi:type,
    # which is required by Enterprise Architect and other XMI importers.
    model = element(root, f"{{{uml}}}Model", **{"xmi:type": "uml:Model", "xmi:id": "MODEL_MURAKATA", "name": "Murakata Sankrail GIS UML Model", "visibility": "public"})

    data_types = element(model, "packagedElement", **{"xmi:type": "uml:Package", "xmi:id": "PKG_TYPES", "name": "Data Types"})
    data_type_ids = {}
    for name in ["String", "Integer", "Decimal", "Boolean", "URI", "Geometry", "Point"]:
        identifier = f"DT_{name.upper()}"
        data_type_ids[name] = identifier
        element(data_types, "packagedElement", **{"xmi:type": "uml:DataType", "xmi:id": identifier, "name": name, "visibility": "public"})

    enum_package = element(model, "packagedElement", **{"xmi:type": "uml:Package", "xmi:id": "PKG_ENUM", "name": "Enumerations"})
    enum_ids = {}
    for enum_name, values in ENUMERATIONS.items():
        enum_id = f"ENUM_{enum_name.upper()}"
        enum_ids[enum_name] = enum_id
        enum = element(enum_package, "packagedElement", **{"xmi:type": "uml:Enumeration", "xmi:id": enum_id, "name": enum_name, "visibility": "public"})
        for index, value in enumerate(values, 1):
            element(enum, "ownedLiteral", **{"xmi:type": "uml:EnumerationLiteral", "xmi:id": f"LIT_{enum_name.upper()}_{index:02}", "name": value})

    project_package = element(model, "packagedElement", **{"xmi:type": "uml:Package", "xmi:id": "PKG_PROJECT", "name": "GIS Project"})
    feature_package = element(model, "packagedElement", **{"xmi:type": "uml:Package", "xmi:id": "PKG_FEATURES", "name": "Spatial Features"})
    class_ids = {name: f"CLS_{name.upper()}" for name in CLASSES}

    def add_class(parent, name, definition):
        attributes = {"xmi:type": "uml:Class", "xmi:id": class_ids[name], "name": name, "visibility": "public"}
        if definition.get("abstract"):
            attributes["isAbstract"] = "true"
        cls = element(parent, "packagedElement", **attributes)
        if definition.get("parent"):
            element(cls, "generalization", **{"xmi:type": "uml:Generalization", "xmi:id": f"GEN_{name.upper()}", "general": class_ids[definition["parent"]]})
        for number, (attribute_name, declared_type) in enumerate(definition.get("attrs", []), 1):
            type_name = declared_type.split()[0]
            type_id = enum_ids.get(type_name, data_type_ids.get(type_name, data_type_ids["String"]))
            property_attrs = {"xmi:type": "uml:Property", "xmi:id": f"ATTR_{name.upper()}_{number:02}", "name": attribute_name, "visibility": "public", "type": type_id}
            if "[0..1]" in declared_type:
                property_attrs.update({"lower": "0", "upper": "1"})
            element(cls, "ownedAttribute", **property_attrs)
        for number, operation in enumerate(definition.get("ops", []), 1):
            op_signature, return_type = operation.rsplit(" : ", 1) if ") : " in operation else (operation, None)
            op_name, raw_parameters = op_signature[:-1].split("(", 1)
            op_id = f"OP_{name.upper()}_{number:02}"
            op_element = element(cls, "ownedOperation", **{"xmi:type": "uml:Operation", "xmi:id": op_id, "name": op_name, "visibility": "public"})
            for parameter_index, raw_parameter in enumerate(filter(None, raw_parameters.split(",")), 1):
                parameter_name, parameter_type = [part.strip() for part in raw_parameter.split(" : ", 1)]
                parameter_classifier = class_ids.get(parameter_type, enum_ids.get(parameter_type, data_type_ids.get(parameter_type, data_type_ids["String"])))
                element(op_element, "ownedParameter", **{"xmi:type": "uml:Parameter", "xmi:id": f"{op_id}_IN_{parameter_index:02}", "name": parameter_name, "direction": "in", "type": parameter_classifier})
            if return_type:
                return_classifier = class_ids.get(return_type, enum_ids.get(return_type, data_type_ids.get(return_type, data_type_ids["String"])))
                element(op_element, "ownedParameter", **{"xmi:type": "uml:Parameter", "xmi:id": f"{op_id}_RETURN", "direction": "return", "type": return_classifier})
        return cls

    add_class(project_package, "GISProject", CLASSES["GISProject"])
    add_class(project_package, "MapLayer", CLASSES["MapLayer"])
    for class_name in CLASSES:
        if class_name not in {"GISProject", "MapLayer"}:
            add_class(feature_package, class_name, CLASSES[class_name])

    relation_package = element(model, "packagedElement", **{"xmi:type": "uml:Package", "xmi:id": "PKG_RELATIONS", "name": "Relationships"})

    def association(identifier, name, first_type, first_role, first_multiplicity, second_type, second_role, second_multiplicity, composition=False, shared=False, aggregation_end="first"):
        association_element = element(relation_package, "packagedElement", **{"xmi:type": "uml:Association", "xmi:id": identifier, "name": name, "visibility": "public"})
        first_lower, first_upper = first_multiplicity
        second_lower, second_upper = second_multiplicity
        first = {"xmi:type": "uml:Property", "xmi:id": identifier + "_END1", "name": first_role, "type": class_ids[first_type], "association": identifier, "lower": first_lower, "upper": first_upper}
        second = {"xmi:type": "uml:Property", "xmi:id": identifier + "_END2", "name": second_role, "type": class_ids[second_type], "association": identifier, "lower": second_lower, "upper": second_upper}
        aggregation = "composite" if composition else "shared" if shared else None
        if aggregation and aggregation_end == "first":
            first["aggregation"] = aggregation
        elif aggregation:
            second["aggregation"] = aggregation
        element(association_element, "ownedEnd", **first)
        element(association_element, "ownedEnd", **second)

    # Association-end types are deliberately oriented by role: GISProject owns
    # the 'layers' end (whose type is MapLayer), and MapLayer owns 'features'.
    association("ASC_PROJECT_LAYERS", "contains", "MapLayer", "layers", ("9", "9"), "GISProject", "project", ("1", "1"), composition=True, aggregation_end="second")
    association("ASC_LAYER_FEATURES", "represents", "SpatialFeature", "features", ("0", "*"), "MapLayer", "layer", ("1", "1"), shared=True, aggregation_end="second")

    raw = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8")
    XMI_FILE.write_bytes(pretty)


def make_diagram_pdf():
    page_width, page_height = landscape(A3)
    c = canvas.Canvas(str(DIAGRAM_PDF), pagesize=(page_width, page_height), pageCompression=1)
    c.setTitle("Murakata Sankrail GIS - UML Class Diagram")
    c.setAuthor("Group 08")

    navy = colors.HexColor("#12355B")
    blue = colors.HexColor("#DDEBF7")
    green = colors.HexColor("#E7F3E8")
    yellow = colors.HexColor("#FFF2CC")
    purple = colors.HexColor("#EDE7F6")
    grey = colors.HexColor("#56616F")

    def ty(y):
        return page_height - y

    def line(x1, y1, x2, y2, color=colors.black, width=1, dash=None):
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(width)
        if dash:
            c.setDash(*dash)
        c.line(x1, ty(y1), x2, ty(y2))
        c.restoreState()

    def text(x, y, value, font="Helvetica", size=8, color=colors.black, align="left"):
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, ty(y), value) if align == "left" else c.drawCentredString(x, ty(y), value)

    def box(x, y, width, title, attrs, ops, fill=colors.white, abstract=False, enum=False):
        # Header, a generously spaced attribute compartment, then operations.
        # The lower padding is intentional: diagrams are often printed at A3/A4,
        # and cramped class boxes are difficult to read in print.
        height = 38 + max(1, len(attrs)) * 11 + (len(ops) * 11 + 7 if ops else 0)
        c.setStrokeColor(navy)
        c.setFillColor(fill)
        c.roundRect(x, ty(y + height), width, height, 4, fill=1, stroke=1)
        c.setFillColor(navy)
        c.roundRect(x, ty(y + 25), width, 25, 4, fill=1, stroke=0)
        if abstract:
            text(x + width / 2, y + 9, "<<abstract>>", "Helvetica-Oblique", 6.5, colors.white, "center")
            text(x + width / 2, y + 19, title, "Helvetica-Bold", 9, colors.white, "center")
        elif enum:
            text(x + width / 2, y + 9, "<<enumeration>>", "Helvetica-Oblique", 6.5, colors.white, "center")
            text(x + width / 2, y + 19, title, "Helvetica-Bold", 8.5, colors.white, "center")
        else:
            text(x + width / 2, y + 16, title, "Helvetica-Bold", 9, colors.white, "center")
        cursor = y + 37
        for name, declared_type in attrs:
            field_text = f"+ {declared_type}" if not name else f"+ {name} : {declared_type}"
            text(x + 6, cursor, field_text, "Helvetica", 7.1)
            cursor += 11
        if not attrs and not ops:
            text(x + 6, cursor, "(no direct attributes)", "Helvetica-Oblique", 7, grey)
            cursor += 11
        if ops:
            line(x, cursor - 4, x + width, cursor - 4, navy, 0.55)
            for operation in ops:
                text(x + 6, cursor + 5, f"+ {operation}", "Helvetica", 7.1)
                cursor += 11
        return (x, y, width, height)

    def enumeration(x, y, width, title, values):
        attrs = [("", value) for value in values]
        return box(x, y, width, title, attrs, [], fill=purple, enum=True)

    def center_top(rect):
        x, y, width, _ = rect
        return x + width / 2, y

    def center_bottom(rect):
        x, y, width, height = rect
        return x + width / 2, y + height

    def center_right(rect):
        x, y, width, height = rect
        return x + width, y + height / 2

    def center_left(rect):
        x, y, _, height = rect
        return x, y + height / 2

    def generalization(child, parent, slot=0, total=1):
        sx, sy = center_top(child)
        px, py, pw, ph = parent
        ex, ey = px + pw * (slot + 1) / (total + 1), py + ph
        line(sx, sy, ex, ey + 9, navy, 1.05)
        c.saveState()
        c.setStrokeColor(navy)
        c.setFillColor(colors.white)
        c.setLineWidth(1.05)
        p = c.beginPath()
        p.moveTo(ex, ty(ey))
        p.lineTo(ex - 5, ty(ey + 9))
        p.lineTo(ex + 5, ty(ey + 9))
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        c.restoreState()

    def diamond(x, y, size=6, color=navy):
        c.saveState()
        c.setStrokeColor(color)
        c.setFillColor(color)
        p = c.beginPath()
        p.moveTo(x, ty(y))
        p.lineTo(x + size, ty(y + size / 2))
        p.lineTo(x, ty(y + size))
        p.lineTo(x - size, ty(y + size / 2))
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        c.restoreState()

    def open_diamond(x, y, size=6, color=navy):
        c.saveState()
        c.setStrokeColor(color)
        c.setFillColor(colors.white)
        p = c.beginPath()
        p.moveTo(x, ty(y))
        p.lineTo(x + size, ty(y + size / 2))
        p.lineTo(x, ty(y + size))
        p.lineTo(x - size, ty(y + size / 2))
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        c.restoreState()

    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(32, ty(33), "UML Class Diagram: GIS Mapping of Murakata, Sankrail")
    c.setFont("Helvetica", 8)
    c.setFillColor(grey)
    c.drawString(32, ty(48), "Assignment 2 | Derived from the submitted Assignment 1 QGIS shapefile schema and QML categories")
    line(32, 55, page_width - 32, 55, navy, 1.2)

    gis = box(40, 78, 180, "GISProject", CLASSES["GISProject"]["attrs"], CLASSES["GISProject"]["ops"], fill=blue)
    layer = box(330, 78, 190, "MapLayer", CLASSES["MapLayer"]["attrs"], CLASSES["MapLayer"]["ops"], fill=blue)
    spatial = box(630, 78, 185, "SpatialFeature", CLASSES["SpatialFeature"]["attrs"], CLASSES["SpatialFeature"]["ops"], fill=yellow, abstract=True)

    polygon = box(300, 255, 185, "PolygonFeature", [], CLASSES["PolygonFeature"]["ops"], fill=yellow, abstract=True)
    point = box(530, 255, 170, "PointFeature", [], CLASSES["PointFeature"]["ops"], fill=yellow, abstract=True)
    linear = box(745, 255, 170, "LineFeature", [], CLASSES["LineFeature"]["ops"], fill=yellow, abstract=True)

    study_area = box(28, 420, 120, "StudyArea", CLASSES["StudyArea"]["attrs"], [], fill=green)
    bareland = box(155, 420, 120, "Bareland", CLASSES["Bareland"]["attrs"], [], fill=green)
    cropland = box(282, 420, 120, "Cropland", [], [], fill=green)
    forest = box(409, 420, 120, "Forest", CLASSES["Forest"]["attrs"], [], fill=green)
    settlement = box(536, 420, 120, "Settlement", CLASSES["Settlement"]["attrs"], [], fill=green)
    waterbody = box(663, 420, 120, "Waterbody", CLASSES["Waterbody"]["attrs"], [], fill=green)
    drainage = box(790, 420, 120, "Drainage", CLASSES["Drainage"]["attrs"], [], fill=green)
    landmark = box(505, 550, 140, "Landmark", CLASSES["Landmark"]["attrs"], [], fill=green)
    road = box(735, 550, 145, "Road", CLASSES["Road"]["attrs"], [], fill=green)

    enum_x1, enum_x2 = 930, 1060
    enumeration(enum_x1, 78, 120, "GeometryType", ENUMERATIONS["GeometryType"])
    enumeration(enum_x2, 78, 125, "BarelandType", ENUMERATIONS["BarelandType"])
    enumeration(enum_x1, 170, 120, "ForestType", ENUMERATIONS["ForestType"])
    enumeration(enum_x2, 170, 125, "SettlementType", ENUMERATIONS["SettlementType"])
    enumeration(enum_x1, 262, 120, "WaterbodyType", ENUMERATIONS["WaterbodyType"])
    enumeration(enum_x2, 262, 125, "DrainageType", ENUMERATIONS["DrainageType"])
    enumeration(enum_x1, 370, 120, "RoadType", ENUMERATIONS["RoadType"])
    enumeration(enum_x2, 370, 125, "ConstructionMaterial", ENUMERATIONS["ConstructionMaterial"])
    enumeration(enum_x1, 462, 255, "LandmarkType", ENUMERATIONS["LandmarkType"])

    # Composition: the filled diamond sits at the GISProject (whole) end.
    sx, sy = center_right(gis)
    ex, ey = center_left(layer)
    diamond(sx + 7, sy - 3)
    line(sx + 13, sy, ex, ey, navy, 1.15)
    text((sx + ex) / 2, min(sy, ey) - 9, "contains", "Helvetica-Oblique", 7.3, navy, "center")
    text(sx + 15, sy - 4, "1", "Helvetica", 7, navy)
    text(ex - 10, ey - 4, "9", "Helvetica", 7, navy)

    # Shared aggregation: MapLayer groups the features represented by its file.
    sx, sy = center_right(layer)
    ex, ey = center_left(spatial)
    open_diamond(sx + 7, sy - 3)
    line(sx + 13, sy, ex, ey, navy, 1.15)
    text((sx + ex) / 2, min(sy, ey) - 9, "represents", "Helvetica-Oblique", 7.3, navy, "center")
    text(sx + 15, sy - 4, "1", "Helvetica", 7, navy)
    text(ex - 24, ey - 4, "0..*", "Helvetica", 7, navy)

    for index, child in enumerate([study_area, bareland, cropland, forest, settlement, waterbody, drainage]):
        generalization(child, polygon, index, 7)
    for index, child in enumerate([polygon, point, linear]):
        generalization(child, spatial, index, 3)
    generalization(landmark, point)
    generalization(road, linear)

    text(32, 706, "Legend", "Helvetica-Bold", 8.5, navy)
    line(32, 714, 65, 714, navy, 1.05)
    text(71, 717, "generalization (inheritance)", "Helvetica", 7.2)
    diamond(255, 711)
    line(261, 714, 292, 714, navy, 1.05)
    text(300, 717, "composition", "Helvetica", 7.2)
    open_diamond(416, 711)
    line(422, 714, 453, 714, navy, 1.05)
    text(461, 717, "shared aggregation", "Helvetica", 7.2)
    text(600, 717, "Yellow = abstract class; green = concrete feature; purple = enumeration", "Helvetica", 7.2)
    text(32, 735, "Traceability: feature-specific attributes retain DBF field names. Categories follow QML styles; LandmarkType lists observed records.", "Helvetica", 7.2, grey)
    text(32, 752, "Nine source layers: boundary, bareland, cropland, drainage, forest, landmarks, roads, settlement, and waterbody. No cross-layer key is present.", "Helvetica", 7.2, grey)
    c.setFont("Helvetica", 6.8)
    c.setFillColor(grey)
    c.drawRightString(page_width - 32, ty(775), "Group 08 | Assignment 2 | Prepared for UML class-diagram submission")
    c.showPage()
    c.save()


def make_writeup_pdf():
    page_width, page_height = A4
    c = canvas.Canvas(str(WRITEUP_PDF), pagesize=A4, pageCompression=1)
    c.setTitle("Murakata Sankrail GIS - Class Diagram Write-up")
    c.setAuthor("Group 08")
    navy = colors.HexColor("#12355B")
    grey = colors.HexColor("#56616F")
    margin = 20 * mm
    y = page_height - 19 * mm
    body_size = 9.1
    body_leading = 12.2
    usable_width = page_width - 2 * margin

    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(page_width / 2, y, "Short Write-up")
    y -= 17
    c.setFont("Helvetica", 11)
    c.drawCentredString(page_width / 2, y, "GIS Class Diagram for Murakata and Sankrail")
    y -= 14
    c.setFont("Helvetica", 8.5)
    c.setFillColor(grey)
    c.drawCentredString(page_width / 2, y, "Assignment 2 | Group 08 | Based on our Assignment 1 QGIS project")
    y -= 10
    c.setStrokeColor(navy)
    c.setLineWidth(0.8)
    c.line(margin, y, page_width - margin, y)
    y -= 7

    def paragraph(value):
        nonlocal y
        c.setFont("Helvetica", body_size)
        c.setFillColor(colors.black)
        for line_value in wrap_text(c, value, usable_width, "Helvetica", body_size):
            c.drawString(margin, y, line_value)
            y -= body_leading
        y -= 2.5

    def heading(value):
        nonlocal y
        y -= 1
        c.setFillColor(navy)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, value)
        y -= 14

    heading("What we modelled")
    paragraph("In Assignment 1, our group made a QGIS map of Murakata and Sankrail. It uses nine shapefile layers: boundary, bareland, cropland, drainage, forest, landmarks, roads, settlement and waterbody. For Assignment 2, we drew a UML class diagram to show how the project and its geographic data fit together. The diagram has 15 classes and nine enumerations.")

    heading("Project and map layers")
    paragraph("We used GISProject for the QGIS project and MapLayer for each shapefile. The project contains nine map layers, one for each source layer. A map layer stores its name, source file, geometry type and feature count. It also represents the spatial features in that file. Keeping these classes separate makes it clear which details belong to the project and which belong to an individual layer.")

    heading("Geographic features")
    paragraph("SpatialFeature is an abstract class for information shared by mapped features, including geometry and an optional identifier. We made the identifier optional because the boundary layer has no ID field. We grouped the feature classes by shape using the abstract classes PolygonFeature, PointFeature and LineFeature. StudyArea, Bareland, Cropland, Drainage, Forest, Settlement and Waterbody are polygon features; Landmark is a point feature; and Road is a line feature.")
    paragraph("Feature attributes keep the field names from the DBF tables, such as NAME, VILL_NAME, AREA, bareland_t, forest_typ, landmark_t and road_type. Cropland has no extra thematic field in the source data, so it has no extra attribute in the diagram.")

    heading("Categories and relationships")
    paragraph("We used nine enumerations for fixed categories in the data, including road type, forest type, waterbody type and construction material. Their values follow the QML category definitions and the values recorded in the shapefiles.")
    paragraph("The filled diamond shows that GISProject contains its nine MapLayer objects. The open diamond shows that a MapLayer can represent many SpatialFeature objects. The shapefiles do not have keys linking records across layers, so we did not add claims such as a road connecting a settlement. Spatial relationships can be checked from the feature geometries when needed.")

    heading("Why we chose this structure")
    paragraph("The diagram follows the data from our Assignment 1 project. It keeps the source field names, groups features by geometry and shows the available categories. The Enterprise Architect XMI file contains the same classes and relationships, along with the saved diagram layout.")

    c.setFont("Helvetica", 7.5)
    c.setFillColor(grey)
    c.drawRightString(page_width - margin, 11 * mm, "Group 08 | Assignment 2")
    c.save()


def create_zip():
    with ZipFile(ZIP_FILE, "w", ZIP_DEFLATED) as archive:
        archive.write(DIAGRAM_PDF, DIAGRAM_PDF.name)
        archive.write(XMI_FILE, XMI_FILE.name)
        archive.write(WRITEUP_PDF, WRITEUP_PDF.name)


if __name__ == "__main__":
    # Prefer EA's full-round-trip export because it preserves the diagram
    # layout. The generated XMI remains a fallback if EA has not been used.
    if EA_XMI_FILE.exists():
        copy2(EA_XMI_FILE, XMI_FILE)
    else:
        make_xmi()
    make_diagram_pdf()
    make_writeup_pdf()
    create_zip()
    print(DIAGRAM_PDF)
    print(XMI_FILE)
    print(WRITEUP_PDF)
    print(ZIP_FILE)
