# -*- coding: utf-8 -*-
# @author: zisull@qq.com
# @date: 2024年11月19日

import configparser
import os
import xml.etree.ElementTree as ElementTree
from collections.abc import MutableMapping
from threading import Lock

import orjson
import toml
import yaml


class Config:
    """Args:
        data: 配置数据，字典格式
        file: 配置文件名，可以不带扩展名，默认 config,也可以指定任意扩展名,不影响 way 参数.
        way: 配置文件格式，支持 json, toml, ini, xml, yaml, 默认 toml
        replace: 是否覆盖已有配置文件,默认False
        auto_save: 是否自动保存,默认True
        backup: 是否备份原配置文件,默认False

配置管理器，支持多种格式的配置文件，并提供读写操作。dict <=> [ini, xml, json, toml, yaml]\n
注意 __setattr__ ：\n
1. cc.write("a", 100) 当无节时候[ini]会分配一个'默认'节
2.当只有一个 '.' ，例如 cc.a = 100，能够成功赋值读值，但是不会保存到data和配置文件，也不会触发自动保存。\n
3.当有两个及以上 '.' ，例如 cc.a.b = 200，会保存到data和配置文件，也会触发自动保存。\n
cc = Diconfig(way="toml")\n
cc.a = 100 # 不会保存到data和配置文件，也不会触发自动保存\n
cc.a.b = 200 # 会保存到data和配置文件，也会触发自动保存\n
你可以选择 cc.write("a", 100) 赋值单.状态，也可以用 cc.update({"a": 100}) 批量赋值,也可以用 cc.set_data({"a": 100}) 完全赋值。
"""

    def __init__(self, data: dict = None, file: str = "config", way: str = "toml", replace: bool = False,
                 auto_save: bool = True, backup: bool = False):
        self.way = self.validate_format(way)
        self.file = self.ensure_extension(file)
        self.auto_save = auto_save
        self.data = ConfigNode(data if data is not None else {}, manager=self)
        self._dirty = False if data is not None else True
        self.backup = backup
        self._lock = Lock()
        self.handler = ConfigHandlerFactory.get_handler(self.way)

        if os.path.exists(self.file) and not replace:
            self._load()
        else:
            self.save()

    @property
    def json(self) -> str:
        """返回配置数据，json格式"""
        return orjson.dumps(self.dict, option=orjson.OPT_INDENT_2).decode('utf-8')

    @property
    def dict(self) -> dict:
        """返回配置数据，字典格式"""
        return self.data.to_dict()

    @dict.setter
    def dict(self, value: dict):
        """设置配置数据，字典格式"""
        self.set_data(value)  # 调用 set_data 方法将字典数据赋值给

    @property
    def auto_save(self) -> bool:
        """返回是否自动保存"""
        return self._auto_save

    @auto_save.setter
    def auto_save(self, value: bool):
        """设置是否自动保存"""
        self._auto_save = value

    @property
    def backup(self) -> bool:
        """返回是否备份原配置文件"""
        return self._backup

    @backup.setter
    def backup(self, value: bool):
        """设置是否备份原配置文件"""
        self._backup = value

    @property
    def str(self) -> str:
        """返回配置数据，字符串格式"""
        return str(self.dict)

    @property
    def file_path(self) -> str:
        """返回配置文件路径"""
        return self.file

    @property
    def file_path_abs(self) -> str:
        """返回配置文件绝对路径"""
        return os.path.abspath(self.file)

    def read(self, key: str, default=None):
        """返回 配置值 or 默认值 """
        keys = key.split('.')
        node = self.data
        for k in keys:
            if isinstance(node, ConfigNode):
                node = node.data.get(k, None)
                if isinstance(node, dict):
                    node = ConfigNode(node, manager=self)
                elif node is None:
                    return default
            else:
                return default
        return node

    def write(self, key: str, value, overwrite_mode: bool = False):
        """写 配置项,配置值,覆写模式 (用于字典路径冲突时候,是否覆写已有路径,默认不覆盖
        例如 write a.b.c = 1, a.b = 2, 将会丢失a.b.c的值,反之则会丢失a.b的值"""
        self.mark_dirty()
        keys = key.split('.')
        node = self.data

        for k in keys[:-1]:
            if overwrite_mode:
                if isinstance(node, ConfigNode):
                    if k not in node.data or not isinstance(node.data[k], dict):
                        node.data[k] = {}
                else:
                    node.data = {k: {}}
                node = node[k]
            else:
                node = getattr(node, k)

        setattr(node, keys[-1], value)

        if self.auto_save:
            self.save()

    def del_clean(self):
        """清空配置项,删除配置文件"""
        self.mark_dirty()
        with self._lock:
            if os.path.exists(self.file):
                try:
                    os.remove(self.file)
                    self.data = ConfigNode({}, manager=self)
                    return True
                except OSError as e:
                    print(f"清除配置文件 {self.file} 失败：{e}")
            else:
                print(f"配置文件 {self.file} 不存在，无法清除")
            return False

    def update(self, data: dict):
        """更新添加配置项"""
        self.mark_dirty()
        self._recursive_update(self.data.data, data)
        if self.auto_save:
            self.save()

    def set_data(self, data: dict):
        """设置完整配置数据,也可以用 dict 属性来设置"""
        self.mark_dirty()
        self.data = ConfigNode(data, manager=self)
        if self.auto_save:
            self.save()

    def del_key(self, key: str):
        """删除配置项"""
        self.mark_dirty()
        keys = key.split('.')
        if not keys:
            return
        node = self.data
        parent_nodes = []
        for k in keys[:-1]:
            parent_nodes.append((node, k))
            node = getattr(node, k, None)
            if node is None:
                return
        final_key = keys[-1]
        if final_key in node.data:
            del node.data[final_key]
            while parent_nodes:
                parent, key_in_parent = parent_nodes.pop()
                if not parent[key_in_parent].data:
                    del parent[key_in_parent]
                else:
                    break
            if self.auto_save:
                self.save()

    def _load(self):
        with self._lock:
            try:
                with open(self.file, 'rb' if self.way == "json" else 'r',
                          encoding=None if self.way == "json" else 'utf-8') as f:
                    raw_data = self.handler.load(f)
                    self.data = ConfigNode(raw_data, manager=self)
            except Exception as e:
                print(f"加载配置文件 {self.file} 失败：{e}")

    def load(self, file: str = None, way: str = None):
        if file:
            self.file = file
        if way:
            self.way = way.lower()
            self.handler = ConfigHandlerFactory.get_handler(self.way)
        self._load()

    def mark_dirty(self):
        """改动标记,用于判断是否需要保存,一般不用自己调用"""
        self._dirty = True

    def save(self):
        """保存配置文件"""
        with self._lock:
            if not self._dirty:
                return
            try:
                self._backup_file()
                self._ensure_file_exists()
                with open(self.file, 'wb' if self.way == "json" else 'w',
                          encoding=None if self.way == "json" else 'utf-8') as f:
                    self.handler.save(self.data.to_dict(), f)
                self._dirty = False
            except Exception as e:
                print(f"保存配置文件失败 {self.file}: {e}")

    def save_to_file(self, file: str = None, way: str = None):
        """不会改变原有方式,另存到指定文件"""
        with self._lock:
            try:
                # 使用局部变量来存储文件路径和格式
                target_file = self.ensure_extension(file) if file else self.file
                target_way = self.validate_format(way) if way else self.way
                target_handler = ConfigHandlerFactory.get_handler(target_way)

                # 确保文件存在
                self._ensure_file_exists()

                # 打开文件并保存数据
                with open(target_file, 'wb' if target_way == "json" else 'w',
                          encoding=None if target_way == "json" else 'utf-8') as f:
                    target_handler.save(self.data.to_dict(), f)

                print(f"配置已成功另存到 {target_file}")
            except Exception as e:
                print(f"另存配置文件失败 {target_file}: {e}")

    def _ensure_file_exists(self):
        if not os.path.exists(self.file):
            with open(self.file, 'w'):
                pass  # 创建一个空文件

    def _backup_file(self):
        if os.path.exists(self.file) and self.backup:
            backup_file = self.file + '.bak'
            try:
                os.replace(self.file, backup_file)
            except Exception as e:
                print(f"备份文件失败: {e}")

    def _recursive_update(self, original, new_data):
        """递归更新配置项"""
        for key, value in new_data.items():
            if isinstance(value, dict) and isinstance(original.get(key, None), dict):
                self._recursive_update(original[key], value)
            else:
                if original.get(key) != value:  # 检查是否真的发生了变化
                    original[key] = value
                    self.mark_dirty()  # 标记数据已更改

    @staticmethod
    def validate_format(_way):
        """验证并返回格式"""
        _way = _way.lower()
        way_list = ['json', 'toml', 'yaml', 'ini', 'xml']
        if _way not in way_list:
            raise ValueError(f"Unsupported format: {_way}. Supported formats are: {', '.join(way_list)}")
        return _way

    def ensure_extension(self, file):
        """确保文件名有正确的扩展名"""
        if not os.path.splitext(file)[1]:
            file += f".{self.way}"
        return file

    def __str__(self):
        return str(self.dict)

    def __repr__(self):
        return repr(self.dict)

    def __getattr__(self, item: str):
        return getattr(self.data, item)

    def __getitem__(self, item: str):
        return self.data[item]

    def __call__(self, key: str, dvalue=None):
        return self.read(key, dvalue)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, item):
        return item in self.data

    def __bool__(self):
        return bool(self.data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()


class ConfigHandler:
    def load(self, file):
        raise NotImplementedError

    def save(self, data, file):
        raise NotImplementedError


class JSONConfigHandler(ConfigHandler):
    def load(self, file):
        return orjson.loads(file.read())

    def save(self, data, file):
        file.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))


