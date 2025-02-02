from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Annotated, Any, Optional, TypeVar, Union

import pytest

from injection import inject, injectable

T = TypeVar("T")


@injectable
class SomeGenericInjectable[_]: ...


@injectable
class SomeInjectable: ...


class SomeClass: ...


class TestInject:
    @classmethod
    def assert_inject(cls, annotation: Any):
        @inject
        def my_function(instance: annotation):
            assert isinstance(instance, SomeInjectable)

        my_function()

    def test_inject_with_success(self):
        self.assert_inject(SomeInjectable)

    def test_inject_with_annotated(self):
        self.assert_inject(Annotated[SomeInjectable, "metadata"])

    def test_inject_with_union(self):
        self.assert_inject(Union[T, SomeInjectable])

    def test_inject_with_new_union(self):
        self.assert_inject(T | SomeInjectable)

    def test_inject_with_union_and_none(self):
        self.assert_inject(None | SomeInjectable)

    def test_inject_with_annotated_and_union(self):
        self.assert_inject(Annotated[T | SomeInjectable, "metadata"])

    def test_inject_with_optional(self):
        self.assert_inject(Optional[SomeInjectable])

    def test_inject_with_no_parameter(self):
        @inject
        def my_function(): ...

        my_function()

    def test_inject_with_positional_only_parameter(self):
        @inject
        def my_function(instance: SomeInjectable, /, **kw):
            assert isinstance(instance, SomeInjectable)

        my_function()

    def test_inject_with_keyword_variable(self):
        kwargs = {"key": "value"}

        @inject
        def my_function(instance: SomeInjectable, **kw):
            assert kw == kwargs
            assert isinstance(instance, SomeInjectable)

        my_function(**kwargs)

    def test_inject_with_positional_variable(self):
        arguments = ("value",)

        @inject
        def my_function(*args, instance: SomeInjectable = ...):
            assert args == arguments
            assert isinstance(instance, SomeInjectable)

        my_function(*arguments)

    async def test_inject_with_async_function(self):
        class Dependency: ...

        @injectable
        async def recipe() -> Dependency:
            return Dependency()

        @inject
        def my_function_sync(_: Dependency): ...

        with pytest.raises(RuntimeError):
            my_function_sync()

        @inject
        async def my_function_async(instance: Dependency):
            assert isinstance(instance, Dependency)

        await my_function_async()

    async def test_inject_with_deep_async_dependency(self):
        class A: ...

        @injectable
        async def a_recipe() -> A:
            return A()

        @injectable
        class B:
            def __init__(self, a: A):
                self.a = a

        @inject
        async def my_function(b: B):
            assert isinstance(b, B)

        await my_function()

    def test_inject_with_generic_injectable(self):
        @inject
        def my_function(instance: SomeGenericInjectable[str]):
            assert isinstance(instance, SomeGenericInjectable)

        my_function()

    def test_inject_with_scoped_generic_injectable(self):
        class Factory[T](ABC):
            @abstractmethod
            def build(self) -> T:
                raise NotImplementedError

        @injectable(on=Factory[SomeClass])
        class SomeClassFactory(Factory[SomeClass]):
            def build(self) -> SomeClass:
                return SomeClass()

        @inject
        def build(factory: Factory) -> Any:
            raise NotImplementedError

        @inject
        def build_some_class(factory: Factory[SomeClass]) -> SomeClass:
            return factory.build()

        with pytest.raises(TypeError):
            build()

        assert isinstance(build_some_class(), SomeClass)

    def test_inject_with_class(self):
        @inject
        class Class:
            def __init__(self, some_injectable: SomeInjectable):
                self.injectable = some_injectable

        instance = Class()
        assert isinstance(instance.injectable, SomeInjectable)

    def test_inject_with_dataclass(self):
        @inject
        @dataclass(frozen=True, slots=True)
        class DataClass:
            injectable: SomeInjectable = ...

        instance = DataClass()
        assert isinstance(instance.injectable, SomeInjectable)

    def test_inject_with_register_injectable_after_injected_function(self):
        class LateInjectable: ...

        @inject
        def my_function(instance: LateInjectable):
            assert isinstance(instance, LateInjectable)

        with pytest.raises(TypeError):
            my_function()

        @injectable
        def late_injectable_factory() -> LateInjectable:
            return LateInjectable()

        my_function()

    def test_inject_with_str_type_annotation(self):
        @inject
        def my_function(instance: "SomeInjectable"):
            assert isinstance(instance, SomeInjectable)

        my_function()

    def test_inject_with_non_existent_str_type_annotation_raise_type_error(self):
        @inject
        def my_function(instance: "123"):
            raise NotImplementedError

        with pytest.raises(TypeError):
            my_function()

    def test_inject_with_no_injectable_raise_type_error(self):
        @inject
        def my_function(instance: SomeClass):
            raise NotImplementedError

        with pytest.raises(TypeError):
            my_function()

    def test_inject_with_self_injectable(self):
        @injectable
        class A:
            @inject
            def my_method(self, dependency: SomeInjectable):
                assert isinstance(self, A)
                assert isinstance(dependency, SomeInjectable)
                return self

        A.my_method()

        a = A()
        assert a.my_method() is a

    def test_inject_with_class_method(self):
        @injectable
        class A:
            @classmethod
            @inject
            def my_method(cls, dependency: SomeInjectable):
                assert cls is A
                assert isinstance(dependency, SomeInjectable)
                return cls

        A.my_method()

        a = A()
        assert a.my_method() is A

    def test_inject_with_static_method(self):
        @injectable
        class A:
            @staticmethod
            @inject
            def my_method(dependency: SomeInjectable):
                assert isinstance(dependency, SomeInjectable)

        A.my_method()

        a = A()
        assert a.my_method() is None

    def test_inject_with_set_method_in_multiple_class_raise_type_error(self):
        @inject
        def _method(this, _: SomeInjectable = ...):
            return this

        @injectable
        class A:
            method = _method

        with pytest.raises(TypeError):

            @injectable
            class B:
                method = _method

        assert isinstance(A.method(), A)

    def test_inject_with_set_method_after_dependency_resolution_raise_type_error(self):
        @inject
        def _method(this=..., _: SomeInjectable = ...):
            return this

        assert _method() is ...

        with pytest.raises(TypeError):

            @injectable
            class A:
                method = _method
