# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *

def setup_assembly_and_run(L=70.0, applied_displacement=1.4):
    myModel = mdb.models['Model-1']
    myAssembly = myModel.rootAssembly
    
    # ساخت سیستم مختصات در صورت عدم وجود
    if not myAssembly.features.has_key('Datum csys-1'):
        myAssembly.DatumCsysByDefault(CARTESIAN)
    
    # پیدا کردن قطعه نهایی (هوشمند)
    part_name = 'Specimen'
    if 'Specimen_Orphan' in myModel.parts:
        part_name = 'Specimen_Orphan'
    myPart = myModel.parts[part_name]
    
    # 1. مونتاژ (Assembly) ایمن
    if 'Specimen_Inst' not in myAssembly.instances:
        myInst = myAssembly.Instance(name='Specimen_Inst', part=myPart, dependent=ON)
    else:
        myInst = myAssembly.instances['Specimen_Inst']
    
    # 2. تعریف Step (فعال‌سازی Nlgeom برای ترک‌خوردگی)
    if 'Step-1' not in myModel.steps:
        myModel.StaticStep(name='Step-1', previous='Initial', nlgeom=ON, 
                           initialInc=0.01, minInc=1e-15, maxInc=0.05)
        
    # 3. خروجی‌ها (درخواست متغیرهای خرابی)
    if 'F-Output-1' in myModel.fieldOutputRequests:
        myModel.fieldOutputRequests['F-Output-1'].setValues(
            variables=('S', 'E', 'U', 'SDEG', 'STATUS', 'DMICRT'))
        
    # 4. شرایط مرزی (Boundary Conditions)
    tol = 1e-3
    left_edges = myInst.edges.getByBoundingBox(xMin=-tol, yMin=-tol, zMin=-tol, xMax=tol, yMax=2.0, zMax=tol)
    right_edges = myInst.edges.getByBoundingBox(xMin=L-tol, yMin=-tol, zMin=-tol, xMax=L+tol, yMax=2.0, zMax=tol)
    
    left_set = myAssembly.Set(edges=left_edges, name='Left_Edge')
    right_set = myAssembly.Set(edges=right_edges, name='Right_Edge')
    
    # اصلاح ارور: استفاده از کلمه صحیح boundaryConditions
    if 'Fix_Left' not in myModel.boundaryConditions:
        myModel.DisplacementBC(name='Fix_Left', createStepName='Step-1', 
                               region=left_set, u1=0.0, u2=0.0)
                           
    if 'Pull_Right' not in myModel.boundaryConditions:
        myModel.DisplacementBC(name='Pull_Right', createStepName='Step-1', 
                               region=right_set, u1=applied_displacement)
                           
    # 5. ساخت Job
    job_name = 'Tensile_Test_Stochastic'
    if job_name not in mdb.jobs:
        mdb.Job(name=job_name, model='Model-1', 
                description='Mesoscale transverse cracking simulation', 
                numCpus=4, numDomains=4)
            
    print("==================================================")
    print("SUCCESS: Assembly, Step, BCs, and Job created!")
    print("Job Name: " + job_name)
    print("==================================================")

if __name__ == "__main__":
    setup_assembly_and_run()
