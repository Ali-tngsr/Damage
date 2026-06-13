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
    """Assign appropriate elements and sections to continuum and cohesive faces."""
    model = mdb.models[MODEL_NAME]
    part = model.parts[PART_NAME]

    # ساخت متریال و سکشن چسبنده اصلی
    create_cohesive_material(model)
    create_cohesive_section(model)

    part.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)

    # === ترفند هوشمند مساحت برای جداسازی قطعات چسبنده از قطعات اصلی ===
    cohesive_faces = []
    continuum_faces = []

    for face in part.faces:
        # نوارهای ترک مساحتی بسیار کوچکتر از سلول‌های اصلی دارند
        if face.getSize() < 0.005:
            cohesive_faces.append(face)
        else:
            continuum_faces.append(face)

    import mesh
    import regionToolset

    # ۱. اختصاص المان به قطعات پیوسته (کامپوزیت)
    if continuum_faces:
        cont_region = regionToolset.Region(faces=mesh.MeshFaceArray(continuum_faces))
        cont_elem = mesh.ElemType(elemCode=CPS4R, elemLibrary=STANDARD)
        part.setElementType(regions=cont_region, elemTypes=(cont_elem,))

    # ۲. اختصاص المان و سکشن خرابی به مسیرهای ترک
    if cohesive_faces:
        coh_region = regionToolset.Region(faces=mesh.MeshFaceArray(cohesive_faces))
        coh_elem = mesh.ElemType(elemCode=COH2D4, elemLibrary=STANDARD)
        part.setElementType(regions=coh_region, elemTypes=(coh_elem,))
        # مهم: تحمیل سکشن چسبنده برای فعال شدن متغیر SDEG
        part.SectionAssignment(region=coh_region, sectionName=COH_SECTION_NAME)
        part.Set(faces=mesh.MeshFaceArray(cohesive_faces), name='Cohesive_Elements_Set')

    part.generateMesh()
    print('SUCCESS: Elements and sections correctly partitioned by area.')

if __name__ == '__main__':
    mesh_continuum_part()
