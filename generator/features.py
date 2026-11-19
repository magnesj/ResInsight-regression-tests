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


Z_SCALE = 5.0


def _look_at(view, target, direction, distance):
    """Point the camera at target, looking along direction with world Z as up."""
    # Camera coordinates are in scaled display space
    view.grid_z_scale = Z_SCALE
    d = _normalize(direction)
    up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.99 else (0.0, 1.0, 0.0)
    dot = sum(u * c for u, c in zip(up, d))
    y = _normalize([u - dot * c for u, c in zip(up, d)])
    z = [-c for c in d]
    x = [
        y[1] * z[2] - y[2] * z[1],
        y[2] * z[0] - y[0] * z[2],
        y[0] * z[1] - y[1] * z[0],
    ]
    eye = [t - c * distance for t, c in zip(target, d)]
    # The camera matrix is a row-major view matrix (world to camera)
    view.camera_matrix = [
        x[0], x[1], x[2], -sum(a * b for a, b in zip(x, eye)),
        y[0], y[1], y[2], -sum(a * b for a, b in zip(y, eye)),
        z[0], z[1], z[2], -sum(a * b for a, b in zip(z, eye)),
        0.0, 0.0, 0.0, 1.0,
    ]
    view.camera_point_of_interest = list(target)
    view.update()


def _normalize(v):
    length = math.sqrt(sum(c * c for c in v))
    return [c / length for c in v]


def _display_offset(case):
    # Camera coordinates are relative to the center of the main grid, which is
    # larger than the active cell bounding box
    centers = case.grid(0).cell_centers()
    xs = [c.x for c in centers]
    ys = [c.y for c in centers]
    # Cell centers report depth, while the scene uses negative depth as z
    zs = [-c.z for c in centers]
    return (
        (min(xs) + max(xs)) / 2,
        (min(ys) + max(ys)) / 2,
        (min(zs) + max(zs)) / 2,
    )


def _look_at_points(view, case, points, direction=(0.0, 1.0, -0.6), margin=2.5):
    xs, ys, zs = zip(*points)
    cx, cy, cz = _display_offset(case)
    target = (
        (min(xs) + max(xs)) / 2 - cx,
        (min(ys) + max(ys)) / 2 - cy,
        ((min(zs) + max(zs)) / 2 - cz) * Z_SCALE,
    )
    extent = math.dist(
        (min(xs), min(ys), min(zs) * Z_SCALE), (max(xs), max(ys), max(zs) * Z_SCALE)
    )
    _look_at(view, target, direction, max(extent, 100.0) * margin)


def _look_at_grid(view, case, direction=(0.0, 1.0, -0.6)):
    bbox = case.reservoir_boundingbox()
    corners = [
        (bbox.min_x, bbox.min_y, bbox.min_z),
        (bbox.max_x, bbox.max_y, bbox.max_z),
    ]
    _look_at_points(view, case, corners, direction, margin=1.4)


def _hide_grid(view):
    # Keep a single corner cell so that only well paths and intersections remain visible
    cell_filters = view.descendants(rips.CellFilterCollection)[0]
    cell_range = cell_filters.add_new_object(rips.CellRangeFilter)
    cell_range.start_index_i = 1
    cell_range.start_index_j = 1
    cell_range.start_index_k = 1
    cell_range.cell_count_i = 1
    cell_range.cell_count_j = 1
    cell_range.cell_count_k = 1
    cell_range.update()


def _read_dev_points(path):
    # Well path files list x, y, depth and md after a name line
    points = []
    for line in path.read_text().splitlines()[1:]:
        values = line.split()
        if len(values) >= 3:
            points.append((float(values[0]), float(values[1]), -float(values[2])))
    return points


def _intersect_well(view, well_path):
    collection = view.descendants(rips.IntersectionCollection)[0]
    intersection = collection.add_new_object(rips.CurveIntersection)
    intersection.type = "CS_WELL_PATH"
    intersection.well_path = well_path
    intersection.update()


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
    """Unmodified default 3D view of the SPE1 grid."""
    pass


@feature("background_color")
def background_color(project, case, view, testmodels):
    """View background color set to #3388AA."""
    view.background_color = "#3388AA"
    view.update()


@feature("grid_box_hidden")
def grid_box_hidden(project, case, view, testmodels):
    """Grid box (axes) hidden with show_grid_box = False."""
    view.show_grid_box = False
    view.update()


@feature("z_scale")
def z_scale(project, case, view, testmodels):
    """Z scale set to 1 instead of the default 5."""
    view.grid_z_scale = Z_SCALE
    view.update()


