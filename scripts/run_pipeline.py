# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
from abaqus import mdb
from abaqusConstants import OFF
import inspect

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

REPO_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..'))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from build_mesoscale_model import build_model
from Cohesive_Mat import mesh_continuum_part
from boundaryConditions import setup_assembly_and_run

DEFAULT_JOB_NAME = 'Tensile_Test_Stochastic'

def _parse_bool_flag(args, flag_name): return flag_name in args
def _parse_float(args, name, default_value):
    prefix = '--%s=' % name
    for arg in args:
        if arg.startswith(prefix): return float(arg[len(prefix):])
    return default_value
def _parse_int(args, name, default_value):
    prefix = '--%s=' % name
    for arg in args:
        if arg.startswith(prefix): return int(arg[len(prefix):])
    return default_value
def _abaqus_user_args(argv):
    if '--' in argv: return argv[argv.index('--') + 1:]
    return argv[1:]

def run_pipeline(L=70.0, t_0=0.25, t_90=0.5, rho_sat=8.0, seed=42,
                 element_size=0.125, applied_strain=0.025,
                 save_cae=True, submit_job=False, job_name=DEFAULT_JOB_NAME):
                 
    total_thickness = (2.0 * t_0) + t_90

    print('--- Step 1/3: building mesoscale model ---')
    build_model(L=L, t_0=t_0, t_90=t_90, rho_sat=rho_sat, seed=seed)

    print('--- Step 2/3: Creating materials and uniform continuum mesh ---')
    mesh_continuum_part(element_size=element_size)

    print('--- Step 3/3: creating assembly and BCs ---')
    setup_assembly_and_run(L=L, total_thickness=total_thickness,
                           applied_strain=applied_strain, job_name=job_name)

    print('\n*** PIPELINE PAUSED FOR MANUAL COHESIVE SEAM INSERTION ***')
    print('Please use "Mesh -> Edit -> Element -> Insert cohesive seams" in the GUI.')

if __name__ == '__main__':
    user_args = _abaqus_user_args(sys.argv)
    run_pipeline(
        L=_parse_float(user_args, 'L', 70.0),
        t_0=_parse_float(user_args, 't0', 0.25),
        t_90=_parse_float(user_args, 't90', 0.5),
        rho_sat=_parse_float(user_args, 'rho-sat', 8.0),
        seed=_parse_int(user_args, 'seed', 42),
        element_size=_parse_float(user_args, 'element-size', 0.125),
        applied_strain=_parse_float(user_args, 'strain', 0.025),
        # به صورت پیش‌فرض سابمیت را غیرفعال می‌کنیم
        submit_job=False)
