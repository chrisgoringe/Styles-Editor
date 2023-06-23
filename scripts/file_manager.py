# A bunch of utility methods to load and save style files
import pandas as pd
import os, json
from modules.shared import cmd_opts, opts, prompt_styles
import modules.scripts as scripts
import shutil
import datetime
from pathlib import Path
import pyAesCrypt

class FileManager:
  columns = ['name','prompt','negative_prompt']

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
      dataframe = pd.read_csv(filename, header=None, names=cls.columns, encoding="utf-8-sig",
                                  engine='python', skiprows=[0], usecols=[0,1,2])
    except:
      dataframe = pd.DataFrame(columns=cls.columns)
    display = cls.display_name(filename)
    entries = range(dataframe.shape[0])
    dataframe.insert(loc=0, column="sort", value=[i+1 for i in entries])
    dataframe.insert(loc=4, column="notes", value=[cls.lookup_notes(dataframe['name'][i], display) for i in entries])
    dataframe.fillna('', inplace=True)
    return dataframe
  
  @classmethod
  def save_styles(cls, data:pd.DataFrame, filename=None, use_default=False):
    filename = filename or (cls.default_style_file_path if use_default else cls.current_styles_file_path)
    data.to_csv(filename, encoding="utf-8-sig", columns=cls.columns, index=False)
    cls.update_notes_dictionary(data, cls.display_name(filename))
    cls.save_notes_dictionary()
    prompt_styles.reload()
  
  @classmethod
  def create_file_if_missing(cls, filename):
    filename = cls.full_path(filename)
    if not os.path.exists(filename):
      print("", file=open(filename,"w"))

  @classmethod
  def do_backup(cls):
    fileroot = os.path.join(cls.backup_directory, datetime.datetime.now().strftime("%y%m%d_%H%M"))
    shutil.copyfile(FileManager.default_style_file_path, fileroot+".csv")
    shutil.make_archive(fileroot,format="zip",root_dir=cls.additional_style_files_directory,base_dir='.')
    paths = sorted(Path(cls.backup_directory).iterdir(), key=os.path.getmtime, reverse=True)
    for path in paths[24:]:
      os.remove(str(path))
    cls.changed_since_backup = False
    if cls.encrypt and len(cls.encrypt_key)>0:
      for extension in [".csv",".zip"]:
        pyAesCrypt.encryptFile(fileroot+extension, fileroot+extension+".aes", cls.encrypt_key)
        os.remove(fileroot+extension)

  @classmethod
  def full_path(cls, filename:str) -> str:
    """
    Return the full path for an additional style file.
    Input can be the full path, the filename with extension, or the filename without extension.
    If input is None, '', or the default style file path, return the default style file path
    """
    if filename is None or filename=='' or filename==cls.default_style_file_path:
      return cls.default_style_file_path
    filename = filename+".csv" if not filename.endswith(".csv") else filename
    return os.path.relpath(os.path.join(cls.additional_style_files_directory,os.path.split(filename)[1]))
                           
  @classmethod
  def display_name(cls, filename:str) -> str:
    """
    Return the full path for an additional style file. 
    Input can be the full path, the filename with extension, or the filename without extension
    """
    fullpath = cls.full_path(filename)
    return os.path.splitext(os.path.split(fullpath)[1])[0] if fullpath!=cls.default_style_file_path else ''
  
  @classmethod
  def save_notes_dictionary(cls):
    print(json.dumps(cls.notes_dictionary),file=open(os.path.join(cls.basedir, "notes.json"), 'w'))   

  @classmethod
  def update_notes_dictionary(cls, data:pd.DataFrame, prefix:str):
    for row in data.iterrows():
      stylename = prefix+"::"+row[1][1] if prefix!='' else row[1][1]
      cls.notes_dictionary[stylename] = row[1][4]

  @classmethod
  def lookup_notes(cls, stylename, prefix):
    stylename = prefix+"::"+stylename if prefix!='' else stylename
    return cls.notes_dictionary[stylename] if stylename in cls.notes_dictionary else ''