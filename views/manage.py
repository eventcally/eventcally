from app import app, db
from models import AdminUnit, AdminUnitMember, AdminUnitMemberInvitation, Event, EventPlace, EventReviewStatus, EventOrganizer, User
from flask import render_template, flash, url_for, redirect, request, jsonify, make_response
from flask_babelex import gettext
from flask_security import auth_required, roles_required, current_user
from access import has_access, access_or_401, get_admin_unit_for_manage, get_admin_units_for_manage, get_admin_unit_for_manage_or_404
from sqlalchemy.sql import asc, func
from sqlalchemy import and_, or_, not_
from .utils import get_pagination_urls, permission_missing
from forms.event_place import FindEventPlaceForm
from forms.event import FindEventForm

@app.route("/manage")
@auth_required()
def manage():
    try:
        if 'manage_admin_unit_id' in request.cookies:
            manage_admin_unit_id = int(request.cookies.get('manage_admin_unit_id'))
            admin_unit = get_admin_unit_for_manage(manage_admin_unit_id)

            if admin_unit:
                return redirect(url_for('manage_admin_unit', id=admin_unit.id))
    except:
        pass

    return redirect(url_for('manage_admin_units'))

@app.route("/manage/admin_units")
@auth_required()
def manage_admin_units():
    admin_units = get_admin_units_for_manage()
    invitations = AdminUnitMemberInvitation.query.filter(AdminUnitMemberInvitation.email == current_user.email).all()

    return render_template('manage/admin_units.html',
        invitations=invitations,
        admin_units=admin_units)

@app.route('/manage/admin_unit/<int:id>')
@auth_required()
def manage_admin_unit(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    response = make_response(redirect(url_for('manage_admin_unit_events', id=admin_unit.id)))
    response.set_cookie('manage_admin_unit_id', str(admin_unit.id))
    return response

@app.route('/manage/admin_unit/<int:id>/reviews')
@auth_required()
def manage_admin_unit_event_reviews(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, 'event:verify'):
        events = list()
        events_paginate = None
    else:
        events_paginate = Event.query.filter(and_(Event.admin_unit_id == admin_unit.id, Event.review_status == EventReviewStatus.inbox)).order_by(Event.start).paginate()
        events = events_paginate.items

    return render_template('manage/reviews.html',
        admin_unit=admin_unit,
        events=events,
        pagination = get_pagination_urls(events_paginate, id=id))

@app.route('/manage/admin_unit/<int:id>/events')
@auth_required()
def manage_admin_unit_events(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizer = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).first()

    if organizer:
        return redirect(url_for('manage_organizer_events', organizer_id=organizer.id))

    flash('Please create an organizer before you create an event', 'danger')
    return redirect(url_for('manage_admin_unit_organizers', id=id))

@app.route('/manage/events')
@auth_required()
def manage_organizer_events():
    organizer = EventOrganizer.query.get_or_404(request.args.get('organizer_id'))
    admin_unit = get_admin_unit_for_manage_or_404(organizer.admin_unit_id)
    organizers = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).all()

    keyword = request.args.get('keyword') if 'keyword' in request.args else ""

    form = FindEventForm(**request.args)
    form.organizer_id.choices = [(o.id, o.name) for o in organizers]

    if keyword:
        like_keyword = '%' + keyword + '%'
        event_filter = and_(Event.organizer_id == organizer.id, Event.review_status != EventReviewStatus.inbox, Event.name.ilike(like_keyword))
    else:
        event_filter = and_(Event.organizer_id == organizer.id, Event.review_status != EventReviewStatus.inbox)

    events = Event.query.filter(event_filter).order_by(Event.start).paginate()
    return render_template('manage/events.html',
        admin_unit=admin_unit,
        organizer=organizer,
        form=form,
        events=events.items,
        pagination=get_pagination_urls(events))

@app.route('/manage/admin_unit/<int:id>/organizers')
@auth_required()
def manage_admin_unit_organizers(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizers = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).paginate()

    return render_template('manage/organizers.html',
        admin_unit=admin_unit,
        organizers=organizers.items,
        pagination=get_pagination_urls(organizers, id=id))

@app.route('/manage/admin_unit/<int:id>/event_places')
@auth_required()
def manage_admin_unit_event_places(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizer = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).first()

    if organizer:
        return redirect(url_for('manage_organizer_event_places', organizer_id=organizer.id))

    flash('Please create an organizer before you create a place', 'danger')
    return redirect(url_for('manage_admin_unit_organizers', id=id))

@app.route('/manage/event_places')
@auth_required()
def manage_organizer_event_places():
    organizer = EventOrganizer.query.get_or_404(request.args.get('organizer_id'))
    admin_unit = get_admin_unit_for_manage_or_404(organizer.admin_unit_id)
    organizers = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).all()

    form = FindEventPlaceForm(**request.args)
    form.organizer_id.choices = [(o.id, o.name) for o in organizers]

    places = EventPlace.query.filter(EventPlace.organizer_id == organizer.id).order_by(func.lower(EventPlace.name)).paginate()
    return render_template('manage/places.html',
        admin_unit=admin_unit,
        organizer=organizer,
        form=form,
        places=places.items,
        pagination=get_pagination_urls(places))

@app.route('/manage/admin_unit/<int:id>/members')
@auth_required()
def manage_admin_unit_members(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, 'admin_unit.members:read'):
        return permission_missing(url_for('manage_admin_unit', id=id))

    members = AdminUnitMember.query.join(User).filter(AdminUnitMember.admin_unit_id == admin_unit.id).order_by(func.lower(User.email)).paginate()
    invitations = AdminUnitMemberInvitation.query.filter(AdminUnitMemberInvitation.admin_unit_id == admin_unit.id).order_by(func.lower(AdminUnitMemberInvitation.email)).all()

    return render_template('manage/members.html',
        admin_unit=admin_unit,
        can_invite_users=has_access(admin_unit, 'admin_unit.members:invite'),
        members=members.items,
        invitations=invitations,
        pagination=get_pagination_urls(members, id=id))

@app.route('/manage/admin_unit/<int:id>/widgets')
@auth_required()
def manage_admin_unit_widgets(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    return render_template('manage/widgets.html', admin_unit=admin_unit)