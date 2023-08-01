# A bunch of utility methods to load and save style files
import pandas as pd
import numpy as np
import os, json
from typing import Dict
from modules.shared import cmd_opts, opts, prompt_styles
import modules.scripts as scripts
import shutil
import datetime
from pathlib import Path
try:
  import pyAesCrypt
except:
  print("No pyAesCrypt - won't be able to do encryption")
from scripts.additionals import Additionals
from scripts.shared import columns, user_columns, display_columns, d_types, name_column

class StyleFile:
  def __init__(self, prefix:str):
    self.prefix = prefix
    self.filename = Additionals.full_path(prefix)
    self.data:pd.DataFrame = self._load()

  def _load(self):
    try:
      data = pd.read_csv(self.filename, header=None, names=columns, 
                              encoding="utf-8-sig", dtype=d_types,
                              skiprows=[0], usecols=[0,1,2])
    except:
      data = pd.DataFrame(columns=columns)

    indices = range(data.shape[0])
    data.insert(loc=0, column="sort", value=[i+1 for i in indices])
    data.fillna('', inplace=True)
    data.insert(loc=4, column="notes", 
                     value=[FileManager.lookup_notes(data['name'][i], self.prefix) for i in indices])
    if len(data)>0:
      for column in user_columns:
        data[column] = data[column].str.replace('\n', '<br>',regex=False)
    return data
  
  @staticmethod
  def sort_dataset(data:pd.DataFrame) -> pd.DataFrame:
    def _to_numeric(series:pd.Series):
      nums = pd.to_numeric(series)
      if any(nums.isna()):
        raise Exception("don't update display")
      return nums
    
    try:
      return data.sort_values(by='sort', axis='index', inplace=False, na_position='first', key=_to_numeric)
    except:
      return data
  
  def save(self):
    self.fix_duplicates()
    clone = self.data.copy()
    if len(clone)>0:
      for column in user_columns:
        clone[column] = clone[column].str.replace('<br>', '\n',regex=False)
    clone.to_csv(self.filename, encoding="utf-8-sig", columns=columns, index=False)

  def fix_duplicates(self):
    names = self.data['name']
    used = set()
    for index, value in names.items():
      if value in used:
        while value in used:
          value = value + "x"
        names.at[index] = value
      used.add(value)

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
  loaded_styles:Dict[str,StyleFile] = {}

  @classmethod
  def clear_style_cache(cls):
    """
    Drop all loaded styles
    """
    cls.loaded_styles = {}

  @classmethod
  def get_current_styles(cls):
    return cls.get_styles(cls._current_prefix())
  
  @classmethod
  def using_additional(cls):
    return cls._current_prefix()!=''
  
  @classmethod
  def get_styles(cls, prefix='') -> pd.DataFrame:
    """
    If prefix is '', this is the default style file.
    Load or retrieve from cache
    """
    if not prefix in cls.loaded_styles:
      cls.loaded_styles[prefix] = StyleFile(prefix)
    return cls.loaded_styles[prefix].data.copy()
  
  @classmethod
  def save_current_styles(cls, data):
    cls.save_styles(data, cls._current_prefix())
    
  @classmethod
  def save_styles(cls, data:pd.DataFrame, prefix=''):
    if not prefix in cls.loaded_styles:
      cls.loaded_styles[prefix] = StyleFile(prefix)
    cls.loaded_styles[prefix].data = data
    cls.loaded_styles[prefix].save()
    
    cls.update_notes_dictionary(data, prefix)
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
    additional_files_as_numpy = { prefix : FileManager.get_styles(prefix=prefix).to_numpy() for prefix in Additionals.additional_style_files(include_new=False, display_names=True) }
    for _, row in cls.get_styles().iterrows():
      prefix, row[1] = Additionals.split_stylename(row[1])
      if prefix:
        if prefix in additional_files_as_numpy:
          additional_files_as_numpy[prefix] = cls.add_or_replace(additional_files_as_numpy[prefix], row)
        else:
          additional_files_as_numpy[prefix] = np.vstack([row])
    for prefix in additional_files_as_numpy:
      cls.save_styles(pd.DataFrame(additional_files_as_numpy[prefix], columns=display_columns), prefix=prefix)

  @classmethod
  def merge_additional_style_files(cls):
    styles = cls.get_styles('')
    styles = styles.drop(index=[i for (i, row) in styles.iterrows() if Additionals.has_prefix(row[1])])
    for prefix in Additionals.prefixes():
      styles_with_prefix = cls.get_styles(prefix=prefix).copy()
      if len(styles_with_prefix)==0:
        os.remove(Additionals.full_path(prefix))
      else:
        styles_with_prefix[name_column] = [Additionals.merge_name(prefix,x) for x in styles_with_prefix[name_column]]
        styles = pd.concat([styles, styles_with_prefix], ignore_index=True)
    styles['sort'] = [i+1 for i in range(len(styles['sort']))]
    cls.save_styles(styles)

  @classmethod
  def _current_prefix(cls):
    return Additionals.display_name(cls.current_styles_file_path)

  @classmethod
  def move_to_additional(cls, maybe_prefixed_style, new_prefix):
    old_prefixed_style = Additionals.prefixed_style(maybe_prefixed_style, cls._current_prefix())
    new_prefixed_style = Additionals.prefixed_style(maybe_prefixed_style, new_prefix, force=True)
    data = cls.get_styles()
    data[name_column] = data[name_column].str.replace(old_prefixed_style, new_prefixed_style)
    cls.save_styles(data)
    cls.remove_from_additional(old_prefixed_style)
    cls.update_additional_style_files()

  @classmethod
  def remove_style(cls, maybe_prefixed_style):
    prefixed_style = Additionals.prefixed_style(maybe_prefixed_style, cls._current_prefix())
    data = cls.get_styles()
    rows_to_drop = [i for (i, row) in data.iterrows() if row[1]==prefixed_style]
    cls.save_styles(data.drop(index=rows_to_drop))
    cls.remove_from_additional(prefixed_style)
    cls.update_additional_style_files()

  @classmethod
  def duplicate_style(cls, maybe_prefixed_style):
    prefixed_style = Additionals.prefixed_style(maybe_prefixed_style, cls._current_prefix())
    data = cls.get_styles()
    new_rows = pd.DataFrame([row for (i, row) in data.iterrows() if row[1]==prefixed_style])
    data = pd.concat([data, new_rows], ignore_index=True)
    data = StyleFile.sort_dataset(data)
    cls.save_styles(data)
    cls.update_additional_style_files()

  @classmethod
  def remove_from_additional(cls, maybe_prefixed_style):
    prefix, style = Additionals.split_stylename(maybe_prefixed_style)
    if prefix:
      data = cls.get_styles(prefix)
      data = data.drop(index=[i for (i, row) in data.iterrows() if row[1]==style])
      cls.save_styles(data, prefix=prefix)

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
      try:
        pyAesCrypt.encryptFile(fileroot+".csv", fileroot+".csv.aes", cls.encrypt_key)
        os.remove(fileroot+".csv")
      except:
        print("Failed to encrypt")

  @classmethod
  def list_backups(cls):
    return [file for file in os.listdir(cls.backup_directory) if (file.endswith('csv') or file.endswith('aes'))]

  @classmethod
  def backup_file_path(cls, file):
    return os.path.join(cls.backup_directory, file)
  
  @classmethod
  def restore_from_backup(cls, file):
    path = cls.backup_file_path(file)
    if not os.path.exists(path):
      return "Invalid selection"
    if os.path.splitext(file)[1]==".aes":
      try:
        temp = os.path.join(cls.backup_directory, "temp.aes")
        temd = os.path.join(cls.backup_directory, "temp.csv")
        shutil.copyfile(file,temp)
        pyAesCrypt.decryptFile(temp, temd, cls.encrypt_key)
        os.rename(temd, cls.default_style_file_path)
      except:
        error = "Failed to decrypt .aes file"
      finally:
        if os.path.exists(temp):
          os.remove(temp)
        if os.path.exists(temd):
          os.remove(temd)
    else:
      shutil.copyfile(path, cls.default_style_file_path)
    return None

  
  @classmethod
  def restore_from_upload(cls, tempfile):
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