# A bunch of utility methods to load and save style files
import pandas as pd
import numpy as np
import os, json
from modules.shared import cmd_opts, opts, prompt_styles
import modules.scripts as scripts
import shutil
import datetime
from pathlib import Path
import pyAesCrypt
from scripts.additionals import Additionals
from scripts.shared import columns, user_columns, display_columns, d_types

class FileManager:
  basedir = scripts.basedir()
  additional_style_files_directory = os.path.join(basedir,"additonal_style_files")
  backup_directory = os.path.join(basedir,"backups")
  if not os.path.exists(backup_directory):
    os.mkdir(backup_directory)
  if not os.path.exists(additional_style_files_directory):
    os.mkdir(additional_style_files_directory)

  try:
    default_style_file_path = cmd_opts.styles_file 
  except:
    default_style_file_path = getattr(opts, 'styles_dir', None)
  current_styles_file_path = default_style_file_path

  Additionals.init(default_style_file_path=default_style_file_path, additional_style_files_directory=additional_style_files_directory)

  try:
    with open(os.path.join(basedir, "notes.json")) as f:
      notes_dictionary = json.load(f)
  except:
    notes_dictionary = {}

  encrypt = False
  encrypt_key = ""
  
  @classmethod
  def load_styles(cls, filename=None, use_default=False) -> pd.DataFrame:
    filename = filename or (cls.default_style_file_path if use_default else cls.current_styles_file_path)
    try:
      dataframe = pd.read_csv(filename, header=None, names=columns, encoding="utf-8-sig", dtype=d_types,
                                  engine='python', skiprows=[0], usecols=[0,1,2])
    except:
      dataframe = pd.DataFrame(columns=columns)
    display = Additionals.display_name(filename)
    entries = range(dataframe.shape[0])
    dataframe.insert(loc=0, column="sort", value=[i+1 for i in entries])
    dataframe.insert(loc=4, column="notes", value=[cls.lookup_notes(dataframe['name'][i], display) for i in entries])
    dataframe.fillna('', inplace=True)
    if len(dataframe)>0:
      for column in user_columns:
        dataframe[column] = dataframe[column].str.replace('\n', '<br>',regex=False)
    return dataframe
  
  @classmethod
  def fix_duplicates(cls, data:pd.DataFrame):
    names = data['name']
    used = set()
    for index, value in names.items():
      if value in used:
        while value in used:
          value = value + "x"
        names.at[index] = value
      used.add(value)
  
  @classmethod
  def save_styles(cls, data:pd.DataFrame, filename=None, use_default=False):
    filename = filename or (cls.default_style_file_path if use_default else cls.current_styles_file_path)
    clone = data.copy()
    cls.fix_duplicates(clone)
    if len(clone)>0:
      for column in user_columns:
        clone[column] = clone[column].str.replace('<br>', '\n',regex=False)
    clone.to_csv(filename, encoding="utf-8-sig", columns=columns, index=False)
    cls.update_notes_dictionary(data, Additionals.display_name(filename))
    cls.save_notes_dictionary()
    prompt_styles.reload()
  
  @staticmethod
  def create_file_if_missing(filename):
    filename = Additionals.full_path(filename)
    if not os.path.exists(filename):
      print("", file=open(filename,"w"))

  @staticmethod
  def add_or_replace(array:np.ndarray, row):
    for i in range(len(array)):
      if array[i][1] == row[1]:
        array[i] = row
        return array
    return np.vstack([array,row])

  @classmethod
  def update_additional_style_files(cls):
    additional_file_contents = { prefix : FileManager.load_styles(Additionals.full_path(prefix)).to_numpy() for prefix in Additionals.additional_style_files(include_blank=False, display_names=True) }
    for _, row in cls.load_styles(use_default=True).iterrows():
      prefix, row[1] = Additionals.split_stylename(row[1])
      if prefix:
        if prefix in additional_file_contents:
          additional_file_contents[prefix] = cls.add_or_replace(additional_file_contents[prefix], row)
        else:
          additional_file_contents[prefix] = np.vstack([row])
    for prefix in additional_file_contents:
      cls.save_styles(pd.DataFrame(additional_file_contents[prefix], columns=display_columns), filename=Additionals.full_path(prefix))

  @classmethod
  def remove_from_additional(cls, prefixed_style):
    prefix, style = Additionals.split_stylename(prefixed_style)
    if prefix:
      data = cls.load_styles(Additionals.full_path(prefix))
      data = data.drop(index=[i for (i, row) in data.iterrows() if row[1]==style])
      cls.save_styles(data, Additionals.full_path(prefix))

  @classmethod
  def do_backup(cls):
    fileroot = os.path.join(cls.backup_directory, datetime.datetime.now().strftime("%y%m%d_%H%M"))
    if not os.path.exists(cls.default_style_file_path):
      return
    shutil.copyfile(cls.default_style_file_path, fileroot+".csv")
    paths = sorted(Path(cls.backup_directory).iterdir(), key=os.path.getmtime, reverse=True)
    for path in paths[24:]:
      os.remove(str(path))
    if cls.encrypt and len(cls.encrypt_key)>0:
      pyAesCrypt.encryptFile(fileroot+".csv", fileroot+".csv.aes", cls.encrypt_key)
      os.remove(fileroot+".csv")

  @classmethod
  def restore_from_backup(cls, tempfile):
    error = None
    if os.path.exists(cls.default_style_file_path):
      if os.path.exists(cls.default_style_file_path+".temp"):
        os.remove(cls.default_style_file_path+".temp")
      os.rename(cls.default_style_file_path, cls.default_style_file_path+".temp")
    if os.path.splitext(tempfile)[1]==".aes":
      try:
        pyAesCrypt.decryptFile(tempfile, cls.default_style_file_path, cls.encrypt_key)
      except:
        error = "Failed to decrypt .aes file"
    elif os.path.splitext(tempfile)[1]==".csv":
      os.rename(tempfile, cls.default_style_file_path)
    else:
      error = "Can only restore from .csv or .aes file"
    if os.path.exists(cls.default_style_file_path+".temp"):    
      if os.path.exists(cls.default_style_file_path):
        os.remove(cls.default_style_file_path+".temp")
      else:
        os.rename(cls.default_style_file_path+".temp", cls.default_style_file_path)
    return error
  
  @classmethod
  def save_notes_dictionary(cls):
    print(json.dumps(cls.notes_dictionary),file=open(os.path.join(cls.basedir, "notes.json"), 'w'))   

  @classmethod
  def update_notes_dictionary(cls, data:pd.DataFrame, prefix:str):
    for _, row in data.iterrows():
      stylename = prefix+"::"+row[1] if prefix!='' else row[1]
      cls.notes_dictionary[stylename] = row[4]

  @classmethod
  def lookup_notes(cls, stylename, prefix):
    stylename = prefix+"::"+stylename if prefix!='' else stylename
    return cls.notes_dictionary[stylename] if stylename in cls.notes_dictionary else ''