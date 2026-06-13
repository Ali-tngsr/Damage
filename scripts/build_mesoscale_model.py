# -*- coding: utf-8 -*-
"""Build the stochastic mesoscale Abaqus model for the laminate gauge section."""
from __future__ import print_function

import os
import sys

from abaqus import *
from abaqusConstants import *
import regionToolset

import inspect
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from mesoscale_common import assign_vf_field, get_properties, rounded_vf, safe_name

MODEL_NAME = 'Model-1'
PART_NAME = 'Specimen'
PLY90_SET_NAME = 'Ply90_Faces'


def _delete_if_exists(repository, name):
    try:
        del repository[name]
    except KeyError:
        pass


def _create_engineering_material(model, name, props, orientation):
    if name in model.materials.keys():
        return
    model.Material(name=name)
    nu21 = props['nu12'] * (props['E22'] / props['E11'])

    if orientation == '0deg':
        table = ((props['E11'], props['E22'], props['E22'],
                  props['nu12'], props['nu12'], props['nu23'],
                  props['G12'], props['G12'], props['G23']),)
    elif orientation == '90deg':
        table = ((props['E22'], props['E22'], props['E11'],
                  props['nu23'], nu21, nu21,
                  props['G23'], props['G12'], props['G12']),)
    model.materials[name].Elastic(type=ENGINEERING_CONSTANTS, table=table)


def _create_section(model, section_name, material_name):
    if section_name not in model.sections.keys():
        model.HomogeneousSolidSection(name=section_name, material=material_name, thickness=None)


def create_model(model_name=MODEL_NAME):
    _delete_if_exists(mdb.models, model_name)
    return mdb.Model(name=model_name)


def build_model(L=70.0, t_0=0.25, t_90=0.5, rho_sat=8.0, seed=42,
                vf_decimals=1, model_name=MODEL_NAME):
    """Build geometry, partitions, stochastic materials, mesh seeds and sets."""
    model = create_model(model_name)
    t_total = (2.0 * t_0) + t_90
    n_cols = max(1, int(round(rho_sat * L)))
    dx = L / float(n_cols)
    row_thickness = t_90 / 5.0

    sketch = model.ConstrainedSketch(name='profile', sheetSize=max(200.0, 2.0 * L))
    sketch.rectangle(point1=(0.0, 0.0), point2=(L, t_total))
    part = model.Part(name=PART_NAME, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    part.BaseShell(sketch=sketch)

    horiz = model.ConstrainedSketch(name='partition_horizontal', sheetSize=max(200.0, 2.0 * L))
    horiz.Line(point1=(0.0, t_0), point2=(L, t_0))
    horiz.Line(point1=(0.0, t_0 + t_90), point2=(L, t_0 + t_90))
    for row_idx in range(1, 5):
        y_pos = t_0 + (row_idx * row_thickness)
        horiz.Line(point1=(0.0, y_pos), point2=(L, y_pos))
    part.PartitionFaceBySketch(faces=part.faces, sketch=horiz)

    vert = model.ConstrainedSketch(name='partition_vertical', sheetSize=max(200.0, 2.0 * L))
    for col_idx in range(1, n_cols):
        x_pos = col_idx * dx
        vert.Line(point1=(x_pos, 0.0), point2=(x_pos, t_total))
    part.PartitionFaceBySketch(faces=part.faces, sketch=vert)

    # =========================================================================
    # کد جدید: ساخت خودکار ست لبه‌ها با متد کاملاً ایمن findAt
    # =========================================================================
    crack_edges_list = []
    for col_idx in range(1, n_cols):
        x_pos = col_idx * dx
        # برای هر 5 ردیف داخل لایه 90 درجه، نقطه وسط لبه عمودی را استخراج می‌کنیم
        for row_idx in range(5):
            y_center = t_0 + (row_idx + 0.5) * row_thickness
            # فرمت مخصوص آباکوس برای findAt
            crack_edges_list.append(((x_pos, y_center, 0.0),))

    if crack_edges_list:
        # پیدا کردن یکپارچه تمام لبه‌ها که مستقیماً در آباکوس قابل تبدیل به Set است
        valid_edges = part.edges.findAt(*crack_edges_list)
        part.Set(edges=valid_edges, name='Potential_Crack_Edges')
        print('SUCCESS: Created Edge Set "Potential_Crack_Edges".')
    # =========================================================================
    vf_field = assign_vf_field(n_cols, 5, seed)
    props_0 = get_properties(45.0, units='MPa')
    mat_0, sec_0 = 'Mat_0deg_Vf45', 'Sec_0deg_Vf45'
    _create_engineering_material(model, mat_0, props_0, '0deg')
    _create_section(model, sec_0, mat_0)

    for col_idx in range(n_cols):
        x_c = (col_idx + 0.5) * dx
        bottom_face = part.faces.findAt(((x_c, t_0 / 2.0, 0.0),))
        part.SectionAssignment(region=regionToolset.Region(faces=bottom_face), sectionName=sec_0)
        top_face = part.faces.findAt(((x_c, t_0 + t_90 + (t_0 / 2.0), 0.0),))
        part.SectionAssignment(region=regionToolset.Region(faces=top_face), sectionName=sec_0)

        for row_idx in range(5):
            vf_value = vf_field[row_idx][col_idx]
            vf_key = rounded_vf(vf_value, vf_decimals)
            mat_name = safe_name('Mat_90deg_Vf', vf_key)
            sec_name = safe_name('Sec_90deg_Vf', vf_key)
            props_90 = get_properties(vf_key, units='MPa')
            _create_engineering_material(model, mat_name, props_90, '90deg')
            _create_section(model, sec_name, mat_name)
            y_c = t_0 + (row_idx + 0.5) * row_thickness
            face_90 = part.faces.findAt(((x_c, y_c, 0.0),))
            part.SectionAssignment(region=regionToolset.Region(faces=face_90), sectionName=sec_name)

    all_faces = part.faces
    part.MaterialOrientation(
        region=regionToolset.Region(faces=all_faces),
        orientationType=GLOBAL, axis=AXIS_3,
        additionalRotationType=ROTATION_NONE, localCsys=None, fieldName='', stackDirection=STACK_3
    )
    return model, part, vf_field


if __name__ == '__main__':
    build_model()
