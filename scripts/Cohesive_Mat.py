# -*- coding: utf-8 -*-
"""Define cohesive material/section and mesh the mesoscale continuum part."""
from __future__ import print_function

from abaqus import *
from abaqusConstants import *
import mesh
import regionToolset

MODEL_NAME = 'Model-1'
PART_NAME = 'Specimen'
COH_MAT_NAME = 'Cohesive_Mat'
COH_SECTION_NAME = 'Cohesive_Sec'

def create_stochastic_cohesive_materials(model, vf_field, n_cols):
    import mesoscale_common
    fracture_energy = 0.2  # مقدار Gc_MT
    penalty_stiffness = 1.0e8 # مقدار سفتی پنالتی طبق مقاله
    
    # برای هر ستون ترک و هر ردیف، یک متریال چسبنده مختص آن ناحیه می‌سازیم
    for col_idx in range(n_cols):
        for row_idx in range(5):
            vf = vf_field[row_idx][col_idx]
            props = mesoscale_common.get_properties(vf, units='MPa')
            yt_local = props['YT']  # محاسبه استحکام کششی محلی
            
            mat_name = 'Coh_Mat_C%d_R%d' % (col_idx, row_idx)
            if mat_name not in model.materials.keys():
                material = model.Material(name=mat_name)
                # سفتی پنالتی یکنواخت
                material.Elastic(type=TRACTION, table=((penalty_stiffness, penalty_stiffness, penalty_stiffness),))
                # اعمال استحکام متغیر به المان چسبنده (عامل اصلی باز شدن ترک‌ها)
                material.MaxsDamageInitiation(table=((yt_local, yt_local, yt_local),))
                material.maxsDamageInitiation.DamageEvolution(type=ENERGY, softening=LINEAR, table=((fracture_energy,),))
              
def create_cohesive_material(model, strength=17.0, fracture_energy=0.2,
                             penalty_stiffness=1.0e8):
    """Create the baseline bilinear traction-separation cohesive material."""
    if COH_MAT_NAME in model.materials.keys():
        return model.materials[COH_MAT_NAME]

    material = model.Material(name=COH_MAT_NAME)
    material.Elastic(type=TRACTION,
                     table=((penalty_stiffness, penalty_stiffness, penalty_stiffness),))
    material.MaxsDamageInitiation(table=((strength, strength, strength),))
    material.maxsDamageInitiation.DamageEvolution(type=ENERGY, softening=LINEAR,
                                                  table=((fracture_energy,),))
    print('Cohesive material created: %s' % COH_MAT_NAME)
    return material


def create_cohesive_section(model):
    if COH_SECTION_NAME not in model.sections.keys():
        model.CohesiveSection(name=COH_SECTION_NAME, material=COH_MAT_NAME,
                              response=TRACTION_SEPARATION,
                              initialThicknessType=GEOMETRY)
        print('Cohesive section created: %s' % COH_SECTION_NAME)


def mesh_continuum_part(element_size=0.125):
    """Assign plane-stress elements and generate the mesh for Specimen."""
    model = mdb.models[MODEL_NAME]
    part = model.parts[PART_NAME]

    create_cohesive_material(model)
    create_cohesive_section(model)

    part.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)
    face_region = regionToolset.Region(faces=part.faces)
    element_type = mesh.ElemType(elemCode=CPS4R, elemLibrary=STANDARD)
    part.setElementType(regions=face_region, elemTypes=(element_type,))
    part.generateMesh()
    print('Continuum mesh generated for %s with element size %g.' % (PART_NAME, element_size))
    # پیدا کردن سطوح مربوط به نوارهای باریک (Cohesive) و اختصاص المان COH2D4
    import mesh
    cohesive_faces = []
    # dx و n_cols را بر اساس مقادیر L و rho_sat محاسبه کنید
    cohesive_width = 1e-4
    
    for col_idx in range(1, n_cols):
        x_center = (col_idx * dx) + (cohesive_width / 2.0)
        # پیدا کردن فیس‌های نوار باریک در طول ضخامت
        faces = part.faces.getByBoundingBox(
            xMin=x_center - cohesive_width, xMax=x_center + cohesive_width,
            yMin=-0.1, yMax=t_total + 0.1, zMin=-0.1, zMax=0.1)
        for f in faces:
            cohesive_faces.append(f)
            
    if cohesive_faces:
        coh_region = regionToolset.Region(faces=mesh.MeshFaceArray(cohesive_faces))
        coh_elem_type = mesh.ElemType(elemCode=COH2D4, elemLibrary=STANDARD)
        part.setElementType(regions=coh_region, elemTypes=(coh_elem_type,))

if __name__ == '__main__':
    mesh_continuum_part()
