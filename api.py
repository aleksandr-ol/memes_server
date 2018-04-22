from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import settings

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + settings.db_user + ':' + settings.db_pass + '@' +\
                                        settings.db_host + ':3306/' + settings.db_name

db = SQLAlchemy(app)


class Parsed_posts(db.Model):
    id = db.Column(db.String, primary_key=True)
    text = db.Column(db.String)
    likes = db.Column(db.Integer)
    reposts = db.Column(db.Integer)
    group_id = db.Column(db.Integer)
    date = db.Column(db.Integer)
    attachments = db.Column(db.String)


@app.route('/mems/offset=<offset>', methods=['GET'])
def get_all_memes(offset):
    memes = Parsed_posts.query.order_by(Parsed_posts.date.desc()).offset(offset).limit(10).all()
    output = []

    for mem in memes:
        mem_data = {}
        mem_data['id'] = mem.id
        mem_data['text'] = mem.text
        mem_data['likes'] = mem.likes
        mem_data['reposts'] = mem.reposts
        mem_data['group_id'] = mem.group_id
        mem_data['date'] = mem.date
        mem_data['attachments'] = json.loads(mem.attachments)
        output.append(mem_data)

    return json.dumps(output)


# @app.route('/mem/<mem_id>', methods=['GET'])
# def get_one_mem(mem_id):
#     return ''
#
# if __name__ == '__main__':
#     app.run(host="0.0.0.0", debug=True)
