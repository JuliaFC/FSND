from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
database_name = "capstone"
database_path = 'postgres://qbeofqzgzkxcgk:e2baa4f34be48554269dd8dc4aff6a5eda5bc81daaecb5ed34307f2ea2c206a9@ec2-52-73-199-211.compute-1.amazonaws.com:5432/df71t1phq444bi'
app.config['SQLALCHEMY_DATABASE_URI'] = database_path

db = SQLAlchemy(app)

from models import User

@app.route('/add/')
def webhook():
    name = "ram"
    email = "ram@ram.com"
    u = User(id = id, nickname = name, email = email)
    print("user created", u)
    db.session.add(u)
    db.session.commit()
    return "user created"

@app.route('/delete/')
def delete():
    u = User.query.get(i)
    db.session.delete(u)
    db.session.commit()
    return "user deleted"

if __name__ == '__main__':
    app.run()