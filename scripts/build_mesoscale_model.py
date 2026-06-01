# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *
import regionToolset
import numpy as np

def assign_vf_field(n_cols, n_rows=5, seed=None):
    """
    تولید میدان تصادفی کسر حجمی (Vf) بر اساس قوانین مقاله.
    لایه ۹۰ درجه به ۵ ردیف ضخامتی تقسیم می‌شود.
    """
    rng = np.random.default_rng(seed)
    vf_field = np.zeros((n_rows, n_cols))
    
    # ردیف‌های مرزی (متصل به لایه 0 درجه) - غنی از رزین (0 تا 30 درصد)
    vf_field[0, :] = rng.uniform(0, 30, n_cols)
    vf_field[4, :] = rng.uniform(0, 30, n_cols)
    
    # ردیف‌های انتقال - (20 تا 55 درصد)
    vf_field[1, :] = rng.uniform(20, 55, n_cols)
    vf_field[3, :] = rng.uniform(20, 55, n_cols)
    
    # ردیف مرکزی - غنی از الیاف (45 تا 75 درصد)
    vf_field[2, :] = rng.uniform(45, 75, n_cols)
    
    return vf_field

# اگر اسکریپت material_interp در همین پوشه است:
# import material_interp

def create_geometry(L=70.0, t_0=0.25, t_90=0.5):
    """
    ایجاد هندسه مدل [0/90]s در آباکوس
    L: طول نمونه (70 میلی‌متر)
    t_0: ضخامت هر لایه 0 درجه (0.25 میلی‌متر - بالا و پایین)
    t_90: ضخامت کل لایه 90 درجه در وسط (0.5 میلی‌متر برای [0/90]s)
    """
    myModel = mdb.models['Model-1']
    
    # 1. ساخت Part (قطعه) دوبعدی
    mySketch = myModel.ConstrainedSketch(name='profile', sheetSize=200.0)
    t_total = (2 * t_0) + t_90
    mySketch.rectangle(point1=(0.0, 0.0), point2=(L, t_total))
    myPart = myModel.Part(name='Specimen', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    myPart.BaseShell(sketch=mySketch)
    
    # 2. پارتیشن‌بندی ضخامت (ایجاد لایه‌های 0 و 90 درجه)
    # خطوط جداکننده لایه 0 درجه پایین و 90 درجه
    mySketch_part = myModel.ConstrainedSketch(name='partition', sheetSize=200.0)
    mySketch_part.Line(point1=(0.0, t_0), point2=(L, t_0))
    # خط جداکننده 90 درجه و 0 درجه بالا
    mySketch_part.Line(point1=(0.0, t_0 + t_90), point2=(L, t_0 + t_90))
    
    # تقسیم لایه 90 درجه به 5 ردیف (برای توزیع تصادفی خواص)
    row_thickness = t_90 / 5.0
    for i in range(1, 5):
        y_pos = t_0 + (i * row_thickness)
        mySketch_part.Line(point1=(0.0, y_pos), point2=(L, y_pos))
        
    myPart.PartitionFaceBySketch(faces=myPart.faces, sketch=mySketch_part)
    
    print("Geometry and partitions created successfully.")
    return myPart

# برای تست اجرای کد در محیط آباکوس
if __name__ == "__main__":
    create_geometry()
