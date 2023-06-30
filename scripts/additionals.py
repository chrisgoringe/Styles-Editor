import os

class Additionals:
  @classmethod
  def init(cls, default_style_file_path, additional_style_files_directory) -> None:
    cls.default_style_file_path = default_style_file_path
    cls.additional_style_files_directory = additional_style_files_directory

  @staticmethod
  def has_prefix(fullname:str):
    """
    Return true if the fullname is prefixed.
    """
    return ('::' in fullname)
  
  @staticmethod
  def split_stylename(fullname:str):
    """
    Split a stylename in the form [prefix::]name into prefix, name or None, name
    """
    if '::' in fullname:
      return fullname[:fullname.find('::')], fullname[fullname.find('::')+2:]
    else:
      return None, fullname
    
  @staticmethod
  def merge_name(prefix:str, name:str):
    """
    Merge prefix and name into prefix::name (or name, if prefix is none or '')
    """
    if prefix:
      return prefix+"::"+name
    else:
      return name
    
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
  def additional_style_files(cls, include_blank=True, display_names=False):
    format = cls.display_name if display_names else cls.full_path
    additional_style_files = [format(f) for f in os.listdir(cls.additional_style_files_directory) if f.endswith(".csv")]
    return [format('')]+additional_style_files if include_blank else additional_style_files