#############################################################################
#
# (C) 2021 Cadence Design Systems, Inc. All rights reserved worldwide.
#
# This sample script is not supported by Cadence Design Systems, Inc.
# It is provided freely for demonstration purposes only.
# SEE THE WARRANTY DISCLAIMER AT THE BOTTOM OF THIS FILE.
#
#############################################################################

"""

=================================================================
 POINTWISE TUTORIAL WORKBOOK CHAPTER 16: RE-ENTRY VEHICLE PYTHON
=================================================================
Written by: Cannon DeBardelaben, Pointwise, Inc.

This script completes Chapter 16 of the Pointwise Tutorial workbook; creating
the "Re-Entry Vehicle" mesh using Python instead of Glyph/Tcl.

"""

from pointwise import GlyphClient
from pointwise.glyphapi import *
import os

glf = GlyphClient()
pw = glf.get_glyphapi()

# 16.4 Initialization

pw.Application.reset()

# Variables

# Note: No need to define pi or Deg2Rad, as we can use math.pi and math.radians
conDimAB = 25
conDimBC = 37
conDimCD = 9
conDimDE = 11
conDimEF = 121
dsWall = 0.001
radiusBase = 100.0
radiusNose = 50.0
radiusShoulder = 10.0
shelfLength = 15.0
coneAngle = 45.0
obStagPt = 2.0
obTop = 33.0
obRho = 0.5

# In order to create a balanced grid, opposing edges must have the same
# dimension
conDimGA = conDimEF

# Need to subtract the number of nodes to produce the number of points in an
# edge (since nodes are shared points)
conDimFG = conDimAB + conDimBC + conDimCD + conDimDE - 3

# Angles

# Convert coneAngle to radians
coneAngleRad = math.radians(coneAngle)
sinConeAngle = math.sin(coneAngleRad)
cosConeAngle = math.cos(coneAngleRad)
coneAngleRad2 = coneAngleRad * 0.5
sinConeAngle2 = math.sin(coneAngleRad2)
cosConeAngle2 = math.cos(coneAngleRad2)

# 16.5 Define Nodes

# Note: Use Vector3 instead of lists or tuples
G = Vector3(0, 0, 0)

A = G + Vector3(obStagPt, 0, 0)

B = Vector3(radiusNose * (1 - sinConeAngle), radiusNose * cosConeAngle, 0)

C = Vector3(0, 0, 0)
C.y = radiusBase - radiusShoulder * (1.0 - cosConeAngle)
C.x = B.x + (C.y - B.y) * cosConeAngle / sinConeAngle

D = Vector3(0, 0, 0)
D.x = C.x + radiusShoulder * sinConeAngle
D.y = radiusBase

E = Vector3(0, 0, 0)
E.x = D.x + shelfLength
E.y = radiusBase

F = E + Vector3(0, obTop, 0)

H = Vector3(0, 0, 0)
H.y = F.y * 0.5
H.x = (F.x / F.y**2) * H.y**2

I = Vector3(0, 0, 0)
I.x = A.x + radiusNose * (1 - math.cos(0.5 * math.radians(90 - coneAngle)))
I.y = radiusNose * math.sin(0.5 * math.radians(90 - coneAngle))

J = Vector3(0, 0, 0)
J.x = C.x + radiusShoulder * (sinConeAngle - sinConeAngle2)
J.y = radiusBase - radiusShoulder * (1 - cosConeAngle2)

# 16.6 Connector Creation

def createDimCon(segmentType, conDim, ctrlPts):
    """
    Create connector with specified segment type and dimension
      Arguments:
        Segment type, connector dimension, and control points.
      Returns:
        A connector of the given segment type is created and dimensioned.
    """
    with pw.Application.begin("Create") as createCon:
        # Line takes as many segments as supplied and
        # connects them into one curve
        if segmentType == "Line":
            seg = pw.SegmentSpline()
            for x in ctrlPts:
                seg.addPoint(x)
            seg.setSlope("Linear")

        # Circle takes 3 Control Points: Two end points, and a shoulder.
        elif segmentType == "Circle":
            seg = pw.SegmentCircle()
            seg.addPoint(ctrlPts[0])
            seg.addPoint(ctrlPts[1])
            seg.setShoulderPoint(ctrlPts[2])

        # Conic takes 3 Control Points: Two end points, and a shoulder
        elif segmentType == "Conic":
            seg = pw.SegmentConic()
            seg.addPoint(ctrlPts[0])
            seg.addPoint(ctrlPts[1])
            seg.setShoulderPoint(ctrlPts[2])

        else:
            raise GlyphError("", "Invalid segmentType: {}".format(segmentType))

    con = pw.Connector()
    con.addSegment(seg)
    con.setDimension(conDim)

    return con

