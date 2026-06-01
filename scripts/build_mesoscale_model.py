# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *
import regionToolset
import numpy as np

def assign_vf_field(n_cols, n_rows=5, seed=None):
    """
    تولید میدان تصادفی کسر حجمی (Vf) بر اساس قوانین استوکاستیک مقاله.
    این نسخه با مفسر قدیمی NumPy در داخل نرم‌افزار ABAQUS سازگار شده است.
    """
    # تنظیم Seed برای تکرارپذیری نتایج به روش کلاسیک
    if seed is not None:
        np.random.seed(seed)
        
    vf_field = np.zeros((n_rows, n_cols))
    
    # ردیف‌های مرزی (مجاورت لایه 0) -> غنی از رزین (0 تا 30)
    vf_field[0, :] = np.random.uniform(0, 30, n_cols)
    vf_field[4, :] = np.random.uniform(0, 30, n_cols)
    
    # ردیف‌های انتقالی -> (20 تا 55)
    vf_field[1, :] = np.random.uniform(20, 55, n_cols)
    vf_field[3, :] = np.random.uniform(20, 55, n_cols)
    
    # ردیف مرکزی -> غنی از الیاف (45 تا 75)
    vf_field[2, :] = np.random.uniform(45, 75, n_cols)
    
    return vf_field

def build_full_mesoscale_model(L=70.0, t_0=0.25, t_90=0.5, rho_sat=8.0, seed=42):
    """
    ساخت کامل هندسه و پارتیشن‌بندی دو بعدی متقاطع در آباکوس
    L: طول گیج نمونه (70 میلی‌متر)
    t_0: ضخامت لایه 0 درجه
    t_90: ضخامت لایه 90 درجه
    rho_sat: چگالی اشباع ترک‌ها (تعداد ترک در هر میلی‌متر)
    """
    myModel = mdb.models['Model-1']
    t_total = (2 * t_0) + t_90
    
    # 1. محاسبه تعداد ستون‌ها (پتانسیل‌های مسیر ترک) بر اساس پارامترهای مقاله
    n_cols = int(np.round(rho_sat * L))
    dx = L / float(n_cols)
    print("Number of vertical columns (crack paths) to create: {}".format(n_cols))
    
    # 2. ساخت قطعه (Part) مبنا
    mySketch = myModel.ConstrainedSketch(name='profile', sheetSize=200.0)
    mySketch.rectangle(point1=(0.0, 0.0), point2=(L, t_total))
    myPart = myModel.Part(name='Specimen', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    myPart.BaseShell(sketch=mySketch)
    
    # 3. ایجاد پارتیشن‌های افقی (لایه‌های ضخامتی)
    mySketch_horiz = myModel.ConstrainedSketch(name='horiz_partition', sheetSize=200.0)
    mySketch_horiz.Line(point1=(0.0, t_0), point2=(L, t_0))
    mySketch_horiz.Line(point1=(0.0, t_0 + t_90), point2=(L, t_0 + t_90))
    
    row_thickness = t_90 / 5.0
    for i in range(1, 5):
        y_pos = t_0 + (i * row_thickness)
        mySketch_horiz.Line(point1=(0.0, y_pos), point2=(L, y_pos))
        
    myPart.PartitionFaceBySketch(faces=myPart.faces, sketch=mySketch_horiz)
    
    # 4. ایجاد پارتیشن‌های عمودی (ستون‌های ساختاری راستای X)
    mySketch_vert = myModel.ConstrainedSketch(name='vert_partition', sheetSize=200.0)
    for j in range(1, n_cols):
        x_pos = j * dx
        mySketch_vert.Line(point1=(x_pos, 0.0), point2=(x_pos, t_total))
        
    myPart.PartitionFaceBySketch(faces=myPart.faces, sketch=mySketch_vert)
    
    # 5. تولید ماتریس توزیع تصادفی کسر حجمی الیاف
    vf_field = assign_vf_field(n_cols, n_rows=5, seed=seed)
    
    print("Full grid geometry with {} cells created successfully.".format(n_cols * 5))
    return myPart, vf_field

if __name__ == "__main__":
    # اجرای تابع اصلی
    specimen_part, generated_vf = build_full_mesoscale_model()
