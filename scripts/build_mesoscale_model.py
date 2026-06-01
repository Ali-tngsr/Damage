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