con_AB = createDimCon("Circle", conDimAB, [A, B, I])
con_BC = createDimCon("Line", conDimBC, [B, C])
con_CD = createDimCon("Circle", conDimCD, [C, D, J])
con_DE = createDimCon("Line", conDimDE, [D, E])
con_EF = createDimCon("Line", conDimEF, [E, F])
con_FG = createDimCon("Conic", conDimFG, [F, G, H])
con_GA = createDimCon("Line", conDimGA, [G, A])

# 16.7 Adjusting Connector Distribution

con_EF.getDistribution(1).setBeginSpacing(dsWall)
con_GA.getDistribution(1).setEndSpacing(dsWall)
generalDistFG = pw.DistributionGeneral([con_AB, con_BC, con_CD, con_DE])
con_FG.setDistribution(1, generalDistFG)

# 16.8 Domain Creation

with pw.Application.begin("Create") as creator:
    # Note: Use python context management to automatically end or abort the mode
    try:
        # Edge has 79 pts
        edge_AE = pw.Edge.createFromConnectors([con_AB, con_BC, con_CD, con_DE])

        # Edge has 121 pts
        edge_EF = pw.Edge.createFromConnectors([con_EF])

        # Edge has 79 pts
        edge_FG = pw.Edge.createFromConnectors([con_FG])

        # Edge has 121 pts
        edge_GA = pw.Edge.createFromConnectors([con_GA])

        dom_A = pw.DomainStructured()

        # Opposing Edges are balanced
        for edge in [edge_AE, edge_EF, edge_FG, edge_GA]:
            dom_A.addEdge(edge)

    except:
        # Prints to Pointwise Messages Window
        glf.puts("Domain assembly failed")
        # Re-raising the exception aborts the mode
        raise

    else:
        glf.puts("Domain assembly successful")

# 16.9 Solve Domain

with pw.Application.begin("EllipticSolver", dom_A) as solveDom:
    dom_A.setEllipticSolverAttribute("EdgeAngleBlend", "Linear", edge = 3)
    solveDom.run(20)

# 16.10 Extrude Block

blk_A = pw.BlockStructured()
face_1 = pw.FaceStructured.createFromDomains(dom_A)
blk_A.addFace(face_1)

with pw.Application.begin("ExtrusionSolver", blk_A) as extrudeBlk:
    try:
        blk_A.setExtrusionSolverAttribute("Mode", "Rotate")
        blk_A.setExtrusionSolverAttribute("RotateAxisStart", A)
        blk_A.setExtrusionSolverAttribute("RotateAxisEnd", G)
        blk_A.setExtrusionSolverAttribute("RotateAngle", 90)
        extrudeBlk.run(20)
    except:
        glf.puts("Block extrusion failed")
        raise

# 16.11 Export Grid

# Get directory of script
scriptDir = os.path.dirname(os.path.realpath(__file__))
gridName = "reentryVeh.x"

# Set file location and file name of exported grid
finalPath = os.path.join(scriptDir, gridName)

# Export Grid
pw.Grid.export(blk_A, finalPath, type = "PLOT3D")


#############################################################################
#
# This file is licensed under the Cadence Public License Version 1.0 (the
# "License"), a copy of which is found in the included file named "LICENSE",
# and is distributed "AS IS." TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE
# LAW, CADENCE DISCLAIMS ALL WARRANTIES AND IN NO EVENT SHALL BE LIABLE TO
# ANY PARTY FOR ANY DAMAGES ARISING OUT OF OR RELATING TO USE OF THIS FILE.
# Please see the License for the full text of applicable terms.
#
#############################################################################
