# diconfig User Manual

[Zh](https://github.com/zisull/diconfig/blob/main/README.md) / [En](https://github.com/zisull/diconfig/blob/main/doc/README-en.md)

## 1. Overview

```cmd
pip install diconfig
```

`diconfig` is a convenient, flexible, and efficient configuration manager that supports various common configuration file formats (such as `json`, `toml`, `yaml`, `ini`, `xml`). It allows for easy reading and writing of configuration files in Python projects, while also providing flexible data handling methods and practical features like automatic saving and backup.

`dict <-> config file [json, toml, yaml, ini, xml]`  ==> Dictionary - Configuration - Management

## 2. Class Structure and Functions

### (1) Config Class

#### Initialization Parameters

- `data` (`dict`, optional): Configuration data passed in dictionary format, default is `None`. If not provided, an empty dictionary structure will be initialized.
- `file` (`str`, optional): Configuration file name, which can be without an extension or with a specified extension, default value is `"config"`. If no extension is provided, the default format specified by the `way` parameter will be added.
- `way` (`str`, optional): Configuration file format, supports `json`, `toml`, `ini`, `xml`, `yaml`, default value is `"toml"`. The provided format will be validated to ensure it is supported.
- `replace` (`bool`, optional): Whether to overwrite existing configuration files, default value is `False`.
- `auto_save` (`bool`, optional): Whether to automatically save configuration changes, default value is `True`.
- `backup` (`bool`, optional): Whether to back up the original configuration file, default value is `False`.

#### Properties

- `json`: Returns the configuration data as a `json` formatted string (serialized using the `orjson` library, with an indentation of 2 spaces).
- `dict`: Returns the configuration data in dictionary format, can also be used to set configuration data through the `setter` method (achieved by calling the `set_data` method).
- `str`: Returns the configuration data in a plain string format (essentially the result of calling the `dict` property).
- `file_path`: Returns the configuration file path (corresponding to the provided `file` parameter, possibly with the added extension).
- `file_path_abs`: Returns the absolute path of the configuration file.

##### Main Methods

- `read(key: str, default=None)`: Reads the configuration value based on the provided key (supports multi-level keys separated by `.` similar to dictionary access). Returns the default value if the key does not exist.
- `write(key: str, value, overwrite_mode: bool = False)`: Writes a configuration item. When there is a conflict in the dictionary path in the configuration file, the `overwrite_mode` parameter can decide whether to overwrite the existing path, default is not to overwrite. If auto-saving is enabled (`auto_save=True`), the configuration file will be automatically saved after the write operation is completed.
- `del_clean()`: Clears configuration items and attempts to delete the configuration file. Returns `True` if successful; returns `False` if the file does not exist or deletion fails.
- `update(data: dict)`: Updates or adds configuration items, recursively merging the configuration items from the provided dictionary into the existing configuration data. If auto-saving is enabled, the configuration file will be automatically saved after the operation is completed.
- `set_data(data: dict)`: Sets the complete configuration data, overwriting the existing configuration data. If auto-saving is enabled, the configuration file will be automatically saved after the operation is completed.
- `del_key(key: str)`: Deletes the corresponding configuration item based on the provided key. After deletion, it checks if the parent node is empty; if so, it will also delete it. If auto-saving is enabled, the configuration file will be automatically saved after the operation is completed.
- `load(file: str = None, way: str = None)`: Loads a configuration file. The file path and format to be loaded can be specified through parameters; if not specified, the corresponding parameter values from initialization will be used.
- `save()`: Saves the configuration file. The actual save operation will only be executed if there are changes in the configuration data (marked by the `mark_dirty` method).
- `auto_save(on_off: bool = True)`: Sets whether to automatically save configuration changes.
- `save_to_file(file: str = None, way: str = None)`: Saves the configuration data to a specified file without changing the original configuration file format and properties. If parameters are not specified, it saves to the current configuration's corresponding file.

###    

## 3. Usage Examples and Precautions

### (1) Basic Usage Example

```python
# Example of read and write methods
from diconfig import Config

cc = Config()
cc.write('School Name', 'University')
cc.School.Date = "2021-01-01"
print(cc.read('School.Date'))
print(cc['School Name'])
print(cc.School.Date)
print(cc)
cc.pop('School Name')
print(cc)
cc.clear()  # Clear configuration data in dictionary way
print(cc)
cc.del_clean()

# Example of setting values in dictionary way
cc = Config()
cc.dict = {'Location': 'Beijing', 'Books': {'Quantity': 100, 'Price': 10.5}, 'Students': {'Quantity': 1000, 'Age': 20}}
print(cc)
cc.del_clean()

# Forced overwrite example
dic_ = {'School': 'pass'}
cc = Config(data=dic_)
cc.write('School.University', 'University',
         overwrite_mode=True)  # overwrite_mode=True forces overwrite but will delete the original path
print(cc)
cc.del_clean()
```

### (2) Precautions

- When using single-level property assignment like `cc.a = 100` (only one `.`), although it can successfully assign and read values, this operation will not save to `data` and the configuration file, nor will it trigger auto-saving. Only when using multi-level property assignment (e.g., `cc.a.b = 200`, with two or more `.`), or explicitly calling `write`, `update`, `set_data`, and other related saving methods, will the configuration data be saved to the file and update the internal `data` property, depending on the `auto_save` setting to decide whether to auto-save.

- When using the `write` method, if there is a conflict in the dictionary path, be cautious in choosing whether to enable the `overwrite_mode` parameter. Enabling it will overwrite the existing path, which may lead to data loss in the original path.

## Conclusion

The author has limited skills, and it is not recommended for use in large projects. During my learning of Python, I still clearly remember the confusion I faced when dealing with configuration file read and write operations as a beginner. Therefore, I created a simple, convenient, and user-friendly configuration library aimed at simplifying the read and write process of configuration files as much as possible, allowing users to operate configuration information in a more intuitive and convenient way.

November 19, 2024   zisull@qq.com
