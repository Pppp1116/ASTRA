"""
Comprehensive tests for astra.symbols module.

Tests symbol table management including:
- SymbolInfo creation
- GlobalSymbolTable immutability
- MutableSymbolTable builder
- SymbolTableBuilder
- Symbol validation
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from astra.symbols import (
    SymbolInfo,
    GlobalSymbolTable,
    MutableSymbolTable,
    SymbolTableBuilder,
    build_global_symbol_table,
    validate_symbol_consistency,
)
from astra.ast import (
    FnDecl,
    ExternFnDecl,
    StructDecl,
    EnumDecl,
    TypeAliasDecl,
    ImportDecl,
    Program,
)


def test_symbol_info_creation():
    """Test SymbolInfo creation"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    info = SymbolInfo(
        name="test",
        symbol_type="fn",
        decl=fn,
        file_path="test.astra",
        span_info=(10, 5, 100)
    )

    assert info.name == "test"
    assert info.symbol_type == "fn"
    assert info.decl is fn
    assert info.file_path == "test.astra"
    assert info.span_info == (10, 5, 100)


def test_symbol_info_immutable():
    """Test that SymbolInfo is immutable"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    info = SymbolInfo(
        name="test",
        symbol_type="fn",
        decl=fn,
        file_path="test.astra"
    )

    with pytest.raises(Exception):  # Should raise FrozenInstanceError or AttributeError
        info.name = "changed"


def test_symbol_info_default_span():
    """Test SymbolInfo with default span"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    info = SymbolInfo(
        name="test",
        symbol_type="fn",
        decl=fn,
        file_path="test.astra"
    )

    assert info.span_info == (0, 0, 0)


def test_global_symbol_table_empty():
    """Test empty GlobalSymbolTable"""
    table = GlobalSymbolTable()

    assert len(table.functions) == 0
    assert len(table.structs) == 0
    assert len(table.enums) == 0
    assert len(table.type_aliases) == 0
    assert len(table.extern_functions) == 0
    assert len(table.global_scope) == 0


def test_global_symbol_table_get_function_overloads():
    """Test getting function overloads"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    info = SymbolInfo(name="test", symbol_type="fn", decl=fn, file_path="test.astra")

    table = GlobalSymbolTable(functions={"test": (info,)})

    overloads = table.get_function_overloads("test")
    assert len(overloads) == 1
    assert overloads[0] is info


def test_global_symbol_table_get_function_overloads_empty():
    """Test getting nonexistent function overloads"""
    table = GlobalSymbolTable()

    overloads = table.get_function_overloads("nonexistent")
    assert overloads == tuple()


def test_global_symbol_table_get_struct():
    """Test getting struct"""
    struct = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    info = SymbolInfo(name="Point", symbol_type="struct", decl=struct, file_path="test.astra")

    table = GlobalSymbolTable(structs={"Point": info})

    result = table.get_struct("Point")
    assert result is info


def test_global_symbol_table_get_struct_nonexistent():
    """Test getting nonexistent struct"""
    table = GlobalSymbolTable()

    result = table.get_struct("Nonexistent")
    assert result is None


def test_global_symbol_table_get_enum():
    """Test getting enum"""
    enum = EnumDecl(name="Color", generics=[], variants=[], doc="")
    info = SymbolInfo(name="Color", symbol_type="enum", decl=enum, file_path="test.astra")

    table = GlobalSymbolTable(enums={"Color": info})

    result = table.get_enum("Color")
    assert result is info


def test_global_symbol_table_get_type_alias():
    """Test getting type alias"""
    alias = TypeAliasDecl(name="MyInt", generics=[], target="Int")
    info = SymbolInfo(name="MyInt", symbol_type="type_alias", decl=alias, file_path="test.astra")

    table = GlobalSymbolTable(type_aliases={"MyInt": info})

    result = table.get_type_alias("MyInt")
    assert result is info


def test_global_symbol_table_get_extern_function():
    """Test getting extern function"""
    extern = ExternFnDecl(lib="libc.so", name="exit", params=[], ret="Void")
    info = SymbolInfo(name="exit", symbol_type="extern_fn", decl=extern, file_path="test.astra")

    table = GlobalSymbolTable(extern_functions={"exit": (info,)})

    result = table.get_extern_function("exit")
    assert len(result) == 1
    assert result[0] is info


def test_global_symbol_table_is_global_symbol():
    """Test checking if name is in global scope"""
    table = GlobalSymbolTable(global_scope={"io": "module:io"})

    assert table.is_global_symbol("io")
    assert not table.is_global_symbol("nonexistent")


def test_global_symbol_table_get_duplicate_declarations():
    """Test getting duplicate declarations"""
    struct1 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    struct2 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    info1 = SymbolInfo(name="Point", symbol_type="struct", decl=struct1, file_path="a.astra")
    info2 = SymbolInfo(name="Point", symbol_type="struct", decl=struct2, file_path="b.astra")

    table = GlobalSymbolTable(duplicate_declarations=(("struct", info1, info2),))

    dups = table.get_duplicate_declarations()
    assert len(dups) == 1
    assert dups[0] == ("struct", info1, info2)


def test_global_symbol_table_functions_immutable():
    """Test that functions collection is immutable (tuple)"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    info = SymbolInfo(name="test", symbol_type="fn", decl=fn, file_path="test.astra")

    table = GlobalSymbolTable(functions={"test": (info,)})

    # Should be tuple, not list
    assert isinstance(table.functions["test"], tuple)


