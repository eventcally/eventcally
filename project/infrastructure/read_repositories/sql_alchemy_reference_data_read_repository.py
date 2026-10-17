from typing import List, Optional

from sqlalchemy import or_, select

from project.application.queries.list_custom_event_categories_query import (
    ListCustomEventCategoriesQuery,
)
from project.application.queries.list_custom_event_category_sets_query import (
    ListCustomEventCategorySetsQuery,
)
from project.application.queries.list_event_categories_query import (
    ListEventCategoriesQuery,
)
from project.application.queries.list_licenses_query import ListLicensesQuery
from project.application.queries.lookup_custom_event_categories_query import (
    LookupCustomEventCategoriesQuery,
)
from project.application.queries.lookup_licenses_query import LookupLicensesQuery
from project.application.read_models.image_read_model import LicenseRefReadModel
from project.application.read_models.page import Page
from project.application.read_models.reference_data_read_models import (
    CustomEventCategoryRefReadModel,
    CustomEventCategorySetRefReadModel,
    EventCategoryRefReadModel,
)
from project.application.read_repositories.abstract_reference_data_read_repository import (
    AbstractReferenceDataReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    CustomEventCategory,
    CustomEventCategorySet,
    EventCategory,
    License,
)
from project.infrastructure.read_repositories.query_helpers import paginate
from project.utils import parse_like_term


class SqlAlchemyReferenceDataReadRepository(AbstractReferenceDataReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _page(self, model, page_request, to_item, *filters, order_by=None):
        stmt = select(model).where(*filters).order_by(*(order_by or [model.id]))
        count_stmt = select(model.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, page_request, lambda row: to_item(row[0])
        )

    def list_licenses(self, query: ListLicensesQuery) -> Page[LicenseRefReadModel]:
        return self._page(
            License,
            query.page,
            lambda license: LicenseRefReadModel(
                id=license.id, name=license.name, code=license.code, url=license.url
            ),
        )

    def list_event_categories(
        self, query: ListEventCategoriesQuery
    ) -> Page[EventCategoryRefReadModel]:
        return self._page(
            EventCategory,
            query.page,
            lambda category: EventCategoryRefReadModel(
                id=category.id, name=category.name
            ),
        )

    def list_custom_event_category_sets(
        self, query: ListCustomEventCategorySetsQuery
    ) -> Page[CustomEventCategorySetRefReadModel]:
        return self._page(
            CustomEventCategorySet,
            query.page,
            lambda category_set: CustomEventCategorySetRefReadModel(
                id=category_set.id, name=category_set.name, label=category_set.label
            ),
        )

    def list_custom_event_categories(
        self, query: ListCustomEventCategoriesQuery
    ) -> Page[CustomEventCategoryRefReadModel]:
        return self._page(
            CustomEventCategory,
            query.page,
            lambda category: CustomEventCategoryRefReadModel(
                id=category.id,
                name=category.name,
                label=category.label,
                category_set_id=category.category_set_id,
            ),
            CustomEventCategory.category_set_id == query.category_set_id,
        )

    def lookup_licenses(self, query: LookupLicensesQuery) -> Page[LicenseRefReadModel]:
        filters = []

        if query.term:
            like = parse_like_term(query.term)
            filters.append(or_(License.code.ilike(like), License.name.ilike(like)))

        return self._page(
            License,
            query.page,
            _to_license,
            *filters,
            order_by=[License.sort, License.id],
        )

    def get_license(self, license_id: ObjectId) -> Optional[LicenseRefReadModel]:
        license = self.session.get(License, license_id)
        return _to_license(license) if license else None

    def list_all_event_categories(self) -> List[EventCategoryRefReadModel]:
        categories = self.session.execute(select(EventCategory)).scalars().all()
        return [_to_event_category(category) for category in categories]

    def get_event_category(
        self, category_id: ObjectId
    ) -> Optional[EventCategoryRefReadModel]:
        category = self.session.get(EventCategory, category_id)
        return _to_event_category(category) if category else None

    def get_event_category_by_name(
        self, name: str
    ) -> Optional[EventCategoryRefReadModel]:
        category = self.session.execute(
            select(EventCategory).where(EventCategory.name == name)
        ).scalar_one_or_none()
        return _to_event_category(category) if category else None

    def lookup_custom_event_categories(
        self, query: LookupCustomEventCategoriesQuery
    ) -> Page[CustomEventCategoryRefReadModel]:
        filters = [CustomEventCategory.category_set_id == query.category_set_id]

        if query.term:
            like = parse_like_term(query.term)
            filters.append(
                or_(
                    CustomEventCategory.name.ilike(like),
                    CustomEventCategory.label.ilike(like),
                )
            )

        return self._page(
            CustomEventCategory,
            query.page,
            _to_custom_event_category,
            *filters,
            order_by=[
                CustomEventCategory.name,
                CustomEventCategory.label,
                CustomEventCategory.id,
            ],
        )

    def get_custom_event_category(
        self, category_id: ObjectId
    ) -> Optional[CustomEventCategoryRefReadModel]:
        category = self.session.get(CustomEventCategory, category_id)
        return _to_custom_event_category(category) if category else None


def _to_license(license) -> LicenseRefReadModel:
    return LicenseRefReadModel(
        id=license.id, name=license.name, code=license.code, url=license.url
    )


def _to_event_category(category) -> EventCategoryRefReadModel:
    return EventCategoryRefReadModel(id=category.id, name=category.name)


def _to_custom_event_category(category) -> CustomEventCategoryRefReadModel:
    return CustomEventCategoryRefReadModel(
        id=category.id,
        name=category.name,
        label=category.label,
        category_set_id=category.category_set_id,
    )
