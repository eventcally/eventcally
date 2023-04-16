from flask_security import AsaList, RoleMixin
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    and_,
    func,
    select,
)
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import aliased, backref, deferred, relationship
from sqlalchemy.orm.relationships import remote
from sqlalchemy.schema import CheckConstraint
from sqlalchemy_utils import ColorType

from project import db
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class AdminUnitMemberRolesMembers(db.Model):
    __tablename__ = "adminunitmemberroles_members"
    id = Column(Integer(), primary_key=True)
    member_id = Column("member_id", Integer(), ForeignKey("adminunitmember.id"))
    role_id = Column("role_id", Integer(), ForeignKey("adminunitmemberrole.id"))


class AdminUnitMemberRole(db.Model, RoleMixin):
    __tablename__ = "adminunitmemberrole"
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(MutableList.as_mutable(AsaList()), nullable=True)


class AdminUnitMember(db.Model):
    __tablename__ = "adminunitmember"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("adminunitmembers", lazy=True))
    roles = relationship(
        "AdminUnitMemberRole",
        secondary="adminunitmemberroles_members",
        order_by="AdminUnitMemberRole.id",
        backref=backref("members", lazy="dynamic"),
    )


class AdminUnitMemberInvitation(db.Model):
    __tablename__ = "adminunitmemberinvitation"
    __table_args__ = (UniqueConstraint("email", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    email = Column(String(255))
    roles = Column(UnicodeText())


class AdminUnitInvitation(db.Model, TrackableMixin):
    __tablename__ = "adminunitinvitation"
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
        CheckConstraint("source_admin_unit_id != target_admin_unit_id"),
    )
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


class AdminUnit(db.Model, TrackableMixin):
    __tablename__ = "adminunit"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), unique=True)
    short_name = Column(Unicode(100), unique=True)
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
    eventsuggestions = relationship(
        "EventSuggestion",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
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
        "Location", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    logo_id = deferred(db.Column(db.Integer, db.ForeignKey("image.id")))
    logo = db.relationship(
        "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    url = deferred(Column(String(255)), group="detail")
    email = deferred(Column(Unicode(255)), group="detail")
    phone = deferred(Column(Unicode(255)), group="detail")
    fax = deferred(Column(Unicode(255)), group="detail")
    widget_font = deferred(Column(Unicode(255)), group="widget")
    widget_background_color = deferred(Column(ColorType), group="widget")
    widget_primary_color = deferred(Column(ColorType), group="widget")
    widget_link_color = deferred(Column(ColorType), group="widget")
    incoming_reference_requests_allowed = deferred(Column(Boolean()))
    suggestions_enabled = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
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
    incoming_verification_requests_text = Column(UnicodeText())
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

    def purge(self):
        if self.logo and self.logo.is_empty():
            self.logo_id = None


@listens_for(AdminUnit, "before_insert")
@listens_for(AdminUnit, "before_update")
def before_saving_admin_unit(mapper, connect, self):
    self.purge()


@listens_for(AdminUnit.can_invite_other, "set")
def set_admin_unit_can_invite_other(target, value, oldvalue, initiator):
    if (
        not value
        and target.admin_unit_invitations
        and len(target.admin_unit_invitations) > 0
    ):
        target.admin_unit_invitations = []