def test_mutable_symbol_table_creation():
    """Test MutableSymbolTable creation"""
    table = MutableSymbolTable()

    assert len(table.functions) == 0
    assert len(table.structs) == 0
    assert len(table.enums) == 0
    assert len(table.type_aliases) == 0
    assert len(table.extern_functions) == 0


def test_mutable_symbol_table_add_function():
    """Test adding function to mutable table"""
    table = MutableSymbolTable()
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=10, col=5, pos=100)

    table.add_function(fn, "test.astra")

    assert "test" in table.functions
    assert len(table.functions["test"]) == 1
    assert table.functions["test"][0].name == "test"
    assert table.functions["test"][0].file_path == "test.astra"


def test_mutable_symbol_table_add_extern_function():
    """Test adding extern function to mutable table"""
    table = MutableSymbolTable()
    extern = ExternFnDecl(lib="libc.so", name="exit", params=[], ret="Void", line=5, col=1, pos=50)

    table.add_extern_function(extern, "test.astra")

    assert "exit" in table.extern_functions
    assert len(table.extern_functions["exit"]) == 1


def test_mutable_symbol_table_add_struct():
    """Test adding struct to mutable table"""
    table = MutableSymbolTable()
    struct = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False, line=10, col=5, pos=100)

    table.add_struct(struct, "test.astra")

    assert "Point" in table.structs
    assert table.structs["Point"].name == "Point"


def test_mutable_symbol_table_add_struct_duplicate():
    """Test adding duplicate struct records it"""
    table = MutableSymbolTable()
    struct1 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False, line=10, col=5, pos=100)
    struct2 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False, line=20, col=5, pos=200)

    table.add_struct(struct1, "a.astra")
    table.add_struct(struct2, "b.astra")

    # Only first one should be in table
    assert table.structs["Point"].file_path == "a.astra"
    # Duplicate should be recorded
    assert len(table.duplicate_declarations) == 1
    assert table.duplicate_declarations[0][0] == "struct"


def test_mutable_symbol_table_add_enum():
    """Test adding enum to mutable table"""
    table = MutableSymbolTable()
    enum = EnumDecl(name="Color", generics=[], variants=[], doc="", line=10, col=5, pos=100)

    table.add_enum(enum, "test.astra")

    assert "Color" in table.enums


def test_mutable_symbol_table_add_enum_duplicate():
    """Test adding duplicate enum records it"""
    table = MutableSymbolTable()
    enum1 = EnumDecl(name="Color", generics=[], variants=[], doc="", line=10, col=5, pos=100)
    enum2 = EnumDecl(name="Color", generics=[], variants=[], doc="", line=20, col=5, pos=200)

    table.add_enum(enum1, "a.astra")
    table.add_enum(enum2, "b.astra")

    assert len(table.duplicate_declarations) == 1
    assert table.duplicate_declarations[0][0] == "enum"


def test_mutable_symbol_table_add_type_alias():
    """Test adding type alias to mutable table"""
    table = MutableSymbolTable()
    alias = TypeAliasDecl(name="MyInt", generics=[], target="Int", line=10, col=5, pos=100)

    table.add_type_alias(alias, "test.astra")

    assert "MyInt" in table.type_aliases


def test_mutable_symbol_table_add_type_alias_duplicate():
    """Test adding duplicate type alias records it"""
    table = MutableSymbolTable()
    alias1 = TypeAliasDecl(name="MyInt", generics=[], target="Int", line=10, col=5, pos=100)
    alias2 = TypeAliasDecl(name="MyInt", generics=[], target="i32", line=20, col=5, pos=200)

    table.add_type_alias(alias1, "a.astra")
    table.add_type_alias(alias2, "b.astra")

    assert len(table.duplicate_declarations) == 1
    assert table.duplicate_declarations[0][0] == "type_alias"


