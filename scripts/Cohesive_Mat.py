# -*- coding: utf-8 -*-
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
    fracture_energy = 0.2
    penalty_stiffness = 1.0e8
    for col_idx in range(n_cols):
        for row_idx in range(5):
            vf = vf_field[row_idx][col_idx]
            props = mesoscale_common.get_properties(vf, units='MPa')
            yt_local = props['YT']
            mat_name = 'Coh_Mat_C%d_R%d' % (col_idx, row_idx)
            if mat_name not in model.materials.keys():
                material = model.Material(name=mat_name)
                material.Elastic(type=TRACTION, table=((penalty_stiffness, penalty_stiffness, penalty_stiffness),))
                material.MaxsDamageInitiation(table=((yt_local, yt_local, yt_local),))
                material.maxsDamageInitiation.DamageEvolution(type=ENERGY, softening=LINEAR, table=((fracture_energy,),))
              
def create_cohesive_material(model, strength=17.0, fracture_energy=0.2, penalty_stiffness=1.0e8):
    if COH_MAT_NAME in model.materials.keys(): return model.materials[COH_MAT_NAME]
    material = model.Material(name=COH_MAT_NAME)
    material.Elastic(type=TRACTION, table=((penalty_stiffness, penalty_stiffness, penalty_stiffness),))
    material.MaxsDamageInitiation(table=((strength, strength, strength),))
    material.maxsDamageInitiation.DamageEvolution(type=ENERGY, softening=LINEAR, table=((fracture_energy,),))
    return material

def create_cohesive_section(model):
    if COH_SECTION_NAME not in model.sections.keys():
        model.CohesiveSection(name=COH_SECTION_NAME, material=COH_MAT_NAME,
                              response=TRACTION_SEPARATION, initialThicknessType=GEOMETRY)

def mesh_continuum_part(element_size=0.125):
    model = mdb.models[MODEL_NAME]
    part = model.parts[PART_NAME]

    # ساخت متریال و سکشن چسبنده اصلی (برای استفاده دستی شما در آباکوس)
    create_cohesive_material(model)
    create_cohesive_section(model)

    part.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)

    # اختصاص المان پیوسته به کل قطعه (چون ترک‌ها هنوز ایجاد نشده‌اند)
    all_faces = part.faces
    cont_region = regionToolset.Region(faces=all_faces)
    cont_elem = mesh.ElemType(elemCode=CPS4R, elemLibrary=STANDARD)
    part.setElementType(regions=cont_region, elemTypes=(cont_elem,))

    part.generateMesh()
    print('SUCCESS: Part meshed uniformly with continuum elements. Ready for manual seam insertion.')

if __name__ == '__main__':
    mesh_continuum_part()