@feature("disable_lighting")
def disable_lighting(project, case, view, testmodels):
    """Lighting disabled with disable_lighting = True."""
    view.disable_lighting = True
    view.update()


@feature("cell_result_dynamic", TEST10K)
def cell_result_dynamic(project, case, view, testmodels):
    """Dynamic cell result PRESSURE on the first time step."""
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.update()


@feature("cell_result_static", TEST10K)
def cell_result_static(project, case, view, testmodels):
    """Static cell result PORO."""
    view.apply_cell_result("STATIC_NATIVE", "PORO")
    view.update()


@feature("time_step", TEST10K)
def time_step(project, case, view, testmodels):
    """PRESSURE shown at time step 3 (current_time_step)."""
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.current_time_step = 3
    view.update()


@feature("intersection_polyline", TEST10K)
def intersection_polyline(project, case, view, testmodels):
    """Polyline intersection through the middle of the grid, oblique camera."""
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
    _look_at_grid(view, case, (0.3, 1.0, -0.5))


@feature("regular_surface", TEST10K)
def regular_surface(project, case, view, testmodels):
    """Regular surface covering the central half of the grid, oblique camera."""
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
    _look_at_grid(view, case)


@feature("polygon", TEST10K)
def polygon(project, case, view, testmodels):
    """Red polygon outlining the grid bounding box."""
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
    """Well path imported from a .dev file with a well path intersection, oblique camera."""
    _show_pressure(view)
    project.import_well_paths([str(testmodels / TEST10K_WELLPATH)])
    well_path = project.well_paths()[0]
    _intersect_well(view, well_path)
    _look_at_points(view, case, _read_dev_points(testmodels / TEST10K_WELLPATH), margin=2.5)


@feature("modeled_well_path", TEST10K)
def modeled_well_path(project, case, view, testmodels):
    """Modeled well path with three targets; grid hidden with a cell range filter."""
    _show_pressure(view)
    collection = project.well_path_collection()
    well_path = collection.add_new_object(rips.ModeledWellPath)
    well_path.name = "Modeled well"
    well_path.update()
    geometry = well_path.well_path_geometry()
    reference = geometry.reference_point
    reference[0], reference[1], reference[2] = 3736.27, 4630.61, 4133.5
    geometry.update()
    targets = [[0, 0, 0], [300, 200, 50], [600, 400, 120]]
    for target in targets:
        geometry.append_well_target(target)
    geometry.update()
    _hide_grid(view)
    points = [
        (reference[0] + dx, reference[1] + dy, -(reference[2] + dz))
        for dx, dy, dz in targets
    ]
    _look_at_points(view, case, points, margin=1.5)


@feature("well_path_from_points", TEST10K)
def well_path_from_points(project, case, view, testmodels):
    """Well path imported from a list of points; grid hidden with a cell range filter."""
    _show_pressure(view)
    collection = project.well_path_collection()
    points = [
        [3736.0 + 30 * i, 4630.0 + 20 * i, -4130.0 - 10 * i + math.sin(i) * 5]
        for i in range(15)
    ]
    well_path = collection.import_well_path_from_points(
        name="Point well", coordinates=points
    )
    _hide_grid(view)
    _look_at_points(view, case, points, margin=1.5)

def _fit_multi_plots(project, columns, rows):
    """Use a page layout that matches the number of subplots, so the page has no empty cells."""
    for multi_plot in project.descendants(rips.MultiSummaryPlot):
        multi_plot.number_of_columns = columns
        multi_plot.rows_per_page = rows
        multi_plot.update()


@feature("summary_plot")
def summary_plot(project, case, view, testmodels):
    """Summary plot of the field oil production total (FOPT)."""
    view.delete()  # only the plot should be snapshotted
    summary_case = project.import_summary_case(str(testmodels / SUMMARY))
    collection = project.summary_plot_collection()
    collection.new_summary_plot(summary_cases=[summary_case], address="FOPT")
    _fit_multi_plots(project, rips.NumberOfColumns._1, rips.RowsPerPage._1)


@feature("summary_multi_plot")
def summary_multi_plot(project, case, view, testmodels):
    """Multi plot with one summary plot per vector (FOPT, FWPT)."""
    view.delete()  # only the plot should be snapshotted
    summary_case = project.import_summary_case(str(testmodels / SUMMARY))
    collection = project.summary_plot_collection()
    collection.new_summary_multi_plot(
        summary_cases=[summary_case], addresses=["FOPT", "FWPT"]
    )
    _fit_multi_plots(project, rips.NumberOfColumns._2, rips.RowsPerPage._1)

