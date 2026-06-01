# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *

def create_crack_paths_set(L=70.0, t_0=0.25, t_90=0.5):
    myModel = mdb.models['Model-1']
    myPart = myModel.parts['Specimen']
    
    valid_coords = []
    
    # 1. ساخت مقطع چسبنده (Section) برای متریال مرحله قبل
    if 'Cohesive_Sec' not in myModel.sections:
        myModel.CohesiveSection(
            name='Cohesive_Sec', 
            material='Cohesive_Mat', 
            response=TRACTION_SEPARATION, 
            initialThicknessType=GEOMETRY
        )
        print("Cohesive Section created.")

    # 2. بررسی تک‌تک لبه‌های قطعه
    for e in myPart.edges:
        pt = e.pointOn[0]
        x_mid, y_mid = pt[0], pt[1]
        
        # شرط اول: نقطه میانی خط باید داخل لایه 90 درجه (لایه وسط) باشد
        if (t_0 + 1e-3) < y_mid < (t_0 + t_90 - 1e-3):
            # شرط دوم: روی مرزهای بیرونی نمونه (چپ و راست) نباشد
            if 1e-3 < x_mid < (L - 1e-3):
                # شرط سوم: خط باید کاملاً عمودی باشد (بدون تغییرات در x)
                bbox = e.getBoundingBox()
                dx = bbox['high'][0] - bbox['low'][0]
                if dx < 1e-4:
                    valid_coords.append((pt, ))
    
    # 3. ایجاد گروه (Set) از لبه‌های پیدا شده
    if valid_coords:
        edges_seq = myPart.edges.findAt(*valid_coords)
        myPart.Set(edges=edges_seq, name='Crack_Paths')
        print("=========================================")
        print("SUCCESS: {} crack paths grouped!".format(len(valid_coords)))
        print("Set 'Crack_Paths' created successfully.")
        print("=========================================")
    else:
        print("Error: No edges matched the criteria.")

if __name__ == "__main__":
    create_crack_paths_set()
