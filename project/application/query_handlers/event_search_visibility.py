def can_read_private_events(visibility, actor, criteria) -> bool:
    """The caller asked for private events of an organization and may read them."""
    return bool(
        criteria.include_private
        and criteria.admin_unit_id
        and visibility.can_read_private_events(actor, criteria.admin_unit_id)
    )


def can_read_planned_events(visibility, actor, criteria) -> bool:
    return bool(criteria.include_planned and visibility.authz.can_use_planning(actor))
