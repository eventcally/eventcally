from enum import Enum


class OrganizationRelationSort(str, Enum):
    """Values equal the manage list sort keys; both sort by the target
    organization."""

    name = "name"
    last_modified_at_desc = "-last_modified_at"
