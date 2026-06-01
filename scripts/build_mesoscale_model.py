# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *
import regionToolset
import numpy as np

# پاکسازی مدل‌های قبلی به روش کاملاً ایمن در آباکوس
try:
    del mdb.models['Model-1']
except KeyError:
    pass
    
myModel = mdb.Model(name='Model-1')

# ==========================================
# داده‌های جدول 1 (به مگاپاسکال تبدیل می‌شوند)
# ==========================================
VF_DATA = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
E11_DATA = [1.70, 12.20, 22.73, 33.29, 43.80, 54.31, 64.85]
NU12_DATA = [0.40, 0.64, 0.59, 0.54, 0.49, 0.45, 0.40]
E22_DATA = [1.70, 2.48, 3.25, 4.45, 6.59, 10.89, 17.98]
NU23_DATA = [0.40, 0.34, 0.34, 0.32, 0.28, 0.23, 0.16]
G12_DATA = [0.61, 0.81, 1.09, 1.51, 2.21, 3.68, 6.15]
G23_DATA = [0.61, 0.78, 1.02, 1.43, 2.21, 3.90, 6.80]

def get_props(vf):
    """درون‌یابی خطی خواص مواد برای یک کسر حجمی خاص"""
    return {
        'E11': float(np.interp(vf, VF_DATA, E11_DATA)) * 1000.0,
        'E22': float(np.interp(vf, VF_DATA, E22_DATA)) * 1000.0,
        'nu12': float(np.interp(vf, VF_DATA, NU12_DATA)),
        'nu23': float(np.interp(vf, VF_DATA, NU23_DATA)),
        'G12': float(np.interp(vf, VF_DATA, G12_DATA)) * 1000.0,
        'G23': float(np.interp(vf, VF_DATA, G23_DATA)) * 1000.0
    }

def assign_vf_field(n_cols, n_rows=5, seed=42):
    if seed is not None:
        np.random.seed(seed)
    vf_field = np.zeros((n_rows, n_cols))
    vf_field[0, :] = np.random.uniform(0, 30, n_cols)
    vf_field[4, :] = np.random.uniform(0, 30, n_cols)
    vf_field[1, :] = np.random.uniform(20, 55, n_cols)
    vf_field[3, :] = np.random.uniform(20, 55, n_cols)
    vf_field[2, :] = np.random.uniform(45, 75, n_cols)
    return vf_field