def test_mutable_symbol_table_add_import_alias():
    """Test adding import alias"""
    table = MutableSymbolTable()

    table.add_import_alias("io", "module:io")

    assert "io" in table.global_scope
    assert table.global_scope["io"] == "module:io"


def test_mutable_symbol_table_freeze():
    """Test freezing mutable table to global table"""
    table = MutableSymbolTable()
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=10, col=5, pos=100)
    table.add_function(fn, "test.astra")

    global_table = table.freeze()

    assert isinstance(global_table, GlobalSymbolTable)
    assert "test" in global_table.functions
    assert isinstance(global_table.functions["test"], tuple)


def test_mutable_symbol_table_freeze_converts_to_tuples():
    """Test that freeze converts function lists to tuples"""
    table = MutableSymbolTable()
    fn1 = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=10, col=5, pos=100)
    fn2 = FnDecl(name="test", generics=["T"], params=[("x", "T")], ret="T", body=[], line=20, col=5, pos=200)

    table.add_function(fn1, "test.astra")
    table.add_function(fn2, "test.astra")

    global_table = table.freeze()

    overloads = global_table.functions["test"]
    assert isinstance(overloads, tuple)
    assert len(overloads) == 2


def test_symbol_table_builder_creation():
    """Test SymbolTableBuilder creation"""
    builder = SymbolTableBuilder()

    assert len(builder.processed_files) == 0


