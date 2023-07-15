from typing import Iterable, TypeVar, overload

_T = TypeVar("_T")

def get_instance(reference: type[_T]) -> _T: ...
def inject(*): ...
def new(*, reference: type = ...): ...
@overload
def new(*, references: Iterable[type] = ...): ...
def unique(*, reference: type = ...): ...
@overload
def unique(*, references: Iterable[type] = ...): ...
