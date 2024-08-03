class Field:
    def __init__(self, default=Ellipsis, default_factory=None, metadata=None):
        self.default = default
        self.default_factory = default_factory
        self.metadata = metadata if metadata is not None else {}

    def __repr__(self):
        return f"Field(default={self.default}, default_factory={self.default_factory}, metadata={self.metadata})"


def field(*, default=Ellipsis, default_factory=None, metadata=None):
    return Field(default, default_factory, metadata)


def dataclass(*, frozen=False, order=False):
    def wrapper(cls):
        fields = {name: attr for name, attr in cls.__annotations__.items()}
        defaults = {name: getattr(cls, name, Ellipsis) for name in fields}
        
        def __init__(self, *args, **kwargs):
            if frozen:
                object.__setattr__(self, '_frozen', False)
            for i, (name, attr_type) in enumerate(fields.items()):
                value = kwargs.pop(name, args[i] if i < len(args) else Ellipsis)
                if value is Ellipsis:
                    if isinstance(defaults[name], Field):
                        if defaults[name].default is not Ellipsis:
                            value = defaults[name].default
                        elif defaults[name].default_factory:
                            value = defaults[name].default_factory()
                        else:
                            raise TypeError(f"Missing required argument: '{name}'")
                    else:
                        value = defaults[name]
                object.__setattr__(self, name, value)
            if frozen:
                object.__setattr__(self, '_frozen', True)
        
        setattr(cls, '__init__', __init__)
        
        def __repr__(self):
            field_strs = [f"{name}={getattr(self, name)!r}" for name in fields]
            return f"{cls.__name__}({', '.join(field_strs)})"
        
        setattr(cls, '__repr__', __repr__)
        
        def __eq__(self, other):
            if not isinstance(other, cls):
                return NotImplemented
            return all(getattr(self, name) == getattr(other, name) for name in fields)
        
        setattr(cls, '__eq__', __eq__)
        
        def __setattr__(self, name, value):
            if frozen and getattr(self, '_frozen', False):
                raise AttributeError(f"Cannot assign to field '{name}'")
            super(cls, self).__setattr__(name, value)
        
        setattr(cls, '__setattr__', __setattr__)
        
        def __hash__(self):
            return hash(tuple(getattr(self, name) for name in fields))
        
        setattr(cls, '__hash__', __hash__)

        if order:
            def lt(self, other):
                if not isinstance(other, cls):
                    return NotImplemented
                for name in fields:
                    self_val = getattr(self, name)
                    other_val = getattr(other, name)
                    if self_val < other_val:
                        return True
                    elif self_val > other_val:
                        return False
                return False
            
            def le(self, other):
                return self == other or lt(self, other)
            
            def gt(self, other):
                return not le(self, other)
            
            def ge(self, other):
                return not lt(self, other)

            cls.__lt__ = lt
            cls.__le__ = le
            cls.__gt__ = gt
            cls.__ge__ = ge
        
        cls.__dataclass_fields__ = fields
        
        return cls
    return wrapper


def asdict(obj):
    if not hasattr(obj, '__dataclass_fields__'):
        raise TypeError("asdict() should be called on dataclass instances")
    result = {}
    for name in obj.__dataclass_fields__:
        value = getattr(obj, name)
        if isinstance(value, list):
            result[name] = list(value)
        elif hasattr(value, '__dataclass_fields__'):
            result[name] = asdict(value)
        else:
            result[name] = value
    return result
