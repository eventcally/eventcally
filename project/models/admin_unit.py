from flask_security import AsaList, RoleMixin
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    and_,
    cast,
    func,
    select,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import aliased, backref, deferred, relationship
from sqlalchemy.orm.relationships import remote
from sqlalchemy.schema import CheckConstraint
from sqlalchemy_utils import ColorType

from project import db
from project.models.admin_unit_verification_request import AdminUnitVerificationRequest
from project.models.api_key import ApiKeyOwnerMixin
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class AdminUnitMemberRolesMembers(db.Model):
    __tablename__ = "adminunitmemberroles_members"
    __display_name__ = "Organization member role members"
    id = Column(Integer(), primary_key=True)
    member_id = Column("member_id", Integer(), ForeignKey("adminunitmember.id"))
    role_id = Column("role_id", Integer(), ForeignKey("adminunitmemberrole.id"))


class AdminUnitMemberRole(db.Model, RoleMixin):
    __tablename__ = "adminunitmemberrole"
    __display_name__ = "Organization member role"
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(MutableList.as_mutable(AsaList()), nullable=True)


class AdminUnitMember(db.Model):
    __tablename__ = "adminunitmember"
    __model_name__ = "organization_member"
    __display_name__ = "Organization member"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("adminunitmembers", lazy=True))
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = db.relationship(
        "User",
        backref=db.backref("adminunitmembers", cascade="all, delete-orphan", lazy=True),
    )
    roles = relationship(
        "AdminUnitMemberRole",
        secondary="adminunitmemberroles_members",
        order_by="AdminUnitMemberRole.id",
        backref=backref("members", lazy="dynamic"),
    )

    def __str__(self):
        return self.user.__str__() if self.user else super().__str__()

    def has_role(self, role: str | RoleMixin) -> bool:
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        if isinstance(role, str):
            return role in (role.name for role in self.roles)
        else:  # pragma: no cover
            return role in self.roles

    @hybrid_property
    def is_admin(self):
        return self.has_role("admin")

    @is_admin.expression
    def is_admin(cls):
        return (
            select(func.count())
            .select_from(AdminUnitMemberRole.__table__)
            .join(
                AdminUnitMemberRolesMembers.__table__,
                AdminUnitMemberRolesMembers.role_id == AdminUnitMemberRole.id,
            )
            .where(
                and_(
                    AdminUnitMemberRolesMembers.member_id == cls.id,
                    AdminUnitMemberRole.name == "admin",
                )
            )
            .scalar_subquery()
        ) > 0


class AdminUnitMemberInvitation(db.Model):
    __tablename__ = "adminunitmemberinvitation"
    __table_args__ = (UniqueConstraint("email", "admin_unit_id"),)
    __model_name__ = "organization_member_invitation"
    __display_name__ = "Organization member invitation"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    email = Column(String(255))
    roles = Column(UnicodeText())


class AdminUnitInvitation(db.Model, TrackableMixin):
    __tablename__ = "adminunitinvitation"
    __model_name__ = "organization_invitation"
    __display_name__ = "Organization invitation"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    email = Column(String(255), nullable=False)
    admin_unit_name = Column(String(255))
    relation_auto_verify_event_reference_requests = Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    relation_verify = Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )


class AdminUnitRelation(db.Model, TrackableMixin):
    __tablename__ = "adminunitrelation"
    __table_args__ = (
        UniqueConstraint("source_admin_unit_id", "target_admin_unit_id"),
        CheckConstraint(
            "source_admin_unit_id != target_admin_unit_id", name="source_neq_target"
        ),
    )
    __model_name__ = "organization_relation"
    __display_name__ = "Organization relation"
    id = Column(Integer(), primary_key=True)
    source_admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    target_admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    auto_verify_event_reference_requests = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    verify = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    invited = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )

    def validate(self):
        source_id = (
            self.source_admin_unit.id
            if self.source_admin_unit
            else self.source_admin_unit_id
        )
        target_id = (
            self.target_admin_unit.id
            if self.target_admin_unit
            else self.target_admin_unit_id
        )
        if source_id == target_id:
            raise make_check_violation("There must be no self-reference.")


@listens_for(AdminUnitRelation, "before_insert")
@listens_for(AdminUnitRelation, "before_update")
def before_saving_admin_unit_relation(mapper, connect, self):
    self.validate()