def build_model(L=70.0, t_0=0.25, t_90=0.5, rho_sat=8.0, seed=42):
    t_total = (2 * t_0) + t_90
    n_cols = int(np.round(rho_sat * L))
    dx = L / float(n_cols)
    
    # 1. ساخت هندسه
    mySketch = myModel.ConstrainedSketch(name='profile', sheetSize=200.0)
    mySketch.rectangle(point1=(0.0, 0.0), point2=(L, t_total))
    myPart = myModel.Part(name='Specimen', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    myPart.BaseShell(sketch=mySketch)
    
    # 2. پارتیشن‌بندی
    mySketch_horiz = myModel.ConstrainedSketch(name='horiz', sheetSize=200.0)
    mySketch_horiz.Line(point1=(0.0, t_0), point2=(L, t_0))
    mySketch_horiz.Line(point1=(0.0, t_0 + t_90), point2=(L, t_0 + t_90))
    row_thickness = t_90 / 5.0
    for i in range(1, 5):
        y_pos = t_0 + (i * row_thickness)
        mySketch_horiz.Line(point1=(0.0, y_pos), point2=(L, y_pos))
    myPart.PartitionFaceBySketch(faces=myPart.faces, sketch=mySketch_horiz)
    
    mySketch_vert = myModel.ConstrainedSketch(name='vert', sheetSize=200.0)
    for j in range(1, n_cols):
        x_pos = j * dx
        mySketch_vert.Line(point1=(x_pos, 0.0), point2=(x_pos, t_total))
    myPart.PartitionFaceBySketch(faces=myPart.faces, sketch=mySketch_vert)
    
    # 3. اختصاص مواد
    vf_field = assign_vf_field(n_cols, 5, seed)
    print("Assigning materials... this might take a minute...")
    
    prop_0 = get_props(45.0)
    mat_0_name = "Mat_0_deg"
    myModel.Material(name=mat_0_name)
    myModel.materials[mat_0_name].Elastic(
        type=ENGINEERING_CONSTANTS,
        table=((prop_0['E11'], prop_0['E22'], prop_0['E22'], 
                prop_0['nu12'], prop_0['nu12'], prop_0['nu23'], 
                prop_0['G12'], prop_0['G12'], prop_0['G23']), )
    )
    myModel.HomogeneousSolidSection(name="Sec_0_deg", material=mat_0_name, thickness=None)
    
    for j in range(n_cols):
        x_c = (j + 0.5) * dx
        
        # اختصاص به لایه 0 درجه پایین
        f_bot = myPart.faces.findAt(((x_c, t_0/2.0, 0.0),))
        myPart.SectionAssignment(region=regionToolset.Region(faces=f_bot), sectionName="Sec_0_deg")
        
        # اختصاص به لایه 0 درجه بالا
        f_top = myPart.faces.findAt(((x_c, t_0 + t_90 + t_0/2.0, 0.0),))
        myPart.SectionAssignment(region=regionToolset.Region(faces=f_top), sectionName="Sec_0_deg")
        
        # اختصاص به 5 ردیف لایه 90 درجه
        for i in range(5):
            vf_val = vf_field[i, j]
            
            # --- رفع خطای AbaqusNameError ---
            mat_name_str = "Mat_90_Vf_%.2f" % vf_val
            mat_name = mat_name_str.replace('.', '_') # جایگزینی نقطه با آندرلاین
            sec_name = "Sec_" + mat_name
            # --------------------------------
            
            if mat_name not in myModel.materials.keys():
                prop = get_props(vf_val)
                myModel.Material(name=mat_name)
                # جایگذاری هوشمندانه: در لایه 90 درجه دو بعدی، محور Z الیاف است و X, Y رزین/عرضی
                myModel.materials[mat_name].Elastic(
                    type=ENGINEERING_CONSTANTS,
                    table=((prop['E22'], prop['E22'], prop['E11'], 
                            prop['nu23'], prop['nu12'], prop['nu12'], 
                            prop['G23'], prop['G12'], prop['G12']), )
                )
                myModel.HomogeneousSolidSection(name=sec_name, material=mat_name, thickness=None)
            
            y_c_90 = t_0 + (i + 0.5) * row_thickness
            f_90 = myPart.faces.findAt(((x_c, y_c_90, 0.0),))
            myPart.SectionAssignment(region=regionToolset.Region(faces=f_90), sectionName=sec_name)
            
    print("Materials successfully assigned to all {} cells.".format(n_cols * 7))

if __name__ == "__main__":
    build_model()
        x_pos = j * dx
        mySketch_vert.Line(point1=(x_pos, 0.0), point2=(x_pos, t_total))
    myPart.PartitionFaceBySketch(faces=myPart.faces, sketch=mySketch_vert)
    
    # 3. اختصاص مواد
    vf_field = assign_vf_field(n_cols, 5, seed)
    print("Assigning materials... this might take a minute...")
    
    # متریال لایه 0 درجه (متوسط 45 درصد کسر حجمی فرض شده)
    prop_0 = get_props(45.0)
    mat_0_name = "Mat_0_deg"
    myModel.Material(name=mat_0_name)
    myModel.materials[mat_0_name].Elastic(
        type=ENGINEERING_CONSTANTS,
        table=((prop_0['E11'], prop_0['E22'], prop_0['E22'], 
                prop_0['nu12'], prop_0['nu12'], prop_0['nu23'], 
                prop_0['G12'], prop_0['G12'], prop_0['G23']), )
    )
    myModel.HomogeneousSolidSection(name="Sec_0_deg", material=mat_0_name, thickness=None)
    
    for j in range(n_cols):
        x_c = (j + 0.5) * dx
        
        # اختصاص به لایه 0 درجه پایین
        f_bot = myPart.faces.findAt(((x_c, t_0/2.0, 0.0),))
        myPart.SectionAssignment(region=regionToolset.Region(faces=f_bot), sectionName="Sec_0_deg")
        
        # اختصاص به لایه 0 درجه بالا
        f_top = myPart.faces.findAt(((x_c, t_0 + t_90 + t_0/2.0, 0.0),))
        myPart.SectionAssignment(region=regionToolset.Region(faces=f_top), sectionName="Sec_0_deg")
        
        # اختصاص به 5 ردیف لایه 90 درجه
        for i in range(5):
            vf_val = vf_field[i, j]
            mat_name = "Mat_90_Vf_%.2f" % vf_val
            sec_name = "Sec_" + mat_name
            
            if mat_name not in myModel.materials.keys():
                prop = get_props(vf_val)
                myModel.Material(name=mat_name)
                # جایگذاری هوشمندانه: در لایه 90 درجه دو بعدی، محور Z الیاف است و X, Y رزین/عرضی
                myModel.materials[mat_name].Elastic(
                    type=ENGINEERING_CONSTANTS,
                    table=((prop['E22'], prop['E22'], prop['E11'], 
                            prop['nu23'], prop['nu12'], prop['nu12'], 
                            prop['G23'], prop['G12'], prop['G12']), )
                )
                myModel.HomogeneousSolidSection(name=sec_name, material=mat_name, thickness=None)
            
            y_c_90 = t_0 + (i + 0.5) * row_thickness
            f_90 = myPart.faces.findAt(((x_c, y_c_90, 0.0),))
            myPart.SectionAssignment(region=regionToolset.Region(faces=f_90), sectionName=sec_name)
            
    print("Materials successfully assigned to all {} cells.".format(n_cols * 7))

if __name__ == "__main__":
    build_model()
