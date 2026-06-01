# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh

def setup_mesh_and_cohesive():
    # اتصال به مدل و قطعه‌ای که از قبل ساخته‌اید
    myModel = mdb.models['Model-1']
    myPart = myModel.parts['Specimen']
    
    # 1. تعریف متریال چسبنده (Cohesive Material)
    coh_mat_name = 'Cohesive_Mat'
    if coh_mat_name not in myModel.materials:
        coh_mat = myModel.Material(name=coh_mat_name)
        
        # اصلاح ارور: استفاده از کلمه صحیح TRACTION
        coh_mat.Elastic(type=TRACTION, table=((1e5, 1e5, 1e5), ))
        
        # معیار شروع آسیب (Maximum Nominal Stress)
        coh_mat.MaxsDamageInitiation(table=((60.0, 60.0, 60.0), ))
        
        # تکامل آسیب (Damage Evolution)
        coh_mat.maxsDamageInitiation.DamageEvolution(
            type=ENERGY, softening=LINEAR, table=((0.2, 0.2, 0.2), )
        )
        print("Cohesive material created successfully.")

    # 2. مش‌بندی (Meshing)
    myPart.seedPart(size=0.125, deviationFactor=0.1, minSizeFactor=0.1)
    
    region = regionToolset.Region(faces=myPart.faces)
    elemType = mesh.ElemType(elemCode=CPS4R, elemLibrary=STANDARD)
    myPart.setElementType(regions=region, elemTypes=(elemType, ))
    
    myPart.generateMesh()
    print("Structured mesh generated successfully!")

if __name__ == "__main__":
    setup_mesh_and_cohesive()
