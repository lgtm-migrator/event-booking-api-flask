import datetime

from flask import jsonify, request
from marshmallow import Schema, fields, validate

from app import app, db, jwttoken, max_len
from app.common import parse_args_with_schema, token_auth_required
from app.errors import Error, StatusCode
from app.models.location import Location
from app.models.organizer import Organizer


class LocationCreateSchema(Schema):
    name_location = fields.String(validate=validate.Length(max=max_len), required=True)
    address = fields.String(validate=validate.Length(max=max_len), required=True)
    capacity = fields.Integer(required=True)


class LocationUpdateSchema(Schema):
    name_location = fields.String(validate=validate.Length(max=max_len))
    address = fields.String(validate=validate.Length(max=max_len))
    capacity = fields.Integer()


class LocationListAllSchema(Schema):
    page = fields.Integer()


@app.route('location/new', methods=['POST'])
@parse_args_with_schema(LocationCreateSchema)
@token_auth_required
def location_create(user, user_type, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    location = Location.query.filter_by(address=args['address']).first()
    if location is not None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Duplicated location')
    location = Location(
        name_location=args['name_location'],
        address=args['address'],
        capacity=args['capacity'],
        owner_id=user.id
    )
    db.session.add(location)
    db.session.commit()
    return jsonify({
        'message': 'Location created successfully',
        'data': location.serialize()
    }), 201


@app.route('location/update/<int:location_id>', methods=['PUT'])
@parse_args_with_schema(LocationUpdateSchema)
@token_auth_required
def location_update(user, user_type, location_id, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    location = Location.query.filter_by(id=location_id, owner_id=user.id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    location.update(**args)
    db.session.commit()
    return jsonify({
        'message': 'Location updated successfully',
        'data': location.serialize()
    }), 201


@app.route('location/delete/<int:location_id>', methods=['DELETE'])
@token_auth_required
def location_delete(user, user_type, location_id):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    location = Location.query.filter_by(id=location_id, owner_id=user.id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    location.delete()
    db.session.commit()
    return jsonify({
        'message': 'Location deleted successfully'
    }), 201


@app.route('location/list', methods=['GET'])
@parse_args_with_schema(LocationListAllSchema)
def location_list_all():
    page = None if request.args.get('page') is None else int(request.args.get('page'))
    result = Location.query.paginate(page=page, per_page=15)
    has_next = 1
    if page is not None and page == -(-result.total // 10):
        has_next = 0
    elif page is None:
        has_next = 0

    return jsonify({
        'has_next': has_next,
        'organizers': [x.serialize() for x in result.items]
    }), 200


@app.route('location/info/<int:location_id>', methods=['GET'])
def location_get_specific_info(location_id):
    location = Location.query.filter_by(id=location_id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    return jsonify({'result': location.serialize()}), 200


@app.route('location/list/<int:owner_id>', methods=['GET'])
@parse_args_with_schema(LocationListAllSchema)
def location_get_by_owner(owner_id):
    owner = Organizer.query.filter_by(id=owner_id).first()
    if owner is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Owner not found')
    
    page = None if request.args.get('page') is None else int(request.args.get('page'))
    result = Location.query.filter_by(owner_id=owner_id).paginate(page=page, per_page=15)
    has_next = 1
    if page is not None and page == -(-result.total // 10):
        has_next = 0
    elif page is None:
        has_next = 0

    return jsonify({
        'owner_id': owner_id,
        'has_next': has_next,
        'locations': [x.serialize() for x in result.items]
    }), 200

