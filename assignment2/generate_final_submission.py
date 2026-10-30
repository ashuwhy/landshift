"""Build the Assignment 2 submission ZIP.

The class diagram and the XMI both come from the Enterprise Architect project
(output/ea/Murakata_Sankrail_EA_Project.qea): the diagram PDF is EA's
"Print to PDF" of the class diagram and the XMI is EA's XMI 2.1 export of the
model package with diagrams. This script only writes the short write-up and
packs the three files.
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(r"C:\Desktop\landshift\assignment2")
EA_DIR = ROOT / "output" / "ea"
PDF_DIR = ROOT / "output" / "pdf"
SUBMISSION_DIR = ROOT / "final_submission"
PDF_DIR.mkdir(parents=True, exist_ok=True)
SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

EA_DIAGRAM_PDF = EA_DIR / "Murakata_Sankrail_UML_Class_Diagram_EA.pdf"
EA_XMI_FILE = EA_DIR / "Murakata_Sankrail_UML_Model_EA_export.xmi"
WRITEUP_PDF = PDF_DIR / "Murakata_Sankrail_Class_Diagram_WriteUp.pdf"
ZIP_FILE = SUBMISSION_DIR / "Group_08_Assignment_2_Submission.zip"

MEMBERS = "Group 08: Ashutosh Sharma (23CS10005), Krishnkant Sahu (23CS10035), Sanskar Sovitkar (24CS10131)"

# Same text as WriteUp.md; keep the two in step.
WRITEUP = [
    (None, [
        "For Assignment 1 we mapped Murakata and Sankrail in QGIS using nine shapefile layers: boundary, bareland, cropland, drainage, forest, landmarks, roads, settlement and waterbody. For this assignment we turned that project into a UML class diagram in Enterprise Architect. It has 15 classes and 9 enumerations, and everything in it comes from the shapefiles and QML style files we submitted last time.",
    ]),
    ("The project and its layers", [
        "At the top is GISProject, which stands for the QGIS project itself. Each shapefile is a MapLayer, so the project has exactly nine of them. We drew this as a composition (filled diamond) because a layer only makes sense as part of the project. A MapLayer then holds the features stored in its shapefile. For that link we used an aggregation (open diamond) with 0..* on the feature side, since a layer can hold any number of features, including none.",
    ]),
    ("Features", [
        "We grouped the features by geometry, since that is the first thing every shapefile fixes. SpatialFeature is the abstract parent and holds the geometry and an id. The id is optional ([0..1]) because the boundary layer has no id field. Below it are three abstract classes: PolygonFeature, PointFeature and LineFeature. Seven layers are polygons: StudyArea (our name for the boundary), Bareland, Cropland, Drainage, Forest, Settlement and Waterbody. Landmarks are points and roads are lines.",
        "We kept the attribute names exactly as they are in the DBF files, including cut-off ones like forest_typ, waterbody_ and construct_. Shapefile field names can only be ten characters long, and leaving them unchanged makes it easy to check the diagram against the attribute tables. Cropland has no thematic field, so it only has what it inherits. The drainage shapefile has no features saved in it, so for Drainage we went by its field definition and its QML style.",
    ]),
    ("Categories", [
        "The enumerations come from the QML styles. We listed every category each style defines, not only the ones that show up in our data. That is why LandmarkType is so long: the landmarks style has 33 categories, and our eight landmark points use five of them (temple, temple_tribal, shop, playground and studio). ConstructionMaterial is the exception. The roads style is only categorised by road_type, so we took its two values, metal and non-metal, from the roads attribute table. GeometryType just lists the three geometry kinds.",
    ]),
    ("What we left out", [
        "We thought about adding links between features, for example a road serving a settlement. The layers don't share any keys, though, so nothing in the data supports links like that. They are really spatial relationships, which you would work out from the geometry with operations like intersects() and contains() rather than store as associations.",
    ]),
    ("Files", [
        "The class diagram PDF was exported from Enterprise Architect. The XMI file is EA's XMI 2.1 export of the same model, with the diagram layout, so it can be imported back into EA. A note on the diagram lists where the classes and values came from.",
    ]),
]


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


def make_writeup_pdf():
    page_width, page_height = A4
    c = canvas.Canvas(str(WRITEUP_PDF), pagesize=A4, pageCompression=1)
    c.setTitle("Assignment 2 - UML Class Diagram (Group 08)")
    c.setAuthor("Ashutosh Sharma, Krishnkant Sahu, Sanskar Sovitkar")
    grey = colors.HexColor("#555555")
    margin = 22 * mm
    y = page_height - 22 * mm
    body_font, body_size, body_leading = "Times-Roman", 10.5, 14
    usable_width = page_width - 2 * margin

    c.setFont("Times-Bold", 16)
    c.drawString(margin, y, "Assignment 2 - UML Class Diagram")
    y -= 16
    c.setFont("Times-Roman", 11)
    c.drawString(margin, y, "GIS of Murakata and Sankrail (from our Assignment 1 QGIS project)")
    y -= 14
    c.setFont("Times-Italic", 10)
    c.setFillColor(grey)
    c.drawString(margin, y, MEMBERS)
    y -= 9
    c.setStrokeColor(grey)
    c.setLineWidth(0.4)
    c.line(margin, y, page_width - margin, y)
    y -= 18

    def paragraph(value):
        nonlocal y
        c.setFont(body_font, body_size)
        c.setFillColor(colors.black)
        for line_value in wrap_text(c, value, usable_width, body_font, body_size):
            c.drawString(margin, y, line_value)
            y -= body_leading
        y -= 5

    def heading(value):
        nonlocal y
        y -= 4
        c.setFillColor(colors.black)
        c.setFont("Times-Bold", 11.5)
        c.drawString(margin, y, value)
        y -= 15

    for title, paragraphs in WRITEUP:
        if title:
            heading(title)
        for value in paragraphs:
            paragraph(value)
    c.save()


def create_zip():
    with ZipFile(ZIP_FILE, "w", ZIP_DEFLATED) as archive:
        archive.write(EA_DIAGRAM_PDF, "Murakata_Sankrail_UML_Class_Diagram.pdf")
        archive.write(EA_XMI_FILE, "Murakata_Sankrail_UML_Model.xmi")
        archive.write(WRITEUP_PDF, WRITEUP_PDF.name)


if __name__ == "__main__":
    for required in (EA_DIAGRAM_PDF, EA_XMI_FILE):
        if not required.exists():
            raise SystemExit(f"Missing Enterprise Architect export: {required}")
    make_writeup_pdf()
    create_zip()
    print(WRITEUP_PDF)
    print(ZIP_FILE)
