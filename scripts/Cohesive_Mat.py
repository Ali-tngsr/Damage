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
    # این متریال رفتار ترک‌خوردگی را کنترل می‌کند
    coh_mat_name = 'Cohesive_Mat'
    if coh_mat_name not in myModel.materials:
        coh_mat = myModel.Material(name=coh_mat_name)
        
        # سختی پنالتی (Penalty Stiffness) - مقدار بالا برای جلوگیری از نفوذ المان‌ها
        coh_mat.Elastic(type=TRACTION_SEPARATION, table=((1e5, 1e5, 1e5), ))
        
        # معیار شروع آسیب (Maximum Nominal Stress)
        # مقادیر بر اساس داده‌های نرمال مقاله (حدود 60 مگاپاسکال)
        coh_mat.MaxsDamageInitiation(table=((60.0, 60.0, 60.0), ))
        
        # تکامل آسیب (Damage Evolution) - بر اساس انرژی شکست Gc
        coh_mat.maxsDamageInitiation.DamageEvolution(
            type=ENERGY, softening=LINEAR, table=((0.2, 0.2, 0.2), )
        )
        print("Cohesive material created successfully.")

    # 2. مش‌بندی (Meshing)
    # تنظیم دانه‌بندی (Seed)
    myPart.seedPart(size=0.125, deviationFactor=0.1, minSizeFactor=0.1)
    
    # تعیین نوع المان (Plane Stress - CPS4R)
    region = regionToolset.Region(faces=myPart.faces)
    elemType = mesh.ElemType(elemCode=CPS4R, elemLibrary=STANDARD)
    myPart.setElementType(regions=region, elemTypes=(elemType, ))
    
    # تولید مش
    myPart.generateMesh()
    print("Structured mesh generated successfully!")

if __name__ == "__main__":
    setup_mesh_and_cohesive()
