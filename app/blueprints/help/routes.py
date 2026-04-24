from flask import render_template
from flask_login import login_required
from ._bp import help_bp

@help_bp.route('/')
@login_required
def index():
    return render_template('help/index.html')

@help_bp.route('/topic/<topic_id>')
@login_required
def topic(topic_id):
    # This could eventually pull from a database or markdown files
    return render_template(f'help/topics/{topic_id}.html')
