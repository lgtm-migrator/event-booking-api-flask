import datetime

from flask import jsonify, request
from marshmallow import Schema, fields, validate

from app import app, db, jwttoken, max_len
from app.common import parse_args_with_schema, token_auth_required
from app.errors import Error, StatusCode
from app.models.organizer import Organizer


class UserSignUpSchema(Schema):
    email = fields.Email(validate=validate.Length(max=max_len), required=True)
    password = fields.String(validate=validate.Length(max=max_len), required=True)
    firstname = fields.String(validate=validate.Length(max=max_len), required=True)
    lastname = fields.String(validate=validate.Length(max=max_len), required=True)
    phone = fields.String(validate=validate.Length(max=max_len), required=True)


class UserLogInSchema(Schema):
    email = fields.Email(validate=validate.Length(max=max_len), required=True)
    password = fields.String(validate=validate.Length(max=max_len), required=True)


class UserUpdateSchema(Schema):
    email = fields.Email(validate=validate.Length(max=max_len))
    password = fields.String(validate=validate.Length(max=max_len))
    firstname = fields.String(validate=validate.Length(max=max_len))
    lastname = fields.String(validate=validate.Length(max=max_len))
    phone = fields.String(validate=validate.Length(max=max_len))


class UserListAllSchema(Schema):
    page = fields.Integer()


@app.route('organizer/register', methods=['POST'])
@parse_args_with_schema(UserSignUpSchema)
def organizer_register(args):
    organizer = Organizer.query.filter_by(email=args['email']).first()
    if organizer is not None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Duplicated email')
    organizer = Organizer(**args)
    organizer.set_password(password = args['password'])
    db.session.add(organizer)
    db.session.commit()
    return jsonify({
        'message': 'Attendee created successfully',
        'data': organizer.serialize()
    }), 201


@app.route('organizer/login', methods=['POST'])
@parse_args_with_schema(UserLogInSchema)
def organizer_login(args):
    organizer = Organizer.query.filter_by(email=args['email']).first()
    if organizer and organizer.check_password(args['password']):
        return jsonify({
            'access_token': jwttoken.encode(organizer.id, 'Organizer')
        }), 200
    raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid email or password.')


@app.route('organizer/info/update', methods=['PUT'])
@parse_args_with_schema(UserUpdateSchema)
@token_auth_required
def organizer_update_info(user, user_type, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    user.update(**args)
    if len(args['password']) > 0:
        user.set_password(args['password'])
    db.session.commit()
    return jsonify({
        'message': 'Organizer updated successfully',
        'data': user.serialize()
    }), 201


@app.route('organizer/info', methods=['GET'])
@token_auth_required
def organizer_get_info(user, user_type):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    return jsonify({
        'result': user.serialize()
    }), 200


@app.route('organizer/list', methods=['GET'])
@parse_args_with_schema(UserListAllSchema)
def organizer_list_all():
    page = None if request.args.get('page') is None else int(request.args.get('page'))
    result = Organizer.query.paginate(page=page, per_page=15)
    has_next = 1
    if page is not None and page == -(-result.total // 10):
        has_next = 0
    elif page is None:
        has_next = 0

    return jsonify({
        'has_next': has_next,
        'organizers': [x.serialize() for x in result.items]
    }), 200


@app.route('organizer/list/<int:organizer_id>', methods=['GET'])
def organizer_get_specific_info(organizer_id):
    organizer = Organizer.query.filter_by(id=organizer_id).first()
    if organizer is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Organizer not found.')
    return jsonify(organizer.serialize()), 200
