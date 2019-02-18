from flask import Flask, jsonify, request, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, DateTime,desc
import datetime
import uuid

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///a.db'
app.secret_key = 'A0Zr98j/3yX R~XHH!jmNfgfhdgnhckkfhj'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/account/')
def account():
    if 'username' in session:
        account = Account.query.filter_by(id=session['id']).first()

        return render_template('account/index.html', name=session['username'], balance=account.balance, user=account)
    return redirect("/account/login/", code=302)


@app.route('/account/login/' , methods=['GET', 'POST'])
def accountLogin():
    if request.method == 'POST':
        email = request.form['email']
        ps = request.form['pass']
        account = Account.query.filter(and_(Account.email==email, Account.password==ps)).first()
        if not account:
            return render_template('account/accountLogin.html', erm='Wrong email/password')
        else:
            session['username'] = account.name
            session['id'] = account.id
            return redirect("/account", code=302)
    else:
        return render_template('account/accountLogin.html')


@app.route('/account/logout')
def accountLogout():
    session.pop('username', None)
    session.pop('id', None)
    return redirect("/", code=302)



def addLog(description):
    shortDate, sec = str(datetime.datetime.now()).split('.')
    newLog = Log(date=shortDate, description=description)
    db.session.add(newLog)
    db.session.commit()


@app.route('/account/new', methods=['GET', 'POST'])
def accountReg():
    if request.method == 'POST':
        if request.form['email'] and  request.form['pass'] and request.form['name'] and request.form['surname']:
            email = request.form['email']
            pw = request.form['pass']
            name = request.form['name']
            surname = request.form['surname']
            account = Account.query.filter_by(email=email).first()
            if account:
                return render_template('account/accountReg.html',errm='User exists')
            else:
                if request.form['inviteCode']:
                    invcode = request.form['inviteCode']
                    icode = InviteCode.query.filter_by(code=invcode).first()
                    if icode:
                        newAccount = Account(email=email, password=pw, balance=0, name=name, surname=surname, invitedBy=icode.owner, regdate=datetime.datetime.now(), status=2)
                        db.session.delete(icode)
                    else:
                        return render_template('account/accountReg.html',errm='Wrong invite code!')
                else:
                    newAccount = Account(email=email, password=pw, balance=0, name=name, surname=surname, regdate=datetime.datetime.now(), status=6)
                db.session.add(newAccount)
                db.session.commit()
                addLog('New user registered - ' + newAccount.name + ' ' + newAccount.surname + ' (id ' + str(newAccount.id) + ')')
                session['username'] = newAccount.name
                session['id'] = newAccount.id
                return redirect("/account", code=302)
                #return render_template('account/index.html', name=session['username'], balance=newAccount.balance)

        else:
            return render_template('account/accountReg.html',errm='Something wrong...')
    else:
        return render_template('account/accountReg.html',errm='')


@app.route('/admin/')
def admin():
    allusers = Account.query.count()

    return render_template('admin/index.html', allusers=allusers)


@app.route('/admin/users/')
def userList():
    accounts = Account.query.all()
    acc = list()
    for account in accounts:
        acc.append({'id': account.id, 'name': account.name, 'email': account.email,'status': account.status, 'name':account.name, 'surname': account.surname })
    return render_template('admin/users.html', users=accounts)


@app.route('/admin/logs/')
def showLogs():
    logs = Log.query.order_by(Log.id.desc()).all()
    return render_template('admin/logs.html', logs=logs)


@app.route('/account/updateBasicInfo',methods=['POST'])
def updateBasicInfo():
    account = Account.query.filter_by(id=session['id']).first()
    searchAccount = Account.query.filter_by(phone=request.form['phone']).first()
    if searchAccount:
        if searchAccount.id != account.id:
            return 'phoneExists'
        else:
            account.email = request.form['email']
            account.phone = request.form['phone']
            account.company = request.form['company']
            account.flytype = request.form['flytype']
            db.session.add(account)
            db.session.commit()
            addLog(account.name + ' ' + account.surname + ' changed basic information')
            return 'ok'
    else:
        account.email = request.form['email']
        account.phone = request.form['phone']
        account.company = request.form['company']
        account.flytype = request.form['flytype']
        db.session.add(account)
        db.session.commit()
        addLog(account.name + ' ' + account.surname + ' changed basic information')
        return 'ok'


