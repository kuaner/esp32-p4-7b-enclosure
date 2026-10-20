"""Render the actual CAD geometry, without an illustrative image generator."""
from pathlib import Path
import vtk
import numpy as np
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray


def actor_for(shape, color, opacity=1.0):
    vertices, triangles = shape.tessellate(0.18, 0.2)
    points = np.array([v.toTuple() for v in vertices], dtype=float)
    indices = np.asarray(triangles, dtype=np.int64)
    cells = np.column_stack([np.full(len(indices), 3), indices]).ravel()
    vp = vtk.vtkPoints()
    vp.SetData(numpy_to_vtk(points, deep=True))
    vc = vtk.vtkCellArray()
    vc.SetCells(len(indices), numpy_to_vtkIdTypeArray(cells, deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(vp)
    poly.SetPolys(vc)
    normal = vtk.vtkPolyDataNormals()
    normal.SetInputData(poly)
    normal.SetFeatureAngle(40)
    normal.SplittingOn()
    normal.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normal.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*color[:3])
    prop.SetOpacity(opacity)
    prop.SetAmbient(0.3)
    prop.SetDiffuse(0.7)
    prop.SetSpecular(0.23)
    prop.SetSpecularPower(40)
    return actor


def render(items, path, camera=(230, 150, -240), focus=(0,0,12),
           up=(0,1,0), size=(1600,1200), scale=None, projections=None):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.93, 0.95, 0.97)
    renderer.SetUseDepthPeeling(True)
    renderer.SetMaximumNumberOfPeels(100)
    for shape, color, *rest in items:
        renderer.AddActor(actor_for(shape, color, rest[0] if rest else 1.0))
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetAlphaBitPlanes(1)
    win.SetMultiSamples(0)
    win.SetSize(*size)
    win.AddRenderer(renderer)
    cam = renderer.GetActiveCamera()
    cam.SetPosition(*camera)
    cam.SetFocalPoint(*focus)
    cam.SetViewUp(*up)
    cam.ParallelProjectionOn()
    renderer.ResetCamera()
    if scale:
        cam.SetParallelScale(scale)
    else:
        cam.SetParallelScale(cam.GetParallelScale()*1.13)
    renderer.ResetCameraClippingRange()
    win.Render()
    projected={}
    for name,p in (projections or {}).items():
        renderer.SetWorldPoint(*p,1.0)
        renderer.WorldToDisplay()
        xy=renderer.GetDisplayPoint()
        projected[name]=(xy[0],size[1]-xy[1])
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(win)
    capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff()
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(Path(path)))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    win.Finalize()
    return projected
