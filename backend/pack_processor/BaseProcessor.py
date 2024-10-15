from abc import ABCMeta, abstractmethod


class ProcessorMeta(ABCMeta):
    _registry = {}

    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        ProcessorMeta._registry[name] = new_cls
        return new_cls

    @classmethod
    def create(cls, class_name, *args, **kwargs):
        if class_name in cls._registry:
            return cls._registry[class_name](*args, **kwargs)
        else:
            raise ValueError(f"Class {class_name} not found")


class ProcessorBase(metaclass=ProcessorMeta):
    def __init__(self):
        self.offset = 0
        self.size = 0

    @abstractmethod
    def load(self, xml_filename):
        pass

    @abstractmethod
    def pack(self, data):
        pass
