import numpy as np
import pandas as pd
import os

def get_properties(Vf_target, csv_path='../data/table1_properties.csv'):
    """
    درون‌یابی خواص مکانیکی بر اساس کسر حجمی الیاف
    """
    # خواندن داده‌ها از فایل CSV
    try:
        data = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}")
        return None

    Vf_data = data['Vf'].values
    
    props = {}
    properties_list = ['E11', 'nu12', 'E22', 'nu23', 'YT', 'G12', 'G23']
    
    for prop in properties_list:
        arr = data[prop].values
        # درون‌یابی خطی
        props[prop] = float(np.interp(Vf_target, Vf_data, arr))
        
    return props

# تست اسکریپت
if __name__ == "__main__":
    test_vf = 45.0
    print(f"Testing for Vf = {test_vf}% :")
    print(get_properties(test_vf))
