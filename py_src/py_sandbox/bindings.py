from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple
import wasmer # type: ignore

try:
    from typing import Protocol
except ImportError:
    class Protocol: # type: ignore
        pass


def _load(make_view: Callable[[], Any], mem: wasmer.Memory, base: int, offset: int) -> Any:
    ptr = (base & 0xffffffff) + offset
    view = make_view()
    if ptr + view.bytes_per_element > mem.data_size:
        raise IndexError('out-of-bounds load')
    view_ptr = ptr // view.bytes_per_element
    return view[view_ptr]

def _decode_utf8(mem: wasmer.Memory, ptr: int, len: int) -> str:
    ptr = ptr & 0xffffffff
    len = len & 0xffffffff
    if ptr + len > mem.data_size:
        raise IndexError('string out of bounds')
    view = mem.uint8_view()
    bytes = bytearray(view[ptr:ptr+len])
    x = bytes.decode('utf8')
    return x

def _encode_utf8(val: str, realloc: wasmer.Function, mem: wasmer.Memory) -> Tuple[int, int]:
    bytes = val.encode('utf8')
    ptr = realloc(0, 0, 1, len(bytes))
    assert(isinstance(ptr, int))
    ptr = ptr & 0xffffffff
    if ptr + len(bytes) > mem.data_size:
        raise IndexError('string out of bounds')
    view = mem.uint8_view()
    view[ptr:ptr+len(bytes)] = bytes
    return (ptr, len(bytes))
@dataclass
class Stdout:
    out: str
    err: str

@dataclass
class Value:
    value: str
    datatype: str

@dataclass
class Evalresult:
    stdout: 'Stdout'
    value: Optional['Value']

class Sandbox:
    instance: wasmer.Instance
    _canonical_abi_free: wasmer.Function
    _canonical_abi_realloc: wasmer.Function
    _eval: wasmer.Function
    _exec: wasmer.Function
    _memory: wasmer.Memory
    def __init__(self, store: wasmer.Store, imports: dict[str, dict[str, Any]], module: wasmer.Module):
        self.instance = wasmer.Instance(module, imports)
        
        canonical_abi_free = self.instance.exports.__getattribute__('canonical_abi_free')
        assert(isinstance(canonical_abi_free, wasmer.Function))
        self._canonical_abi_free = canonical_abi_free
        
        canonical_abi_realloc = self.instance.exports.__getattribute__('canonical_abi_realloc')
        assert(isinstance(canonical_abi_realloc, wasmer.Function))
        self._canonical_abi_realloc = canonical_abi_realloc
        
        eval = self.instance.exports.__getattribute__('eval')
        assert(isinstance(eval, wasmer.Function))
        self._eval = eval
        
        exec = self.instance.exports.__getattribute__('exec')
        assert(isinstance(exec, wasmer.Function))
        self._exec = exec
        
        memory = self.instance.exports.__getattribute__('memory')
        assert(isinstance(memory, wasmer.Memory))
        self._memory = memory
    def exec(self, code: str) -> 'Stdout':
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        ptr, len0 = _encode_utf8(code, realloc, memory)
        ret = self._exec(ptr, len0)
        assert(isinstance(ret, int))
        load = _load(memory.int32_view, memory, ret, 0)
        load1 = _load(memory.int32_view, memory, ret, 4)
        ptr2 = load
        len3 = load1
        list = _decode_utf8(memory, ptr2, len3)
        free(ptr2, len3, 1)
        load4 = _load(memory.int32_view, memory, ret, 8)
        load5 = _load(memory.int32_view, memory, ret, 12)
        ptr6 = load4
        len7 = load5
        list8 = _decode_utf8(memory, ptr6, len7)
        free(ptr6, len7, 1)
        return Stdout(list, list8)
    def eval(self, expr: str) -> 'Evalresult':
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        ptr, len0 = _encode_utf8(expr, realloc, memory)
        ret = self._eval(ptr, len0)
        assert(isinstance(ret, int))
        load = _load(memory.int32_view, memory, ret, 0)
        load1 = _load(memory.int32_view, memory, ret, 4)
        ptr2 = load
        len3 = load1
        list = _decode_utf8(memory, ptr2, len3)
        free(ptr2, len3, 1)
        load4 = _load(memory.int32_view, memory, ret, 8)
        load5 = _load(memory.int32_view, memory, ret, 12)
        ptr6 = load4
        len7 = load5
        list8 = _decode_utf8(memory, ptr6, len7)
        free(ptr6, len7, 1)
        load9 = _load(memory.uint8_view, memory, ret, 16)
        option: Optional['Value']
        if load9 == 0:
            option = None
        elif load9 == 1:
            load10 = _load(memory.int32_view, memory, ret, 20)
            load11 = _load(memory.int32_view, memory, ret, 24)
            ptr12 = load10
            len13 = load11
            list14 = _decode_utf8(memory, ptr12, len13)
            free(ptr12, len13, 1)
            load15 = _load(memory.int32_view, memory, ret, 28)
            load16 = _load(memory.int32_view, memory, ret, 32)
            ptr17 = load15
            len18 = load16
            list19 = _decode_utf8(memory, ptr17, len18)
            free(ptr17, len18, 1)
            option = Value(list14, list19)
        else:
            raise TypeError("invalid variant discriminant for option")
        return Evalresult(Stdout(list, list8), option)