class TOMLConfigHandler(ConfigHandler):
    def load(self, file):
        return toml.load(file)

    def save(self, data, file):
        file.write(toml.dumps(data))


class YAMLConfigHandler(ConfigHandler):
    def load(self, file):
        return yaml.safe_load(file)

    def save(self, data, file):
        yaml.dump(data, file, allow_unicode=True)


class INIConfigHandler(ConfigHandler):
    def load(self, file):
        config = configparser.ConfigParser()
        config.read_file(file)
        return {s: dict(config.items(s)) for s in config.sections()}

    def save(self, data, file):
        config = configparser.ConfigParser()
        # 如果 data 不是嵌套字典，包装在一个默认的 section 中
        if not all(isinstance(v, dict) for v in data.values()):
            data = {'默认': data}
        config.read_dict(data)
        config.write(file)


class XMLConfigHandler(ConfigHandler):
    def load(self, file):
        tree = ElementTree.parse(file)
        root = tree.getroot()
        return self._element_to_dict(root)

    def save(self, data, file):
        root = self._dict_to_element('config', data)
        tree = ElementTree.ElementTree(root)
        # 使用 'utf-8' 编码保存文件，并确保 write() 方法接收的是字符串流
        tree.write(file, encoding='unicode', xml_declaration=True)

    def _element_to_dict(self, element):
        data = {}
        for child in element:
            if len(child):  # If the child has children, it's a nested structure
                data[child.tag] = self._element_to_dict(child)
            else:
                data[child.tag] = child.text
        return data

    def _dict_to_element(self, tag, data):
        element = ElementTree.Element(tag)
        for key, value in data.items():
            if isinstance(value, dict):
                child = self._dict_to_element(key, value)
            else:
                child = ElementTree.Element(key)
                child.text = str(value)
            element.append(child)
        return element