def test_symbol_table_builder_add_program():
    """Test adding program to builder"""
    builder = SymbolTableBuilder()
    fn = FnDecl(name="main", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    builder.add_program(program, "main.astra")

    assert "main.astra" in builder.processed_files
    assert "main" in builder.mutable_table.functions


def test_symbol_table_builder_add_program_idempotent():
    """Test that adding same program twice is idempotent"""
    builder = SymbolTableBuilder()
    fn = FnDecl(name="main", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    builder.add_program(program, "main.astra")
    builder.add_program(program, "main.astra")

    # Should only have one function
    assert len(builder.mutable_table.functions["main"]) == 1


def test_symbol_table_builder_add_program_all_types():
    """Test adding program with all declaration types"""
    builder = SymbolTableBuilder()

    fn = FnDecl(name="func", generics=[], params=[], ret="Int", body=[])
    extern = ExternFnDecl(lib="libc.so", name="exit", params=[], ret="Void")
    struct = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    enum = EnumDecl(name="Color", generics=[], variants=[], doc="")
    alias = TypeAliasDecl(name="MyInt", generics=[], target="Int")
    import_decl = ImportDecl(path=["std", "io"], alias="io", source=None)

    program = Program(items=[fn, extern, struct, enum, alias, import_decl])

    builder.add_program(program, "test.astra")

    assert "func" in builder.mutable_table.functions
    assert "exit" in builder.mutable_table.extern_functions
    assert "Point" in builder.mutable_table.structs
    assert "Color" in builder.mutable_table.enums
    assert "MyInt" in builder.mutable_table.type_aliases
    assert "io" in builder.mutable_table.global_scope


def test_symbol_table_builder_build():
    """Test building final symbol table"""
    builder = SymbolTableBuilder()
    fn = FnDecl(name="main", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    builder.add_program(program, "main.astra")

    table = builder.build()

    assert isinstance(table, GlobalSymbolTable)
    assert "main" in table.functions


def test_build_global_symbol_table():
    """Test build_global_symbol_table function"""
    fn = FnDecl(name="main", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    asts = {Path("main.astra"): program}

    table = build_global_symbol_table(asts)

    assert isinstance(table, GlobalSymbolTable)
    assert "main" in table.functions


def test_build_global_symbol_table_multiple_files():
    """Test building table from multiple files"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[])

    program1 = Program(items=[fn1])
    program2 = Program(items=[fn2])

    asts = {
        Path("a.astra"): program1,
        Path("b.astra"): program2,
    }

    table = build_global_symbol_table(asts)

    assert "func1" in table.functions
    assert "func2" in table.functions


def test_build_global_symbol_table_with_list_ast():
    """Test building table when AST is a list"""
    fn = FnDecl(name="main", generics=[], params=[], ret="Int", body=[])

    asts = {Path("main.astra"): [fn]}

    table = build_global_symbol_table(asts)

    assert "main" in table.functions


def test_validate_symbol_consistency_no_errors():
    """Test validation with no errors"""
    fn = FnDecl(name="main", generics=[], params=[], ret="Int", body=[])
    info = SymbolInfo(name="main", symbol_type="fn", decl=fn, file_path="main.astra")

    table = GlobalSymbolTable(functions={"main": (info,)})

    errors = validate_symbol_consistency(table)

    assert len(errors) == 0


def test_validate_symbol_consistency_duplicate_struct():
    """Test validation detects duplicate struct"""
    struct1 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    struct2 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    info1 = SymbolInfo(name="Point", symbol_type="struct", decl=struct1, file_path="a.astra", span_info=(10, 5, 100))
    info2 = SymbolInfo(name="Point", symbol_type="struct", decl=struct2, file_path="b.astra", span_info=(20, 5, 200))

    table = GlobalSymbolTable(
        duplicate_declarations=(("struct", info1, info2),)
    )

    errors = validate_symbol_consistency(table)

    assert len(errors) == 1
    assert "Duplicate struct" in errors[0]
    assert "Point" in errors[0]


def test_validate_symbol_consistency_duplicate_function_signature():
    """Test validation detects duplicate function signatures"""
    fn1 = FnDecl(name="test", generics=[], params=[("x", "Int")], ret="Int", body=[])
    fn2 = FnDecl(name="test", generics=[], params=[("y", "Int")], ret="Int", body=[])
    info1 = SymbolInfo(name="test", symbol_type="fn", decl=fn1, file_path="a.astra", span_info=(10, 5, 100))
    info2 = SymbolInfo(name="test", symbol_type="fn", decl=fn2, file_path="b.astra", span_info=(20, 5, 200))

    table = GlobalSymbolTable(functions={"test": (info1, info2)})

    errors = validate_symbol_consistency(table)

    assert len(errors) == 1
    assert "Duplicate function signature" in errors[0]


def test_validate_symbol_consistency_name_conflict_struct_enum():
    """Test validation detects name conflicts between symbol types"""
    struct = StructDecl(name="Item", generics=[], fields=[], methods=[], packed=False)
    enum = EnumDecl(name="Item", generics=[], variants=[], doc="")
    struct_info = SymbolInfo(name="Item", symbol_type="struct", decl=struct, file_path="a.astra")
    enum_info = SymbolInfo(name="Item", symbol_type="enum", decl=enum, file_path="b.astra")

    table = GlobalSymbolTable(
        structs={"Item": struct_info},
        enums={"Item": enum_info}
    )

    errors = validate_symbol_consistency(table)

    assert len(errors) == 1
    assert "Name conflict" in errors[0]
    assert "Item" in errors[0]


def test_validate_symbol_consistency_multiple_errors():
    """Test validation collects multiple errors"""
    # Duplicate struct
    struct1 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    struct2 = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    info1 = SymbolInfo(name="Point", symbol_type="struct", decl=struct1, file_path="a.astra", span_info=(10, 5, 100))
    info2 = SymbolInfo(name="Point", symbol_type="struct", decl=struct2, file_path="b.astra", span_info=(20, 5, 200))

    # Name conflict
    enum = EnumDecl(name="Color", generics=[], variants=[], doc="")
    alias = TypeAliasDecl(name="Color", generics=[], target="Int")
    enum_info = SymbolInfo(name="Color", symbol_type="enum", decl=enum, file_path="c.astra")
    alias_info = SymbolInfo(name="Color", symbol_type="type_alias", decl=alias, file_path="d.astra")

    table = GlobalSymbolTable(
        enums={"Color": enum_info},
        type_aliases={"Color": alias_info},
        duplicate_declarations=(("struct", info1, info2),)
    )

    errors = validate_symbol_consistency(table)

    assert len(errors) == 2


def test_import_decl_with_file_source():
    """Test import declaration with file source"""
    builder = SymbolTableBuilder()
    import_decl = ImportDecl(path=[], alias="util", source="../util.astra")
    program = Program(items=[import_decl])

    builder.add_program(program, "main.astra")

    assert "util" in builder.mutable_table.global_scope
    assert "file:" in builder.mutable_table.global_scope["util"]


def test_regression_frozen_table_prevents_mutation():
    """Regression test: frozen table attributes cannot be reassigned"""
    table = GlobalSymbolTable()

    # GlobalSymbolTable is frozen, but its dict attributes are mutable for compatibility
    # We can test that the object itself is frozen
    with pytest.raises((AttributeError, Exception)):
        # Try to add a new attribute - this should fail since dataclass is frozen
        table.new_attribute = "test"