@app.route('/system/searchByPhone',methods=['POST'])
def searchByPhone():
    account = Account.query.filter_by(phone=request.form['phone']).first()
    if account:
        return account.name + ' ' + account.surname
    else:
        return 'notFound'


@app.route('/account/sendCoins',methods=['POST'])
def sendCoins():
    senderAccount = Account.query.filter_by(id=session['id']).first()
    receiverAccount = Account.query.filter_by(phone=request.form['phone']).first()
    if receiverAccount:
        if senderAccount.balance >= float(request.form['amount']):
            senderAccount.balance = float(senderAccount.balance) - float(request.form['amount'])
            receiverAccount.balance = float(receiverAccount.balance) + float(request.form['amount'])
            db.session.add(senderAccount)
            db.session.add(receiverAccount)
            db.session.commit()
            addLog(senderAccount.name + ' ' + senderAccount.surname + ' sent ' + str(request.form['amount']) + ' APLCoins to ' + receiverAccount.name + ' ' + receiverAccount.surname)
            return 'ok'
        else:
            return 'smallBalance'
    else:
        return 'userNotFound'



@app.route('/account/genInviteCode',methods=['POST'])
def genInviteCode():
    code = str(uuid.uuid4())
    icode = InviteCode(code=code,owner=session['id'])
    db.session.add(icode)
    db.session.commit()
    return code



@app.route('/account/updatePrivacy', methods=['POST'])
def updatePrivacy():
    account = Account.query.filter_by(id=session['id']).first()
    if request.form['showEmail']=='true':
        account.showEmail = True
    else:
        account.showEmail = False

    if request.form['showPhone']=='true':
        account.showPhone = True
    else:
        account.showPhone = False

    if request.form['showFlyType']=='true':
        account.showFlyType = True
    else:
        account.showFlyType = False

    if request.form['showCompany']=='true':
        account.showCompany = True
    else:
        account.showCompany = False


    db.session.add(account)
    db.session.commit()

    return 'ok'


@app.route('/admin/useredit/id=<int:post_id>', methods=['GET', 'POST'])
def userEdit(post_id):
    account = Account.query.filter_by(id=post_id).first()
    inviter = Account.query.filter_by(id=account.invitedBy).first()
    if request.method == 'GET':
        return render_template('admin/useredit.html', user=account, inviter=inviter)
    else:
        account.id = request.form['id']
        account.email = request.form['email']
        account.balance = request.form['balance']
        account.status = request.form['status']
        account.name = request.form['name']
        account.surname = request.form['surname']
        account.password = request.form['password']
        account.reddate = request.form['regdate']
        account.rating = request.form['rating']
        account.phone = request.form['phone']
        account.company = request.form['company']
        account.flytype = request.form['flytype']
        db.session.add(account)
        db.session.commit()
        return render_template('admin/useredit.html',user=account, mess='Saved!')




meetups = db.Table('meetups',
    db.Column('meetup_id', db.Integer, db.ForeignKey('meetup.id')),
    db.Column('account_id', db.Integer, db.ForeignKey('account.id'))
)


class Meetup(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)
    place = db.Column(db.String(100), unique=True, nullable=False)
    owner = db.Column(db.Integer)
    startDate = db.Column(db.DateTime)
    endDate = db.Column(db.DateTime)
    member = db.relationship("Account", secondary=meetups)




class Account(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    surname = db.Column(db.String(100), unique=False, nullable=False)
    password = db.Column(db.String(100), unique=False, nullable=False)
    status = db.Column(db.Integer) # class Status
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(100),default='')
    company = db.Column(db.String(100),default='')
    flytype = db.Column(db.String(100),default='')
    showEmail = db.Column(db.Boolean,default=False)
    showPhone = db.Column(db.Boolean,default=False)
    showCompany = db.Column(db.Boolean,default=False)
    showFlyType = db.Column(db.Boolean,default=False)
    balance = db.Column(db.Float, default=0)
    regdate = db.Column(db.DateTime)
    invitedBy = db.Column(db.Integer)
    rating = db.Column(db.Integer,default=0)
    meetupslist = db.relationship("Meetup", secondary=meetups)
    def __repr__(self):
        return '<Account: ' + self.username + '(id: ' + self.id + ')'

class InviteCode(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    code =  db.Column(db.String(100), unique=True, nullable=False)
    owner =  db.Column(db.Integer)

class Log(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    date =  db.Column(db.String(100))
    description = db.Column(db.String(100))


if __name__ == '__main__':
    app.run(debug=True)