class ConfigHandlerFactory:
    handlers = {
        'json': JSONConfigHandler(),
        'toml': TOMLConfigHandler(),
        'yaml': YAMLConfigHandler(),
        'ini': INIConfigHandler(),
        'xml': XMLConfigHandler(),  # Added XML handler
    }

    @staticmethod
    def get_handler(_format):
        handler = ConfigHandlerFactory.handlers.get(_format)
        if not handler:
            raise ValueError(f"Unsupported format: {_format}")
        return handler


class ConfigNode(MutableMapping):
    def __init__(self, data=None, manager=None, parent=None, key_in_parent=None):
        self._data = data if data is not None else {}
        self._manager = manager
        self._parent = parent
        self._key_in_parent = key_in_parent

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self._trigger_save()

    def _trigger_save(self):
        if self._manager:
            self._manager.mark_dirty()
            if self._manager.auto_save:
                self._manager.save()

    def __getitem__(self, key):
        value = self._data.get(key)
        if isinstance(value, dict):
            return ConfigNode(value, manager=self._manager, parent=self, key_in_parent=key)
        elif value is not None:
            return value
        else:
            raise KeyError(f"Key '{key}' not found.")

    def __setitem__(self, key, value):
        self._data[key] = value
        self._trigger_save()

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]
            self._trigger_save()
        else:
            raise KeyError(f"Key '{key}' not found.")

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getattr__(self, key):
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                return ConfigNode(value, manager=self._manager, parent=self, key_in_parent=key)
            else:
                return value
        else:
            self._data[key] = {}
            return ConfigNode(self._data[key], manager=self._manager, key_in_parent=key)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self._data[key] = value
            self._trigger_save()

    def to_dict(self):
        return {key: (value.to_dict() if isinstance(value, ConfigNode) else value)
                for key, value in self._data.items()}

    def __repr__(self):
        return repr(self.to_dict())


if __name__ == "__main__":
    pass
