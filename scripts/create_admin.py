import argparse
from app import create_app
from app.extensions import db
from app.models import User

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--password", required=True)
args = parser.parse_args()
app = create_app()
with app.app_context():
    email = args.email.strip().lower()
    user = User.query.filter_by(email=email).first() or User(email=email, role="admin", active=True)
    user.set_password(args.password)
    db.session.add(user)
    db.session.commit()
    print(f"Compte administrateur prêt : {email}")
