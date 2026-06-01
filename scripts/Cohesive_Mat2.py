# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *

def create_crack_paths_set(L=70.0, t_0=0.25, t_90=0.5, rho_sat=8.0):
    myModel = mdb.models['Model-1']
    myPart = myModel.parts['Specimen']
    
    # محاسبه ابعاد شبکه دقیقاً مشابه مرحله ساخت هندسه
    n_cols = int(np.round(rho_sat * L))
    dx = L / float(n_cols)
    row_thickness = t_90 / 5.0
    
    # 1. ساخت مقطع چسبنده (Section) برای متریال مرحله قبل
    if 'Cohesive_Sec' not in myModel.sections:
        myModel.CohesiveSection(
            name='Cohesive_Sec', 
            material='Cohesive_Mat', 
            response=TRACTION_SEPARATION, 
            initialThicknessType=GEOMETRY
        )
        print("Cohesive Section created.")

    # 2. پیدا کردن لبه‌های عمودی با مختصات دقیق ریاضی
    valid_coords = []
    
    # پیمایش روی ستون‌های داخلی (از 1 تا یکی مانده به آخر)
    for j in range(1, n_cols):
        x_pos = j * dx
        
        # پیمایش روی 5 ردیفِ لایه 90 درجه
        for i in range(5):
            y_mid = t_0 + (i + 0.5) * row_thickness
            
            # ثبت نقطه میانی هر خط عمودی
            valid_coords.append(((x_pos, y_mid, 0.0), ))
            
    # 3. ایجاد گروه (Set) از لبه‌های پیدا شده
    if valid_coords:
        # انتخاب دسته‌جمعی تمام خطوط
        edges_seq = myPart.edges.findAt(*valid_coords)
        myPart.Set(edges=edges_seq, name='Crack_Paths')
        print("=========================================")
        print("SUCCESS: {} vertical crack paths grouped!".format(len(valid_coords)))
        print("Set 'Crack_Paths' created successfully.")
        print("=========================================")
    else:
        print("Error: No edges matched the calculated coordinates.")

if __name__ == "__main__":
    create_crack_paths_set()
