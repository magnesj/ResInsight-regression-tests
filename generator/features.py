"""One regression case per rips feature.

Each feature builds a small project with rips on the smallest model that shows it.
Add a feature by writing a function decorated with @feature(name, model) and running
the nightly workflow; the first run reports missing_base until references are promoted.
"""

import math

import rips

FEATURES = {}

SPE1 = "spe1/SPE1CASE2.EGRID"
TEST10K = "TEST10K_FLT_LGR_NNC/TEST10K_FLT_LGR_NNC.EGRID"
TEST10K_WELLPATH = "TEST10K_FLT_LGR_NNC/wellpath_a.dev"
SUMMARY = "flow_diagnostics_test/SIMPLE_SUMMARY2.SMSPEC"


def feature(name, model=SPE1):
    def register(func):
        FEATURES[name] = (func, model)
        return func

    return register


def _show_pressure(view):
    # SOIL is zero at the first time step and shows nothing
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.update()


def _box_center(case):
    bbox = case.reservoir_boundingbox()
    return (
        (bbox.min_x + bbox.max_x) / 2,
        (bbox.min_y + bbox.max_y) / 2,
        (bbox.min_z + bbox.max_z) / 2,
        bbox,
    )


@feature("grid_default")
def grid_default(project, case, view, testmodels):
    pass


@feature("background_color")
def background_color(project, case, view, testmodels):
    view.background_color = "#3388AA"
    view.update()


@feature("grid_box_hidden")
def grid_box_hidden(project, case, view, testmodels):
    view.show_grid_box = False
    view.update()


@feature("z_scale")
def z_scale(project, case, view, testmodels):
    view.grid_z_scale = 1.0
    view.update()


@feature("disable_lighting")
def disable_lighting(project, case, view, testmodels):
    view.disable_lighting = True
    view.update()


@feature("cell_result_dynamic", TEST10K)
def cell_result_dynamic(project, case, view, testmodels):
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.update()


@feature("cell_result_static", TEST10K)
def cell_result_static(project, case, view, testmodels):
    view.apply_cell_result("STATIC_NATIVE", "PORO")
    view.update()


@feature("time_step", TEST10K)
def time_step(project, case, view, testmodels):
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.current_time_step = 3
    view.update()


@feature("intersection_polyline", TEST10K)
def intersection_polyline(project, case, view, testmodels):
    _show_pressure(view)
    x, y, z, bbox = _box_center(case)
    collection = view.descendants(rips.IntersectionCollection)[0]
    intersection = collection.add_new_object(rips.CurveIntersection)
    intersection.type = "CS_POLYLINE"
    intersection.points = [
        [bbox.min_x, bbox.min_y, z],
        [x, y, z],
        [bbox.max_x, bbox.max_y, z],
    ]
    intersection.update()


@feature("regular_surface", TEST10K)
def regular_surface(project, case, view, testmodels):
    _show_pressure(view)
    x, y, z, bbox = _box_center(case)
    nx, ny = 50, 50
    collection = project.descendants(rips.SurfaceCollection)[0]
    surface = collection.new_regular_surface(
        name="Wave surface",
        origin_x=bbox.min_x + (bbox.max_x - bbox.min_x) / 4,
        origin_y=bbox.min_y + (bbox.max_y - bbox.min_y) / 4,
        depth=z,
        nx=nx,
        ny=ny,
        increment_x=(bbox.max_x - bbox.min_x) / 2 / nx,
        increment_y=(bbox.max_y - bbox.min_y) / 2 / ny,
    )
    surface.rotation = 0.0
    surface.update()
    view.set_surface_visible(surface, True)


@feature("polygon", TEST10K)
def polygon(project, case, view, testmodels):
    _show_pressure(view)
    x, y, z, bbox = _box_center(case)
    coordinates = [
        [bbox.min_x, bbox.min_y, z],
        [bbox.max_x, bbox.min_y, z],
        [bbox.max_x, bbox.max_y, z],
        [bbox.min_x, bbox.max_y, z],
    ]
    collection = project.descendants(rips.PolygonCollection)[0]
    created = collection.create_polygon(name="Bounding box", coordinates=coordinates)
    appearance = created.appearance()
    appearance.line_color = "#ff0000"
    appearance.line_thickness = 5
    appearance.update()
    view.set_polygon_visible(created, True)


@feature("well_path_import", TEST10K)
def well_path_import(project, case, view, testmodels):
    _show_pressure(view)
    project.import_well_paths([str(testmodels / TEST10K_WELLPATH)])


@feature("modeled_well_path", TEST10K)
def modeled_well_path(project, case, view, testmodels):
    _show_pressure(view)
    collection = project.well_path_collection()
    well_path = collection.add_new_object(rips.ModeledWellPath)
    well_path.name = "Modeled well"
    well_path.update()
    geometry = well_path.well_path_geometry()
    reference = geometry.reference_point
    reference[0], reference[1], reference[2] = 3736.27, 4630.61, 4133.5
    geometry.update()
    geometry.append_well_target([0, 0, 0])
    geometry.append_well_target([300, 200, 50])
    geometry.append_well_target([600, 400, 120])
    geometry.update()


@feature("well_path_from_points", TEST10K)
def well_path_from_points(project, case, view, testmodels):
    _show_pressure(view)
    collection = project.well_path_collection()
    points = [
        [3736.0 + 30 * i, 4630.0 + 20 * i, -4130.0 - 10 * i + math.sin(i) * 5]
        for i in range(15)
    ]
    collection.import_well_path_from_points(name="Point well", coordinates=points)
