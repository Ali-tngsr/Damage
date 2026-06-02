# -*- coding: utf-8 -*-
"""Extract basic stress-strain and damage indicators from an Abaqus ODB.

Run with Abaqus Python, for example:
    abaqus python scripts/postprocess_odb.py Tensile_Test_Stochastic.odb
"""
from __future__ import print_function

import csv
import os
import sys

from odbAccess import openOdb

JOB_NAME = 'Tensile_Test_Stochastic'
STEP_NAME = 'Step-1'
INSTANCE_NAME = 'SPECIMEN_INST'
PLY90_SET_NAME = 'PLY90_FACES'
CRACK_SET_NAME = 'CRACK_PATHS'


def _safe_get(dictionary, key):
    if key in dictionary.keys():
        return dictionary[key]
    return None


def _mean(values):
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _element_labels_from_set(element_set):
    labels = {}
    if element_set is None:
        return labels
    for element in element_set.elements:
        labels[element.label] = True
    return labels


def extract_results(odb_path, output_csv=None, L=70.0, width=20.0, thickness=1.0):
    if output_csv is None:
        output_csv = os.path.splitext(os.path.basename(odb_path))[0] + '_summary.csv'

    odb = openOdb(odb_path, readOnly=True)
    try:
        step = odb.steps[STEP_NAME]
        instance = odb.rootAssembly.instances[INSTANCE_NAME]
        ply90_labels = _element_labels_from_set(_safe_get(instance.elementSets, PLY90_SET_NAME))
        crack_labels = _element_labels_from_set(_safe_get(instance.elementSets, CRACK_SET_NAME))

        rows = []
        area = width * thickness
        for frame in step.frames:
            frame_value = frame.frameValue
            strain = frame_value
            if frame_value > 1.0:
                strain = frame_value / L

            stress_values = []
            if 'S' in frame.fieldOutputs.keys():
                stress_field = frame.fieldOutputs['S']
                for value in stress_field.values:
                    if (not ply90_labels) or (value.elementLabel in ply90_labels):
                        stress_values.append(float(value.data[0]))
            sigma90 = _mean(stress_values)

            rf_total = 0.0
            if 'RF' in frame.fieldOutputs.keys():
                for value in frame.fieldOutputs['RF'].values:
                    if len(value.data) > 0:
                        rf_total += float(value.data[0])
            global_stress = rf_total / area if area > 0.0 else 0.0

            damaged = 0
            total_damage_values = 0
            for damage_name in ('SDEG', 'DMICRT'):
                if damage_name in frame.fieldOutputs.keys():
                    for value in frame.fieldOutputs[damage_name].values:
                        if (not crack_labels) or (value.elementLabel in crack_labels):
                            total_damage_values += 1
                            if float(value.data) >= 0.95:
                                damaged += 1
                    break

            rows.append({
                'frame': len(rows),
                'frame_value': frame_value,
                'strain': strain,
                'sigma90_mpa': sigma90,
                'global_stress_mpa': global_stress,
                'damaged_cohesive_values': damaged,
                'damage_values_checked': total_damage_values,
            })
    finally:
        odb.close()

    with open(output_csv, 'w') as handle:
        writer = csv.DictWriter(handle, fieldnames=('frame', 'frame_value', 'strain',
                                                    'sigma90_mpa', 'global_stress_mpa',
                                                    'damaged_cohesive_values',
                                                    'damage_values_checked'))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print('Wrote %d frames to %s' % (len(rows), output_csv))
    return output_csv


if __name__ == '__main__':
    odb_file = JOB_NAME + '.odb'
    if len(sys.argv) > 1:
        odb_file = sys.argv[-1]
    extract_results(odb_file)
