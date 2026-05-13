from flask import render_template, request, jsonify
from flask_login import login_required
from ._bp import tags_bp
from app.models.accounting.tag import Tag
from app.services.auth_service import get_current_org
from app.extensions import db

@tags_bp.route('/')
@login_required
def index():
    org = get_current_org()
    tags = Tag.query.filter_by(organization_id=org.id).all()
    return render_template('tags/index.html', tags=tags)

@tags_bp.route('/api/create', methods=['POST'])
@login_required
def create_tag():
    org = get_current_org()
    data = request.get_json()
    
    new_tag = Tag(
        organization_id=org.id,
        name=data.get('name'),
        type=data.get('tag_type', 'GENERAL'),
        color=data.get('color_code', '#6366f1')
    )
    db.session.add(new_tag)
    db.session.commit()
    return jsonify({
        'id': new_tag.id,
        'name': new_tag.name,
        'tag_type': new_tag.type,
        'color_code': new_tag.color
    })
