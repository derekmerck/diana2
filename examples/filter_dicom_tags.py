# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 18:39:07 2020

@author: ben
"""

import SimpleITK as sitk
from glob import glob
import os
import os.path
import pydicom
import shutil
import sys
import re

input_folder = '/Users/3dlab/Desktop/liqi/unzipped'
output_folder = '/Users/3dlab/Desktop/liqi/outputs'

convert_to_nrrd = False
copy_file = False
move_file = False

# must have "dicom tag" and "inclusion criteria"
# if multiple inclusion criteria are specified:
#   you can specify "inclusion criteria relationship" to be either "and" or "or" (default: "and")
#       "and" means that every inclusion criteria must be met by at least one item in the dicom tag values
#       "or" means that only one value-inclusion criteria pair must be found
#"inclusion criteria" can be in the following formats (note: the space is important):
#   "== string/number"
#   "= string/number" (treat as ==)
#   "string/number" (treat as ==)
#   "!= string/number"
#   "> string/number" (for string, this means it is strictly contained in the dicom tag but is not an exact match)
#   ">= string/number" (for string, this means it is contained in the dicom tag and can be an exact match)
#   "< string/number" (for string, this means the dicom tag is strictly contained in it but is not an exact match)
#   "<= string/number" (for string, this means the dicom tag is contained in it and can be an exact match)
#   "contain string" (treat as >=)
#   "!contain string"

criteria_nonaxial = {
     "dicom tag": "ImageType",
     "inclusion criteria": ["!= AXIAL"],
     }

criteria_CT = {
     "dicom tag": "Modality",
     "inclusion criteria": ["CT"]
     }

criteria_axial = {
     "dicom tag": "ImageType",
     "inclusion criteria": ["AXIAL"],
    }

criteria_thick = {
     "dicom tag": "SliceThickness",
     "inclusion criteria": ["== 5"]
     }

criteria_superthick = {
     "dicom tag": "SliceThickness",
     "inclusion criteria": ["> 5"]
     }

criteria_thin = {
     "dicom tag": "SliceThickness",
     "inclusion criteria": ["< 5"]
     }

inclusion_criteria = [criteria_CT]

structure_thickness = {
     "dicom tag": "SliceThickness",
     "suffix": "mm",
     "number format": "{:.3f}"
     }

strcuture_accession = {
     "dicom tag": "AccessionNumber"
     }

structure_series = {
     "prefix": "Series",
     "dicom tag": "SeriesNumber",
     "number format": "{:.0f}"
     }

# must have "dicom tag"
# optional: "prefix", "suffix", "number format"
output_folder_structure = []

# must have "dicom tag"
# optional: "prefix", "suffix", "number format"
output_name_structure = [strcuture_accession, structure_series]

report = False
report_details = False

# do not change "list": []
counters = [
    {
     "dicom tag": "AccessionNumber",
     "list": []
     }
    ]

def check_dir(path):
    path_exists = os.path.exists(path)
    if not path_exists:
        if report:
            print(f"creating folder at {path}")
        os.makedirs(path)

def get_criteria(inclusion_criterium):
    dicom_tag = inclusion_criterium["dicom tag"]
    dicom_tag_match_list = inclusion_criterium["inclusion criteria"]
    andor = inclusion_criterium.get("inclusion criteria relationship")
    return dicom_tag, dicom_tag_match_list, andor

def get_folder_name(path):
    path_hierarchy = path.split('\\')
    name = path_hierarchy[-1]
    return name

#lists must be iterated outside this function
def check_inclusion_criterium(basic_dicom_value, inclusion_criterium):
    parsed_inclusion_criterium = inclusion_criterium.split(' ')
    if isinstance(basic_dicom_value, float):
        parsed_inclusion_criterium[-1] = float(parsed_inclusion_criterium[-1])
    operator = parsed_inclusion_criterium[0]
    target = parsed_inclusion_criterium[-1]
    if len(parsed_inclusion_criterium) == 1 or operator == "=" or operator == "==":
        return basic_dicom_value == target
    elif operator == "!=":
        return basic_dicom_value != target
    elif isinstance(basic_dicom_value, float):
        if operator == ">":
            return basic_dicom_value > target
        elif operator == ">=":
            return basic_dicom_value >= target
        elif operator == "<":
            return basic_dicom_value < target
        elif operator == "<=":
            return basic_dicom_value <= target
        else:
            print(f"unable to compare {basic_dicom_value} and {inclusion_criteria}")
            return False
    elif isinstance(basic_dicom_value, str):
        if "!contain" in operator:
            return not target in basic_dicom_value
        elif "contain" in operator or ">=" in operator:
            return target in basic_dicom_value
        elif ">" in operator:
            return target in basic_dicom_value and not target == basic_dicom_value
        elif "<=" in operator:
            return basic_dicom_value in target
        elif "<" in operator:
            return basic_dicom_value in target and not target == basic_dicom_value
        else:
            print(f"unable to compare {basic_dicom_value} and {inclusion_criteria}")
            return False
    else:
        print(f"unable to compare {basic_dicom_value} and {inclusion_criteria}")
        return False

#TODO: if inclusion criterium[0] == '!', apply a series of "and not"s
def meets_inclusion_criterium(dicom_value_list, inclusion_criteria, inclusion_criteria_relationship = "and"):
    if inclusion_criteria_relationship == "or":
        for inclusion_criterium in inclusion_criteria:
            not_criterium = inclusion_criterium[0] == '!'
            if not_criterium:
                not_matched = True
                for dicom_value in dicom_value_list:
                    not_matched = check_inclusion_criterium(dicom_value, inclusion_criterium)
                if not not_matched:
                    break
            else:
                for dicom_value in dicom_value_list:
                    if check_inclusion_criterium(dicom_value, inclusion_criterium):
                        return True
        return False
    else:
        for inclusion_criterium in inclusion_criteria:
            not_criterium = inclusion_criterium[0] == '!'
            if not_criterium:
                for dicom_value in dicom_value_list:
                    if not check_inclusion_criterium(dicom_value, inclusion_criterium):
                        return False
            else:
                matched = False
                for dicom_value in dicom_value_list:
                    matched = check_inclusion_criterium(dicom_value, inclusion_criterium)
                    if matched:
                        break
                if not matched:
                    return False
        return True

def is_iterable(item):
    if isinstance(item, str):
        return False
    try:
        iter(item)
        return True
    except TypeError:
        return False

def is_number(string):
    numerical_format = re.compile(r"([0-9]+)|([0-9]+\.[0-9]*)")
    return numerical_format.fullmatch(string)

def to_known_types(dicom_value):
    if isinstance(dicom_value, str):
        return dicom_value
    if is_iterable(dicom_value):
        for i in range(0,len(dicom_value)):
            dicom_value[i] = to_known_types(dicom_value[i])
        return dicom_value
    dicom_value = str(dicom_value)
    if is_number(dicom_value):
        return float(str(dicom_value))
    return dicom_value

def meets_inclusion_criteria(dicom):
    for inclusion_criterium in inclusion_criteria:
        dicom_value = dicom.get(inclusion_criterium["dicom tag"])
        dicom_value = to_known_types(dicom_value)
        if not is_iterable(dicom_value):
            dicom_value = [dicom_value]
        dicom_tag_match_list = inclusion_criterium["inclusion criteria"]
        inclusion_criteria_relationship = inclusion_criterium.get("inclusion criteria relationship")
        if inclusion_criteria_relationship is None:
            inclusion_criteria_relationship = "and"
        if not meets_inclusion_criterium(dicom_value, dicom_tag_match_list, inclusion_criteria_relationship):
            return False
    return True

def format_number(item, number_format):
    if isinstance(item, float):
        return number_format.format(item)
    return item

def format_dicom_tag_by_specification(dicom_value, specification, apply_prefix = True, apply_suffix = True):
    dicom_value = to_known_types(dicom_value)
    if not isinstance(dicom_value, str):
        if is_iterable(dicom_value):
            subname = format_dicom_tag_by_specification(dicom_value[0], specification, False, False)
            for i in range(1, len(dicom_value)):
                subname = subname+'_'+format_dicom_tag_by_specification(dicom_value[i], specification, False, False)
            dicom_value = subname
        elif isinstance(dicom_value, float):
            number_format = specification.get("number format")
            if number_format is not None:
                dicom_value = number_format.format(dicom_value)
            else:
                dicom_value = str(dicom_value)
        else:
            dicom_value = str(dicom_value)
    name = dicom_value
    if apply_prefix:
        prefix = specification.get("prefix")
        if prefix is not None:
            name = prefix+name
    if apply_suffix:
        suffix = specification.get("suffix")
        if suffix is not None:
            name = name+suffix
    return name

def build_name_from_hierarchy(dicom, specification_hierarchy, connector):
    name = ""
    if specification_hierarchy:
        base_specification = specification_hierarchy[0]
        base_dicom_value = dicom.get(base_specification["dicom tag"])
        name = format_dicom_tag_by_specification(base_dicom_value, base_specification)
        for i in range(1,len(specification_hierarchy)):
            specification = specification_hierarchy[i]
            dicom_value = dicom.get(specification["dicom tag"])
            name_part = format_dicom_tag_by_specification(dicom_value, specification)
            name = name+connector+name_part
    return name

def apply_counters(dicom):
    for counter in counters:
        target_dicom_tag = counter["dicom tag"]
        dicom_value = dicom.get(target_dicom_tag)
        existing_values = counter["list"]
        if not dicom_value in existing_values:
            existing_values.append(dicom_value)
            if report_details:
                print(f"found the {len(existing_values)}th accession number: {dicom_value}")

def convert(output_folder, image_folder):
    image_dir = glob(image_folder+'/*.dcm')
    num_images = len(image_dir)
    sufficient_images = num_images > 5
    if not sufficient_images:
        return 0
   
    series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(image_folder)
    nb_series = len(series_IDs)
    if nb_series == 0:
        return 0
   
    for i in range(nb_series):
        series_file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(image_folder, series_IDs[i])
        s = series_file_names[0]
        with pydicom.dcmread(s) as dicom:
            if not meets_inclusion_criteria(dicom):
                return 0
            apply_counters(dicom)
           
            save_folder = output_folder
            case_specific_folders = build_name_from_hierarchy(dicom, output_folder_structure, connector='/')
            if case_specific_folders:
                save_folder = output_folder+'/'+case_specific_folders
            check_dir(save_folder)
            file_name = build_name_from_hierarchy(dicom, output_name_structure, connector='_')
            if report:
                print(f"saving to {save_folder+'/'+file_name}")
            if convert_to_nrrd:
                #generating 3D image to save as nrrd
                series_reader = sitk.ImageSeriesReader()
                series_reader.SetFileNames(series_file_names)
                try:
                    image3D = series_reader.Execute()
                    sitk.WriteImage(image3D, save_folder+"/"+file_name+'.nrrd')
                except RuntimeError:
                    with open(output_folder+'/errors_log.txt', 'a') as file:
                        file.write(file_name+'\n')
                        file.close()
                    pass
            if copy_file:
                shutil.copytree(src=image_folder, dst=save_folder+'/dicom/'+file_name)
            if move_file:
                shutil.move(src=image_folder, dst=save_folder+'/dicom/'+file_name)
inclusion_criteria = [criteria_CT, criteria_nonaxial, criteria_thin]
output_folder = '/Users/3dlab/Desktop/liqi/outputs/NonaxialThinImage'
convert_to_nrrd = True
copy_file = True
counters = [{
     "dicom tag": "AccessionNumber",
     "list": []
     }]
scan_count = execute(input_folder)
print(f"{scan_count} number of nonaxial thin ct scans")
print_counts()
write_to_file("nonaxial_thin_ct.txt", counters[0]["list"])

inclusion_criteria = [criteria_CT, criteria_nonaxial, criteria_thick]
output_folder = '/Users/3dlab/Desktop/liqi/outputs/NonaxialThickImage'
convert_to_nrrd = True
copy_file = True
counters = [{
     "dicom tag": "AccessionNumber",
     "list": []
     }]
scan_count = execute(input_folder)
print(f"{scan_count} number of nonaxial thick ct scans")
print_counts()
write_to_file("nonaxial_thick_ct.txt", counters[0]["list"])

inclusion_criteria = [criteria_CT, criteria_nonaxial, criteria_superthick]
output_folder = '/Users/3dlab/Desktop/liqi/outputs/NonaxialSuperThickImage'
convert_to_nrrd = True
copy_file = True
counters = [{
     "dicom tag": "AccessionNumber",
     "list": []
     }]
scan_count = execute(input_folder)
print(f"{scan_count} number of nonaxial super thick ct scans")
print_counts()
write_to_file("nonaxial_super_thick_ct.txt", counters[0]["list"])

inclusion_criteria = [criteria_CT, criteria_axial, criteria_thin]
output_folder = '/Users/3dlab/Desktop/liqi/outputs/ThinImage'
convert_to_nrrd = False
copy_file = True
counters = [{
     "dicom tag": "AccessionNumber",
     "list": []
     }]
scan_count = execute(input_folder)
print(f"{scan_count} number of thin axial ct scans")
print_counts()
write_to_file("thin_axial_ct.txt", counters[0]["list"])

inclusion_criteria = [criteria_CT, criteria_axial, criteria_thick]
output_folder = '/Users/3dlab/Desktop/liqi/outputs/ThickImage'
convert_to_nrrd = False
copy_file = True
counters = [{
     "dicom tag": "AccessionNumber",
     "list": []
     }]
scan_count = execute(input_folder)
print(f"{scan_count} number of thick axial ct scans")
print_counts()
write_to_file("thick_axial_ct.txt", counters[0]["list"])

inclusion_criteria = [criteria_CT, criteria_axial, criteria_superthick]
output_folder = '/Users/3dlab/Desktop/liqi/outputs/SuperThickImage'
convert_to_nrrd = False
copy_file = True

counters = [{
     "dicom tag": "AccessionNumber",
     "list": []
     }]
scan_count = execute(input_folder)
print(f"{scan_count} number of super thick axial ct scans")
print_counts()
write_to_file("super_thick_axial_ct.txt", counters[0]["list"])

	
	
	