class AdminUnit(db.Model, TrackableMixin, ApiKeyOwnerMixin):
    __tablename__ = "adminunit"
    __table_args__ = (
        db.Index(
            "idx_adminunit_incoming_verification_requests_postal_codes",
            "incoming_verification_requests_postal_codes",
            postgresql_using="gin",
        ),
    )
    __model_name__ = "organization"
    __display_name__ = "Organization"

    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), unique=True)
    short_name = Column(Unicode(100), unique=True)
    deletion_requested_at = deferred(Column(DateTime, nullable=True), group="deletion")
    deletion_requested_by_id = deferred(
        Column(ForeignKey("user.id"), nullable=True), group="deletion"
    )
    deletion_requested_by = relationship(
        "User",
        primaryjoin="User.id == AdminUnit.deletion_requested_by_id",
        remote_side="User.id",
    )
    members = relationship(
        "AdminUnitMember",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    invitations = relationship(
        "AdminUnitMemberInvitation",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    admin_unit_invitations = relationship(
        "AdminUnitInvitation",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    events = relationship(
        "Event", cascade="all, delete-orphan", backref=backref("admin_unit", lazy=True)
    )
    references = relationship(
        "EventReference",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    reference_requests = relationship(
        "EventReferenceRequest",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    event_organizers = relationship(
        "EventOrganizer",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    event_places = relationship(
        "EventPlace",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    event_lists = relationship(
        "EventList",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    custom_widgets = relationship(
        "CustomWidget",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    location_id = deferred(db.Column(db.Integer, db.ForeignKey("location.id")))
    location = db.relationship(
        "Location",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        back_populates="adminunit",
    )
    logo_id = deferred(db.Column(db.Integer, db.ForeignKey("image.id")))
    logo = db.relationship(
        "Image",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        back_populates="adminunit",
    )
    url = deferred(Column(String(255)), group="detail")
    email = deferred(Column(Unicode(255)), group="detail")
    phone = deferred(Column(Unicode(255)), group="detail")
    fax = deferred(Column(Unicode(255)), group="detail")
    description = deferred(Column(UnicodeText(), nullable=True), group="detail")
    widget_font = deferred(Column(Unicode(255)), group="widget")
    widget_background_color = deferred(Column(ColorType), group="widget")
    widget_primary_color = deferred(Column(ColorType), group="widget")
    widget_link_color = deferred(Column(ColorType), group="widget")
    incoming_reference_requests_allowed = deferred(Column(Boolean()))
    can_create_other = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    can_verify_other = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    incoming_verification_requests_allowed = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    incoming_verification_requests_text = deferred(Column(UnicodeText()))
    incoming_verification_requests_postal_codes = deferred(
        Column(
            postgresql.ARRAY(Unicode(255)),
            nullable=False,
            default=cast(
                postgresql.array([], type_=Unicode(255)), postgresql.ARRAY(Unicode(255))
            ),
            server_default="{}",
        )
    )
    can_invite_other = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    outgoing_relations = relationship(
        "AdminUnitRelation",
        primaryjoin=remote(AdminUnitRelation.source_admin_unit_id) == id,
        single_parent=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        backref=backref(
            "source_admin_unit",
            lazy=True,
        ),
    )
    incoming_relations = relationship(
        "AdminUnitRelation",
        primaryjoin=remote(AdminUnitRelation.target_admin_unit_id) == id,
        cascade="all, delete-orphan",
        passive_deletes=True,
        backref=backref(
            "target_admin_unit",
            lazy=True,
        ),
    )
    outgoing_verification_requests = relationship(
        "AdminUnitVerificationRequest",
        primaryjoin=remote(AdminUnitVerificationRequest.source_admin_unit_id) == id,
        single_parent=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        backref=backref(
            "source_admin_unit",
            lazy=True,
        ),
    )
    incoming_verification_requests = relationship(
        "AdminUnitVerificationRequest",
        primaryjoin=remote(AdminUnitVerificationRequest.target_admin_unit_id) == id,
        cascade="all, delete-orphan",
        passive_deletes=True,
        backref=backref(
            "target_admin_unit",
            lazy=True,
        ),
    )
    api_keys = relationship(
        "ApiKey",
        primaryjoin="ApiKey.admin_unit_id == AdminUnit.id",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    oauth2_clients = relationship(
        "OAuth2Client",
        primaryjoin="OAuth2Client.admin_unit_id == AdminUnit.id",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    app_installations = relationship(
        "AppInstallation",
        primaryjoin="AppInstallation.admin_unit_id == AdminUnit.id",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )

    def get_number_of_api_keys(self):
        from project.models.api_key import ApiKey

        return ApiKey.query.filter(ApiKey.admin_unit_id == self.id).count()

    @hybrid_property
    def is_verified(self):
        if not self.incoming_relations:
            return False

        return any(
            r.verify and r.source_admin_unit.can_verify_other
            for r in self.incoming_relations
        )

    @is_verified.expression
    def is_verified(cls):
        SourceAdminUnit = aliased(AdminUnit)

        j = AdminUnitRelation.__table__.join(
            SourceAdminUnit,
            AdminUnitRelation.source_admin_unit_id == SourceAdminUnit.id,
        )
        return (
            select(func.count())
            .select_from(j)
            .where(
                and_(
                    AdminUnitRelation.verify,
                    AdminUnitRelation.target_admin_unit_id == cls.id,
                    SourceAdminUnit.can_verify_other,
                )
            )
            .scalar_subquery()
            > 0
        )

    def __str__(self):
        return self.name or super().__str__()


@listens_for(AdminUnit.can_invite_other, "set")
def set_admin_unit_can_invite_other(target, value, oldvalue, initiator):
    if (
        not value
        and target.admin_unit_invitations
        and len(target.admin_unit_invitations) > 0
    ):
        target.admin_unit_invitations = []
