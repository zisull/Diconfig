# diconfig 使用说明文档

[Zh](https://github.com/zisull/diconfig/blob/main/README.md)  / [En](https://github.com/zisull/diconfig/blob/main/doc/README-en.md)

## 一、概述

```cmd
pip install diconfig
```

`diconfig` 是一个方便, 灵活, 高效的配置管理器，支持多种常见的配置文件格式（如 `json`、`toml`、`yaml`、`ini`、`xml`），能够方便地在
Python 项目中进行配置文件的读写操作，同时提供了灵活的数据处理方式以及自动保存、备份等实用功能。

`dict <-> config file[json, toml, yaml, ini, xml]`  == > Dictionary - Configuration - Management

## 二、类结构与功能

### （一）Config 类

#### 初始化参数

  - `data`（`dict`，可选）：配置数据，以字典格式传入，默认为 `None`，若未传入则初始化一个空字典结构。
  - `file`（`str`，可选）：配置文件名，可以不带扩展名或者指定扩展名，默认值为 `"config"`。不带扩展名会加上默认方式的扩展名。
    `way` 参数指定的格式。
  - `way`（`str`，可选）：配置文件格式，支持 `json`、`toml`、`ini`、`xml`、`yaml`，默认值为 `"toml"`。传入的格式会经过验证，确保是受支持的格式。
  - `replace`（`bool`，可选）：是否覆盖已有配置文件，默认值为 `False`。
  - `auto_save`（`bool`，可选）：是否自动保存配置更改，默认值为 `True`。
  - `backup`（`bool`，可选）：是否备份原配置文件，默认值为 `False`。

#### 属性

  - `json`：返回配置数据的 `json` 格式字符串（使用 `orjson` 库进行序列化，缩进为 2 个空格）。
  - `dict`：返回配置数据的字典格式，通过 `setter` 方法也可用于设置配置数据（调用 `set_data` 方法实现赋值）。
  - `str`：返回配置数据的普通字符串格式（其实就是调用 `dict` 属性转换后的结果）。
  - `file_path`：返回配置文件路径（与传入的 `file` 参数对应，可能添加扩展名后的文件名）。
  - `file_path_abs`：返回配置文件的绝对路径。

##### 主要方法

- `read(key: str, default=None)`：根据传入的键（支持用 `.` 分割的多级键，类似字典的多级访问）读取配置值，如果键不存在则返回默认值。
- `write(key: str, value, overwrite_mode: bool = False)`：写入配置项，当配置文件中已有字典路径冲突时，可通过
  `overwrite_mode` 参数决定是否覆写已有路径，默认不覆盖。若开启自动保存（`auto_save=True`），写入操作完成后会自动保存配置文件。
- `del_clean()`：清空配置项，并尝试删除配置文件。操作成功返回 `True`，若文件不存在或删除失败则返回 `False`。
- `update(data: dict)`：更新或添加配置项，递归地将传入字典中的配置项合并到已有配置数据中，若开启自动保存，操作完成后会自动保存配置文件。
- `set_data(data: dict)`：设置完整的配置数据，会覆盖原有的配置数据，若开启自动保存，操作完成后会自动保存配置文件。
- `del_key(key: str)`：根据传入的键删除对应的配置项，删除后会检查父级节点是否为空，若为空也一并删除，若开启自动保存，操作完成后会自动保存配置文件。
- `load(file: str = None, way: str = None)`：加载配置文件，可通过参数指定要加载的文件路径和文件格式，若未指定则使用初始化时的对应参数值。
- `save()`：保存配置文件，只有在配置数据有更改（通过 `mark_dirty` 方法标记）时才会执行实际的保存操作。
- `auto_save(on_off: bool = True)`：设置是否自动保存配置更改。
- `save_to_file(file: str = None, way: str = None)`：将配置数据另存到指定文件，不会改变原有的配置文件格式和路径等属性，若不指定参数则保存到当前配置对应的文件。

###    

## 三、使用示例与注意事项

### （一）基本使用示例

```python
# 读写方法示例
from diconfig import Config

cc = Config()
cc.write('学校名称', '大学')
cc.学校.日期 = "2021-01-01"
print(cc.read('学校.日期'))
print(cc['学校名称'])
print(cc.学校.日期)
print(cc)
cc.pop('学校名称')
print(cc)
cc.clear()  # 字典方式清空配置data
print(cc)
cc.del_clean()

# 字典方式设置值示例
cc = Config()
cc.dict = {'地点': '北京', '图书': {'数量': 100, '价格': 10.5}, '学生': {'数量': 1000, '年龄': 20}}
print(cc)
cc.del_clean()

# 强制覆写示例
dic_ = {'学校': 'pass'}
cc = Config(data=dic_)
cc.write('学校.大学', '大学', overwrite_mode=True)  # overwrite_mode=True 强制覆写，但会导致原路径被删除
print(cc)
cc.del_clean()
```

### （二）注意事项

- 在使用类似 `cc.a = 100` 这种单级属性赋值方式（只有一个 `.`）时，虽然能够成功赋值和读值，但该操作不会保存到 `data`
  和配置文件，也不会触发自动保存。只有当使用多级属性赋值（例如 `cc.a.b = 200`，有两个及以上 `.`），或者显式调用 `write`、
  `update`、`set_data` 等相关保存方法时，配置数据才会保存到文件以及更新内部的 `data` 属性，并根据 `auto_save` 设置决定是否自动保存。

- 在使用 `write` 方法时，如果存在字典路径冲突，需要谨慎选择是否开启 `overwrite_mode` 参数，开启会覆写已有路径，可能导致原路径下的数据丢失。

## 尾语

作者水平有限，如果你是使用大型项目不建议使用。在学习Python的过程中，我仍清晰地记得当初初学时候面对配置文件读写操作时的那种迷茫状态。我便动手写了一个简单、方便且极具人性化的配置库，旨在尽可能简化配置文件的读写流程，让使用者可以用一种更加直观、便捷的方式去操作配置信息。

2024 年 11 月 19 日   zisull@qq.com
