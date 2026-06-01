# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *

def make_orphan_mesh():
    myModel = mdb.models['Model-1']
    
    # بررسی وجود قطعه اصلی که مش‌بندی شده است
    if 'Specimen' in myModel.parts:
        myPart = myModel.parts['Specimen']
        
        # ساخت قطعه جدید از نوع Orphan Mesh
        # متغیر copySets=True تضمین می‌کند که گروه مسیرهای ترک پاک نشود
        myPart.PartFromMesh(name='Specimen_Orphan', copySets=True)
        
        print("==================================================")
        print("SUCCESS: Orphan Mesh 'Specimen_Orphan' created!")
        print("==================================================")
    else:
        print("Error: Part 'Specimen' not found!")

if __name__ == "__main__":
    make_orphan_mesh()
