#!/usr/bin/env python
"""
Code generator script that reads YAML schema and generates SQLAlchemy models.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml
from jinja2 import Environment, FileSystemLoader


@dataclass
class Column:
    name: str
    type: str
    deferred: bool = False
    deferred_group: str = None
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    name: str
    target_model: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Model:
    name: str
    mixin_name: str
    table_name: str = None
    file_name: str = None
    model_name: str = None
    model_name_plural: str = None
    display_name: str = None
    display_name_plural: str = None
    imports: List[str] = field(default_factory=list)
    columns: List[Column] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    enums: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class AssociationTable:
    name: str = None
    mixin_name: str = None
    table_name: str = None
    file_name: str = None
    left_model: str = None
    left_table: str = None
    right_model: str = None
    right_table: str = None
    left_fk: str = None
    right_fk: str = None
    constraints: List[str] = field(default_factory=list)


def snake_case_to_human(snake_case):
    result = snake_case.replace("_", " ")
    return result[:1].upper() + result[1:]


def camel_to_snake_case(name: str) -> str:
    """Convert a ``CamelCase`` name to ``snake_case``."""
    name = re.sub(r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", name)
    return name.lower().lstrip("_")


def class_name_to_model_name(class_name):
    result = camel_to_snake_case(class_name)

    if result[1] == "_":
        result = result[:1] + result[2:]

    return result


def model_name_to_plural(model_name):
    if model_name.endswith("s"):
        return model_name

    if model_name.endswith("y") and not model_name.endswith("key"):
        return model_name[:-1] + "ies"

    return f"{model_name}s"


class SQLAlchemyGenerator:
    """Generates SQLAlchemy model code from YAML schema."""

    TYPE_MAPPING = {
        "string": "Unicode(255)",
        "string!": "Unicode(255)",
        "integer": "Integer()",
        "integer!": "Integer()",
        "text": "UnicodeText()",
        "datetime": "DateTime()",
        "datetime!": "DateTime()",
        "datetimetz": "DateTime(timezone=True)",
        "datetimetz!": "DateTime(timezone=True)",
        "boolean": "Boolean()",
        "boolean!": "Boolean()",
        "float": "Float()",
        "enum": "IntegerEnum()",
        "json": "JSONB",
        "mutable_list": "MutableList.as_mutable(AsaList())",
        "blob": "LargeBinary",
        "numeric": "Numeric()",
        "geometry": "Geometry()",
        "color": "ColorType",
        "array": "ARRAY",
    }

    def __init__(
        self,
        template_dir: str,
        output_models_dir: str,
        config_dir: str,
        mixins_dir: str = None,
    ):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.output_models_dir = output_models_dir
        self.output_association_tables_dir = os.path.join(
            output_models_dir, "association_tables"
        )
        self.output_mixins_dir = os.path.join(output_models_dir, "mixins")
        self.config_dir = config_dir
        self.mixins_dir = mixins_dir
        self.mixin_definitions = {}
        self.model_definitions = {}
        self.generated_mixins: Dict[str, Model] = {}
        self.association_tables: Dict[str, AssociationTable] = {}

        self._load_models()
        self._load_mixins()
        self._collect_association_tables()

    def _load_mixins(self):
        """Load all mixin definitions from the mixins directory."""
        for filename in os.listdir(self.mixins_dir):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                mixin_file = os.path.join(self.mixins_dir, filename)
                with open(mixin_file, "r") as f:
                    data = yaml.safe_load(f)

                for mixin_data in data.get("models", []):
                    mixin_name = mixin_data["name"]
                    self.mixin_definitions[mixin_name] = mixin_data

    def _apply_mixin(self, model: Model, mixin_name: str):
        """Apply a mixin to a model by adding its columns and relationships."""
        if mixin_name not in self.mixin_definitions:
            print(f"Warning: Mixin '{mixin_name}' not found")
            return

        mixin_data = self.mixin_definitions[mixin_name]

        # Add mixin columns
        for col_data in mixin_data.get("columns", []):
            column = self._parse_column(col_data, model)
            model.columns.append(column)

        # Add mixin relationships and foreign keys
        for rel_data in mixin_data.get("relationships", []):
            relationship = self._parse_relationship(rel_data, model)
            if relationship:
                model.relationships.append(relationship)

    def _load_models(self):
        """Load all model definitions from YAML files in config directory."""
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                yaml_file = os.path.join(self.config_dir, filename)
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                for model_data in data.get("models", []):
                    model_name = model_data["name"]
                    self.model_definitions[model_name] = model_data

    def _collect_association_tables(self):
        """Collect all association table definitions from model relationships."""
        for model_name, model_data in self.model_definitions.items():
            for rel_data in model_data.get("relationships", []):
                if rel_data["pattern"] == "many-to-many":
                    if "association_model" not in rel_data:
                        raise ValueError(
                            f"Many-to-many relationship {model_name}.{rel_data['name']} must specify 'association_model'"
                        )
                    if "association_table" not in rel_data:
                        raise ValueError(
                            f"Many-to-many relationship {model_name}.{rel_data['name']} must specify 'association_table'"
                        )

                    table_name = model_data.get("table_name", model_name.lower())
                    association_column = rel_data.get(
                        "association_column",
                        f"{class_name_to_model_name(model_name)}_id",
                    )

                    assoc_model_name = rel_data["association_model"]
                    assoc_table_name = rel_data["association_table"]
                    assoc_table = self.association_tables.get(assoc_model_name)

                    if not assoc_table:  # left
                        assoc_table = AssociationTable(
                            name=assoc_model_name,
                            mixin_name=f"{assoc_model_name}GeneratedMixin",
                            table_name=assoc_table_name,
                            file_name=class_name_to_model_name(assoc_model_name),
                            left_model=model_name,
                            left_table=table_name,
                            left_fk=association_column,
                        )
                        self.association_tables[assoc_model_name] = assoc_table
                    else:  # right
                        assoc_table.right_model = model_name
                        assoc_table.right_table = table_name
                        assoc_table.right_fk = association_column
                        assoc_table.constraints.append(
                            f'UniqueConstraint("{assoc_table.left_fk}", "{assoc_table.right_fk}")'
                        )

    def parse_yaml(self, yaml_path: str) -> List[Model]:
        """Parse YAML schema file and return list of Model objects."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        models = []
        for model_data in data.get("models", []):
            model = self._parse_model(model_data)
            models.append(model)

        return models

    def _parse_model(self, model_data: Dict[str, Any]) -> Model:
        """Parse a single model from YAML data."""
        name = model_data["name"]
        mixin_name = f"{name}GeneratedMixin"

        model = Model(name=name, mixin_name=mixin_name)
        model.table_name = model_data.get("table_name", name.lower())
        model.file_name = model_data.get("file_name", class_name_to_model_name(name))
        model.model_name = model_data.get("model_name", class_name_to_model_name(name))
        model.model_name_plural = model_name_to_plural(model.model_name)
        model.display_name = model_data.get(
            "display_name", snake_case_to_human(model.model_name)
        )
        model.display_name_plural = model_name_to_plural(model.display_name)

        # Add ID column (always present)
        id_col = Column(name="id", type="Integer()", kwargs={"primary_key": True})
        model.columns.append(id_col)

        # Add referenced mixins to the model's mixin list and apply their content
        for mixin_name in model_data.get("mixins", []):
            if mixin_name in self.mixin_definitions:
                mixin_class_name = f"{mixin_name}Mixin"
                if mixin_class_name not in model.mixins:
                    model.mixins.append(mixin_class_name)
                # Apply mixin columns and relationships to the concrete model
                # self._apply_mixin(model, mixin_name)

                mixin_model = self.generated_mixins[mixin_name]
                model.imports.append(
                    f"from project.models.mixins.{mixin_model.file_name} import {mixin_class_name}"
                )
            else:
                print(f"Warning: Mixin '{mixin_name}' not found")

        # Parse columns
        for col_data in model_data.get("columns", []):
            column = self._parse_column(col_data, model)
            model.columns.append(column)

        # Parse relationships and add foreign key columns
        for rel_data in model_data.get("relationships", []):
            relationship = self._parse_relationship(rel_data, model)
            if relationship:
                model.relationships.append(relationship)

        # Parse constraints
        for constraint_data in model_data.get("constraints", []):
            constraint = self._parse_constraint(constraint_data)
            model.constraints.append(constraint)

        # Parse indexes
        for index_data in model_data.get("indexes", []):
            index = self._parse_index(index_data)
            model.indexes.append(index)

        return model

    def _parse_column(self, col_data: Dict[str, Any], model: Model) -> Column:
        """Parse a column definition."""
        name = col_data["name"]
        col_type = col_data["type"]

        # Check if nullable (! means not nullable)
        nullable = col_data.get("nullable", not col_type.endswith("!"))
        col_type = col_type.rstrip("!")

        # Map type to SQLAlchemy type
        sqla_type = self.TYPE_MAPPING.get(col_type, "String(255)")

        # Handle string type with custom length
        if col_type == "string":
            length = col_data.get("length", 255)
            sqla_type = f"Unicode({length})"

        # Handle numeric type with precision and scale
        if col_type == "numeric":
            precision = col_data.get("precision", 10)
            scale = col_data.get("scale", 2)
            sqla_type = f"Numeric({precision}, {scale})"

        # Handle geometry type with geometry_type
        if col_type == "geometry":
            geometry_type = col_data.get("geometry_type", "POINT")
            sqla_type = f'Geometry(geometry_type="{geometry_type}")'

        # Handle array type with array_type
        if col_type == "array":
            array_type = col_data.get("array_type", "string")
            if array_type == "string":
                array_type = "Unicode(255)"

            sqla_type = f"postgresql.ARRAY({array_type})"

        # Handle enum type
        if col_type == "enum" and "enum" in col_data:
            # Generate enum class name from model name and column name
            # e.g., AdminUnitVerificationRequest + review_status -> AdminUnitVerificationRequestReviewStatus
            enum_class = model.name + "".join(
                word.capitalize() for word in name.split("_")
            )
            enum_values = (
                col_data["enum"]
                if isinstance(col_data["enum"], list)
                else col_data["enum"]["values"]
            )
            sqla_type = f"IntegerEnum({enum_class})"
            # Store enum definition in model for code generation
            model.enums[enum_class] = enum_values

        column = Column(name=name, type=sqla_type)

        # Add nullable constraint if not nullable
        if not nullable:
            column.kwargs["nullable"] = False

        # Handle default value
        if "default" in col_data:
            column.kwargs["default"] = col_data["default"]

            if col_type == "enum":
                column.kwargs["default"] = f"{enum_class}.{col_data['default']}.value"
            elif col_type == "datetime" and column.kwargs["default"] == "now":
                column.kwargs["default"] = "datetime.datetime.utcnow"
            elif col_type == "array":
                column.kwargs["default"] = (
                    f"cast(postgresql.array({col_data['default']}, type_={array_type}), {sqla_type})"
                )

            server_default = None
            if "server_default" in col_data:
                server_default = col_data["server_default"]
            elif not nullable:
                server_default = column.kwargs["default"]
                if isinstance(server_default, bool):
                    server_default = int(server_default)
                elif col_type == "enum":
                    server_default = f"str({server_default})"
                elif col_type == "array":
                    server_default = "{}"

            if server_default is not None:
                column.kwargs["server_default"] = (
                    server_default
                    if col_type == "enum"
                    or (
                        isinstance(server_default, str)
                        and server_default.startswith("cls.")
                    )
                    else f'"{server_default}"'
                )

        # Handle onupdate value
        if "onupdate" in col_data:
            column.kwargs["onupdate"] = col_data["onupdate"]

            if col_type == "datetime" and column.kwargs["onupdate"] == "now":
                column.kwargs["onupdate"] = "datetime.datetime.utcnow"

        # Handle unique constraint
        if col_data.get("unique", False):
            column.kwargs["unique"] = True

        # Handle index
        if col_data.get("index", False):
            column.kwargs["index"] = True

        column.kwargs["nullable"] = nullable

        # Handle deferred loading
        if "deferred" in col_data:
            if isinstance(col_data["deferred"], bool):
                column.deferred = col_data["deferred"]
            elif isinstance(col_data["deferred"], str):
                column.deferred = True
                column.deferred_group = col_data["deferred"]

        return column

    def _parse_relationship(
        self, rel_data: Dict[str, Any], model: Model
    ) -> Relationship:
        """Parse a relationship definition and add foreign key columns."""
        name = rel_data["name"]
        target_model = rel_data["target_model"]
        pattern = rel_data.get("pattern", "many-to-one")
        relation = rel_data.get("relation", "reference")

        relationship = Relationship(name=name, target_model=target_model)
        target_model_data = self.model_definitions[target_model]
        target_model_table_name = target_model_data.get(
            "table_name", target_model.lower()
        )

        # Handle nullable
        nullable = True
        if "nullable" in rel_data:
            nullable = rel_data["nullable"]
        elif relation == "parent":
            nullable = False

        # Add foreign key column
        fk_name = f"{name}_id"
        fk_table = rel_data.get("table_name", target_model_table_name)

        # Build ForeignKey with on_delete if specified
        fk_args = [f'"{fk_table}.id"']
        if relation == "parent":
            fk_args.append('ondelete="CASCADE"')
        elif nullable:
            fk_args.append('ondelete="SET NULL"')
        fk_definition = f'ForeignKey({", ".join(fk_args)})'

        fk_kwargs = {}
        # Handle nullable constraint on foreign key
        fk_kwargs["nullable"] = nullable

        if "default" in rel_data:
            fk_kwargs["default"] = rel_data["default"]

        if "onupdate" in rel_data:
            fk_kwargs["onupdate"] = rel_data["onupdate"]

        fk_col = Column(
            name=fk_name, type="Integer()", kwargs=fk_kwargs, args=[fk_definition]
        )

        # Handle deferred foreign key
        if "deferred" in rel_data:
            if isinstance(rel_data["deferred"], bool):
                fk_col.deferred = rel_data["deferred"]
            elif isinstance(rel_data["deferred"], str):
                fk_col.deferred = True
                fk_col.deferred_group = rel_data["deferred"]

        skip_foreign_key = (
            pattern == "many-to-many"
            or pattern == "one-to-many"
            or (pattern == "one-to-one" and relation != "owned")
        )

        if not skip_foreign_key:
            model.columns.append(fk_col)
            relationship.kwargs["foreign_keys"] = f"[cls.{fk_name}]"

        # Configure relationship parameters
        if pattern == "one-to-one":
            relationship.kwargs["uselist"] = False

        if relation == "owned":
            if pattern == "one-to-one":
                relationship.kwargs["single_parent"] = True
            relationship.kwargs["cascade"] = '"all, delete-orphan"'

        # Add back_populates
        back_populates = rel_data.get("back_populates", None)
        if not back_populates:
            if pattern == "many-to-one" or pattern == "many-to-many":
                back_populates = model_name_to_plural(model.model_name)
            else:
                back_populates = model.model_name

        if back_populates and back_populates.lower() != "none":
            relationship.kwargs["back_populates"] = f'"{back_populates}"'

        if rel_data.get("association_table"):
            association_table = rel_data["association_table"]
            relationship.kwargs["secondary"] = f'"{association_table}"'

        # Add primaryjoin if specified
        if rel_data.get("primaryjoin"):
            relationship.kwargs["primaryjoin"] = f'"{rel_data["primaryjoin"]}"'
        elif "secondary" not in relationship.kwargs and pattern == "one-to-many":
            relationship.kwargs["primaryjoin"] = (
                f'"{target_model}.{back_populates}_id == {model.name}.id"'
            )

        # Add order_by if specified
        if rel_data.get("order_by"):
            relationship.kwargs["order_by"] = f'"{target_model}.{rel_data["order_by"]}"'

        return relationship

    def _parse_constraint(self, constraint_data: Dict[str, Any]) -> str:
        """Parse a constraint definition."""
        constraint_type = constraint_data["type"]

        if constraint_type == "unique":
            columns = ", ".join(f'"{col}"' for col in constraint_data["columns"])
            name = constraint_data.get("name", "")
            if name:
                return f'UniqueConstraint({columns}, name="{name}")'
            return f"UniqueConstraint({columns})"

        if constraint_type == "check":
            expression = constraint_data["expression"]
            name = constraint_data.get("name", "")
            if name:
                return f'CheckConstraint("{expression}", name="{name}")'
            return f'CheckConstraint("{expression}")'

        return ""

    def _parse_index(self, index_data: Dict[str, Any]) -> str:
        """Parse an index definition."""
        name = index_data["name"]
        columns = ", ".join(f'"{col}"' for col in index_data["columns"])
        using = index_data.get("using", None)

        if using:
            return f'Index("{name}", {columns}, postgresql_using="{using}")'
        else:
            return f'Index("{name}", {columns})'

    def generate_context(self, model: Model) -> dict:
        # Process columns to handle deferred
        processed_columns = []
        for col in model.columns:
            col_copy = Column(
                name=col.name,
                type=col.type,
                deferred=col.deferred,
                deferred_group=col.deferred_group,
                args=col.args[:],
                kwargs=col.kwargs.copy(),
            )

            parts = [col.type]
            if col.args:
                parts.extend(col.args)
            for key, value in col.kwargs.items():
                if key == "foreign_key":
                    parts.append(f"ForeignKey({value})")
                else:
                    parts.append(f"{key}={value}")

            rendered = f"Column({', '.join(parts)})"

            if col.deferred:
                if col.deferred_group:
                    rendered = f'deferred({rendered}, group="{col.deferred_group}")'
                else:
                    rendered = f"deferred({rendered})"

            col_copy.rendered = rendered

            processed_columns.append(col_copy)

        # Prepare context
        context = {
            "columns": processed_columns,
            "model": model,
        }
        return context

    def generate_code(self, model: Model):
        """Generate SQLAlchemy model code from Model object."""
        context = self.generate_context(model)

        # sqla_model = self.env.get_template("sqla_model.py.j2").render(**context)
        sqla_model_mixin = self.env.get_template("sqla_model_mixin.py.j2").render(
            **context
        )

        # Write to file
        output_file = os.path.join(
            self.output_models_dir, f"{model.file_name}_generated.py"
        )
        with open(output_file, "w") as f:
            f.write(sqla_model_mixin)

    def generate_mixin_code(self, mixin_name: str, mixin_data: Dict[str, Any]):
        """Generate SQLAlchemy mixin code from mixin definition."""
        # Create a temporary model to parse the mixin structure
        temp_model = Model(name=mixin_name, mixin_name=f"{mixin_name}GeneratedMixin")
        temp_model.table_name = None  # Mixins don't have tables
        temp_model.file_name = class_name_to_model_name(mixin_name) + "_mixin"

        # Parse mixin columns
        for col_data in mixin_data.get("columns", []):
            column = self._parse_column(col_data, temp_model)
            temp_model.columns.append(column)

        # Parse mixin relationships
        for rel_data in mixin_data.get("relationships", []):
            relationship = self._parse_relationship(rel_data, temp_model)
            if relationship:
                temp_model.relationships.append(relationship)

        context = self.generate_context(temp_model)

        # Use the same template but it will render differently for mixins
        mixin_code = self.env.get_template("sqla_mixin_mixin.py.j2").render(**context)

        # Write to file
        output_file = os.path.join(
            self.output_mixins_dir, f"{temp_model.file_name}_generated.py"
        )
        with open(output_file, "w") as f:
            f.write(mixin_code)

        self.generated_mixins[mixin_name] = temp_model

    def generate_association_table_code(self, assoc_table: AssociationTable):
        """Generate SQLAlchemy association table code."""
        context = {"assoc_table": assoc_table}

        assoc_code = self.env.get_template("sqla_association_table.py.j2").render(
            **context
        )

        # Write to file
        output_file = os.path.join(
            self.output_association_tables_dir, f"{assoc_table.file_name}_generated.py"
        )
        with open(output_file, "w") as f:
            f.write(assoc_code)


def main():
    """Main entry point."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(script_dir, "config")
    models_dir = os.path.join(config_dir, "models")
    mixins_dir = os.path.join(models_dir, "mixins")
    template_dir = os.path.join(script_dir, "templates")
    project_dir = os.path.dirname(script_dir)
    output_models_dir = os.path.join(project_dir, "project", "models")

    generator = SQLAlchemyGenerator(
        template_dir, output_models_dir, models_dir, mixins_dir
    )

    # Generate mixin files first
    for mixin_name, mixin_data in generator.mixin_definitions.items():
        print(f"Generating mixin {mixin_name}...")
        generator.generate_mixin_code(mixin_name, mixin_data)

    # Parse and generate code for all models
    for model_name, model_data in generator.model_definitions.items():
        print(f"Generating model {model_name}...")
        model = generator._parse_model(model_data)
        generator.generate_code(model)

    # Generate association tables
    for assoc_name, assoc_table in generator.association_tables.items():
        print(f"Generating association table {assoc_name}...")
        generator.generate_association_table_code(assoc_table)

    subprocess.run(["black", output_models_dir], check=True, capture_output=True)


if __name__ == "__main__":
    main()
