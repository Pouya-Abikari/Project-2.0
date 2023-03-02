from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, join_room, emit
import sqlite3
import os
from markupsafe import escape
from datetime import timedelta
import random
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
socketio = SocketIO(app)

app.config['SECRET_KEY'] = os.urandom(16)
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=5)
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def home():     #a function that handles the root URL '/'
    if 'username' in session:       #checks if a session variable called 'username' exists
        session.permanent = True    #sets the session to be permanent
        yes="yes"                   #creates a variable called yes with the value "yes" which then affetcs the website UI
        return render_template('index.html', state=yes)     #returns the index.html template with the variable state set to the value of yes
    return render_template('index.html')        #returns the index.html template if the user is not logged in

@app.route('/form')
def form():     #a function that handles the '/form' route and returns the 'signup.html' template
    return render_template('signup.html')

@app.route('/about')
def about():        #a function that handles the '/about' route and returns the 'about.html' template
    return render_template('about.html')

@app.route('/compare')
def compare():      #a function that handles the '/compare' route and returns the 'form.html' template
    return render_template('form.html')

@app.route('/settings')    #a function that handles the '/settings' route and returns the 'settings.html' template
def settings():     #a function that handles the '/settings' route and returns the 'settings.html' template
    con = sqlite3.connect('image.db')       #creates a connection to a SQLite database named 'image.db'
    cur = con.cursor()                      #creates a cursor object that can execute SQL commands on the connected database
    cur.execute("SELECT image FROM IMAGES WHERE Username=?" ,[(session['username'])])
    #executes a SQL SELECT statement that retrieves all rows from the 'IMAGE' table where the 'Username' column matches the value of the 'username' session variable.
    match = cur.fetchall()      #fetches all the rows returned by the SQL query and assigns them to the variable 'match'
    con.close()     #close the connection to the database
    return render_template('settings.html', i=match)

@app.route('/account')
def account():      #a function that handles the '/account' route
    con = sqlite3.connect('login.db')               #connects to the SQLite database named 'login.db'
    cur = con.cursor()                              #creates a cursor to perform SQL commands on the database
    cur.execute("SELECT username FROM USER")        #is a SQL command that selects all the usernames from the 'USER' table in the database
    result = [item[0] for item in cur.fetchall()]   #retrieves all the results and store them in the list 'result'
    userName = escape(session['username'])          #retrieves the current user's username from the session and escapes any special characters
    return render_template('account.html', userName=userName, search=result)
    #returns the 'account.html' template, passing the current user's username and the list of usernames to the template for use in the page

@app.route('/Users', methods=['GET'])
def Users():        #a function that handles the '/Users' route
    name = request.args.get('name')     #gets the value of the 'name' argument from the GET request's query string
    con = sqlite3.connect('login.db')   #creates a connection to the SQLite database named 'login.db'
    cur = con.cursor()                  #creates a cursor object that can execute SQL commands on the connected database
    cur.execute("SELECT * FROM USER WHERE Username=?" ,[name])
    #executes a SQL SELECT statement that retrieves all rows from the 'USER' table where the 'Username' column matches the value of the 'name' variable.
    username = cur.fetchall()      #fetches all the rows returned by the SQL query and assigns them to the variable 'match'
    con.close()     #close the connection to the database
    con = sqlite3.connect('image.db')       #creates a connection to a SQLite database named 'image.db'
    cur = con.cursor()                      #creates a cursor object that can execute SQL commands on the connected database
    cur.execute("SELECT image FROM IMAGES WHERE Username=?" ,[name])
    #executes a SQL SELECT statement that retrieves all rows from the 'IMAGE' table where the 'Username' column matches the value of the 'name' variable.
    filename = cur.fetchall()     #fetches all the rows returned by the SQL query and assigns them to the variable 'match2'
    con.close()     #close the connection to the database
    if len(filename) == 0:
        return render_template('users.html',username=username, filename="blank.jpg")
    return render_template('users.html',username=username, filename=filename[0][0])
    #calls the Flask's render_template method which renders the 'users.html' template and returns it to the client, passing the variable 'match' as 'i' to the template.


@app.route('/signup',methods=['POST'])
def signup():       #defines the function that will be executed when the above route is accessed
    con = sqlite3.connect('login.db')       #creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()                      #creates a cursor object that can execute SQL commands on the connected database
    cur.execute("SELECT * FROM USER WHERE Username=?" ,[(request.form['un'])])
    #executes a SQL SELECT statement that retrieves all rows from the 'USER' table where the 'Username' column matches the value of the 'un' field from the form data sent in the POST request.
    match = len(cur.fetchall())     #fetches all the rows returned by the SQL query and assigns the number of rows to the variable 'match'
    con.close()     #close the connection to the database
    if match == 0:      #check if the number of matching rows is equal to 0, then proceed to insert the new user data into the 'USER' table
        con = sqlite3.connect('login.db')
        cur = con.cursor()
        cur.execute("INSERT INTO USER(fname,sname,username,password,email)VALUES (?,?,?,?,?)",
                        (request.form['fname'],request.form['sname'],request.form['un'],request.form['pw'],request.form['email']))
        #execute a SQL INSERT statement that inserts the values of the 'fname', 'sname', 'un', 'pw', and 'email' fields from the form data sent in the POST request into the 'USER' table
        con.commit()
        con.close()
        session.permanent = True    #sets the session to be permanent
        session['username'] = request.form['un']    #stores the 'un' field from the form data sent in the POST request as the 'username' in the session
        session['chat'] = None      #initializes the 'chat' session variable to None
        return redirect(url_for('account'))     #redirect the client to the 'account' route
    else:
        error='Username already exists, choose another username.'
        return render_template('signup.html', error=error)  #If the number of matching rows is not equal to 0, then proceed to render the 'signup.html' template
                                                            #and passing the 'error' variable with the value of 'Username already exists, choose another username.' as a parameter

@app.route('/signupform',methods=['POST'])
def signupform():       #a function that will be executed when this route is accessed
    con = sqlite3.connect('login.db')       #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()                      #creates a cursor object that is used to execute SQL commands on the database connection
    cur.execute("INSERT INTO FORM(username,gender,age,hobby1,hobby2,hobby3,phone,colour1,colour2,course1,course2,course3,year,bio)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (session['username'],request.form['gender'],request.form['age'],request.form['hobby1'],request.form['hobby2'],request.form['hobby3'],request.form['phone'],request.form['colour1'],request.form['colour2'],request.form['course1'],request.form['course2'],request.form['course3'],request.form['year'],request.form['bio']))
                    #is an sql statement that insert form data in to the table 'FORM'
    con.commit()    #saves the changes made to the database
    con.close()     #closes the connection to the database
    return "added"

@app.route('/create')
def create():       #a function that will be executed when this route is accessed
    con = sqlite3.connect('login.db')       #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()                      #creates a cursor object that is used to execute SQL commands on the database connection
    cur.execute("""CREATE TABLE USER(
                    fname VARCHAR(15) NOT NULL,
                    sname VARCHAR(20) NOT NULL,
                    username VARCHAR(20) NOT NULL PRIMARY KEY,
                    password VARCHAR(20) NOT NULL,
                    email VARCHAR(25) NOT NULL)
                """)    #is an sql statement that creates a table in the database named 'USER' with five columns, with specific data types and constraints
    return 'created'    #returns a string "created" as a response

@app.route('/createpic')
def createpic():
    con = sqlite3.connect('image.db')
    cur = con.cursor()
    cur.execute("""CREATE TABLE PICS(
                    usernamee VARCHAR(20) NOT NULL,
                    image VARCHAR(30) NOT NULL)
                """)
    return 'created pic'

@app.route('/createavatar')
def createavatar():
    con = sqlite3.connect('image.db')
    cur = con.cursor()
    cur.execute("""CREATE TABLE AVATAR(
                    usernamee VARCHAR(20) NOT NULL PRIMERY KEY,
                    avatar VARCHAR(30) NOT NULL)
                """)
    return 'created avatar'

@app.route('/createform')
def createform():       #a function that will be executed when this route is accessed
    con = sqlite3.connect('login.db')       #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()                      #creates a cursor object that is used to execute SQL commands on the database connection
    cur.execute("""CREATE TABLE FORM(
                    username VARCHAR(20) NOT NULL PRIMARY KEY,
                    gender VARCHAR(10) NOT NULL,
                    age INT NOT NULL,
                    hobby1 VARCHAR(20) NOT NULL,
                    hobby2 VARCHAR(20) NOT NULL,
                    hobby3 VARCHAR(20),
                    phone VARCHAR(15) NOT NULL,
                    colour1 VARCHAR(10) NOT NULL,
                    colour2 VARCHAR(10),
                    course1 VARCHAR(20) NOT NULL,
                    course2 VARCHAR(20) NOT NULL,
                    course3 VARCHAR(20) NOT NULL,
                    year INT NOT NULL,
                    bio VARCHAR(150) NOT NULL)
                """)        #is an sql statement that creates a table in the database named 'FORM' with 14 columns, with specific data types and constraints
    return 'created form'   #returns a string "created form" as a response

@app.route('/createmsg')
def createmsg():        #a function that will be executed when this route is accessed
    con = sqlite3.connect('login.db')       #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()                      #creates a cursor object that is used to execute SQL commands on the database connection
    cur.execute("""CREATE TABLE MSG(
                    sender VARCHAR(20) NOT NULL,
                    receiver VARCHAR(20) NOT NULL,
                    msg VARCHAR(250) NOT NULL)
                """)    #is an sql statement that creates a table in the database named 'MSG' with three columns, with specific data types and constraints
    return 'created msg table'  #returns a string "created msg table" as a response

@app.route("/createcontacts")
def createcontacts():       #a function that will be executed when this route is accessed
    con = sqlite3.connect("login.db")       #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()                      #creates a cursor object that is used to execute SQL commands on the database connection
    try:        #The try-except block is checking if there is an exception when trying to execute the
                #SQL statement which creates a table 'contacts' with two columns user and contact with specific data types and constraints
        cur.execute(""" CREATE TABLE contacts(
                        user VARCHAR(20) NOT NULL,
	                    contact VARCHAR(20) NOT NULL)
                    """)
    except sqlite3.OperationalError as e:   #If there's an exception the code will return the error message as a string
        return str(e)
    return "table contacts created"     #if there's no error, it will return "table contacts created"

@app.route('/imagetable')
def imagetable():
    con = sqlite3.connect('image.db')
    cur = con.cursor()
    cur.execute("""CREATE TABLE IMAGES(
                    username VARCHAR(20) NOT NULL,
                    image VARCHAR(30) NOT NULL)
                """)
    return 'created image table'

@app.route('/select')
def select():       #a function that will be executed when this route is accessed
    if 'username' in session:       #check if the session variable 'username' exists or not
        session.permanent = True    #makes the session last until the user closes the browser
        request.form.get['un'] = escape(session['username'])    #the variable 'un' is set equal to the escaped value of session variable 'username'
        con = sqlite3.connect('login.db')   #line creates a connection to a SQLite database named 'login.db'
        cur = con.cursor()
        cur.execute("SELECT hobby1, hobby2, hobby3 FROM USER WHERE Username='un' ") #is an sql statement that selects hobby1, hobby2, hobby3 from table 'USER'
                                                                                    #where the column 'Username' is equal to the variable 'un'
        rows = cur.fetchall()   #fetches all the rows from the executed query and store them in the variable 'rows'
        return str(rows)        #returns the rows as a string

@app.route('/msg', methods=['POST'])
def msg():      #a function that will be executed when this route is accessed
    con = sqlite3.connect('login.db')   #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()
    cur.execute("INSERT INTO MSG(sender, receiver, message) VALUES (?,?,?)",(session['username'], request.form['receiver'], request.form['message']))
                                    #is an sql statement that insert a new message into the table 'MSG' with three columns, sender, receiver and message
                                    #The values for these columns are taken from the session variable 'username', the request form variable 'receiver' and
                                    #the request form variable 'message' respectively
    con.commit()    #saves the changes made to the database
    con.close()     #closes the connection to the database
    return 'inserted into MSG'      #returns a string "inserted into MSG" as a response

@app.route('/login', methods=['POST'])  #decorator is defining the route and specifying that it only accepts HTTP POST requests
def login():        #line defines a function that will be executed when this route is accessed
    con = sqlite3.connect('login.db')   #line creates a connection to a SQLite database named 'login.db'
    cur = con.cursor()
    cur.execute("SELECT * FROM USER WHERE Username=? AND Password=?",
    (request.form['un'],request.form['pw']))    #is an sql statement that selects all rows from the 'USER' table where the column 'Username' and
                                                #'Password' match the request form variables 'un' and 'pw' respectively
    match = len(cur.fetchall())     #fetches all the rows from the executed query, count the rows and store the count in the variable 'match'
    if match == 0:      #check if match equals 0, if true it means no match found
        error='Wrong username and password, try again.'
        return render_template('index.html', error=error)   #in this case, it renders the index.html template with an error message
    else:
        session.permanent = True
        session['username'] = request.form['un']
        session['chat'] = None
        return redirect(url_for('account'))     #in this case, the session is set as permanent, the session variable 'username' is
                                                #set to the request form variable 'un' and session variable 'chat' is set to None, and the user is redirected to
                                                #the 'account' page

@app.route('/un')
def un():   #a function that will be executed when this route is accessed
    if 'username' in session:       #check if there is a username in the session
        return 'Logged in as %s' % escape(session['username'])  #if the session variable 'username' exists it returns a string "Logged in as {username}"
                                                                #where {username} is the escaped value of session variable 'username'
    return 'You are not logged in'      #if the session variable 'username' does not exist, it returns a string "You are not logged in"

@app.route('/logout')
def logout():   #line defines a function that will be executed when this route is accessed
    session.pop('username', None)       #removes the 'username' key from the session, if it exists
    logout="User logged out successfully!"      #creates a variable logout and assigns the value "User logged out successfully!" to it
    return render_template('index.html', logout=logout)     #Renders the 'index.html' template and pass the logout variable to it

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():     #line defines a function that will be executed when this route is accessed
    if request.method == 'GET':     #check if the request method is GET, if true it renders the 'contact.html' template
        return render_template('contact.html')
    else:                           #if the request method is not GET, it's a POST request
        if  request.form['user'] == escape(session['username']):     #check if the session variable 'username' is equal to the request form variable 'user'
            error = "you can't add yourself as a contact"    #if true, it creates a variable 'yourself' and assigns the value "you can't add yourself as a contact" to it
            con = sqlite3.connect('login.db')
            cur = con.cursor()
            cur.execute("SELECT contact FROM contacts WHERE user=?", (session['username'],))    #selects all rows from the 'contacts' table where the 'user' column matches the session's username
            result = [item[0] for item in cur.fetchall()]
            con.close()
            return render_template('message.html', error=error, chat=session['chat'], contacts=result)     #if true, it renders the 'contact.html' template and passes the variable 'yourself' to it
        else:       #if the session variable 'username' is not equal to the request form variable 'user'
            con = sqlite3.connect('login.db')
            cur = con.cursor()
            cur.execute("SELECT * FROM USER WHERE username=?",
                (request.form['user'],))    #is an sql statement that selects all rows from the 'USER' table where the column 'username' matches the request form variable 'user'
            result = cur.fetchall()     #fetches all the rows from the executed query and store them in the variable 'result'
            con.close()
            if len(result) == 0:
                error = "username not recognised"       #if the length of the result is 0, it means no match found and creates a variable 'error' and assigns the value "username not recognised" to it
                con = sqlite3.connect('login.db')
                cur = con.cursor()
                cur.execute("SELECT contact FROM contacts WHERE user=?", (session['username'],))    #selects all rows from the 'contacts' table where the 'user' column matches the session's username
                result = [item[0] for item in cur.fetchall()]
                con.close()
                return render_template('message.html', error=error, chat=session['chat'], contacts=result)     #if true, it renders the 'contact.html' template and passes the variable 'error' to it
            else:       #if the length of the result is not 0, it means a match is found
                con = sqlite3.connect('login.db')
                cur = con.cursor()
                cur.execute("SELECT * FROM contacts WHERE user=? and contact=?",
                    (session['username'],request.form['user']))     #is an sql statement that selects all rows from the 'contacts' table where the column 'user' matches the
                                                                    #username in session and column 'contact' matches with user
                result = cur.fetchall()     #fetches all the rows from the table that match the query and assigns the result to the variable 'result'
                if len(result) == 0:        #checks if the length of the result is equal to 0, if it is, it executes an SQL query to insert a new row into
                                            #the 'contacts' table with the session's username and the user input as the values for the 'user' and 'contact' columns respectively
                    cur.execute("INSERT INTO contacts (user, contact) VALUES (?,?)",
                        (session['username'],request.form['user']))
                    con.commit()
                    con.close()
                    con = sqlite3.connect('login.db')
                    cur = con.cursor()
                    cur.execute("SELECT contact FROM contacts WHERE user=?", (session['username'],))    #selects all rows from the 'contacts' table where the 'user' column matches the session's username
                    result = [item[0] for item in cur.fetchall()]
                    con.close()
                    return render_template('message.html', chat=session['chat'], contacts=result)     #if true, it renders the 'message.html' template with the contact added
                else:
                    error = "contact exists"       #if the length of the result is not 0, it means the contact already exists and creates a variable 'exists' and assigns the value "contact exists" to it
                    con = sqlite3.connect('login.db')
                    cur = con.cursor()
                    cur.execute("SELECT contact FROM contacts WHERE user=?", (session['username'],))    #selects all rows from the 'contacts' table where the 'user' column matches the session's username
                    result = [item[0] for item in cur.fetchall()]
                    con.close()
                    return render_template('message.html', error=error, chat=session['chat'], contacts=result)     #if true, it renders the 'message.html' template and passes the variable 'exists' to it

@app.route('/message')
def message():
    con = sqlite3.connect('login.db')
    cur = con.cursor()
    cur.execute("SELECT contact FROM contacts WHERE user=?", (session['username'],))    #selects all rows from the 'contacts' table where the 'user' column matches the session's username
    result = [item[0] for item in cur.fetchall()]   #fetches all the rows from the table that match the query and assigns it to the variable 'result'
                                                    #Then it uses list comprehension to extract the first element of each tuple in the result which is the contact name
    return render_template('message.html', chat=session['chat'], contacts=result)   #the result is then copied into contacts

@app.route('/send', methods=['POST'])
def send():
    return redirect(url_for('message'))

@app.route('/getMsgs', methods=['GET'])
def getMsgs():
    session['chat'] = request.args.get("name")  #This line sets a session variable 'chat' to the value of the 'name' query parameter of the GET request
    con = sqlite3.connect('login.db')
    cur = con.cursor()
    usr = session['username']   #This line gets the value of the 'username' session variable
    chat = session['chat']
    cur.execute("""SELECT sender, msg FROM MSG WHERE (receiver=? AND sender=?) OR (receiver=? AND sender=?)""", (usr,chat,chat,usr))
    #selects the sender and message from the MSG table where either the receiver is the value of the 'username' session variable and
    #the sender is the value of the 'chat' session variable, or the receiver is the value of the 'chat' session variable and the sender is the value of the 'username' session variable
    rows = cur.fetchall()   #This line retrieves all the rows returned by the previous SQL statement and stores them in a variable called 'rows'
    return rows     #This line returns the rows as the response of the GET request

@app.route('/createforgot')
def createforgot():
    con = sqlite3.connect("forgot.db")
    cur = con.cursor()
    try:
        cur.execute(""" CREATE TABLE verify(
            verify CHAR(5) NOT NULL)
                    """)
    except sqlite3.OperationalError as e:
        return str(e)
    return "table verify created"

@app.route('/forgot', methods=['POST'])
def forgot():
    verify = (random.randrange(1, 10))
    con = sqlite3.connect('forgot.db')
    cur = con.cursor()
    cur.execute("INSERT INTO USER (verify) VALUES (?)", (verify))
    con.commit()
    return render_template('forgot.html')

@socketio.on('join')
def on_join(data):
    userName = escape(session['username'])  #This line gets the value of the 'username' session variable, and applies the escape function to it
    receiver = data['room']     #This line gets the 'room' field of the data passed in the 'join' event
    input = data['msg']     #This line gets the 'msg' field of the data passed in the 'join' event
    con = sqlite3.connect('login.db')
    cur = con.cursor()
    cur.execute("INSERT INTO MSG (sender, receiver, msg) VALUES (?,?,?)",
    	       		( userName ,receiver , input))      #This line executes an SQL statement that inserts the userName, receiver, and input as a new row in the MSG table
    con.commit()
    con.close()
    S = str(receiver + ' ' + userName)   #This line combines the receiver and userName variables into a single string
    NS = (Order(S))   #This line creates a room code by combining the receiver and userName variables and applying the Order function to it
    roomcode = NS.replace(" ", "")
    join_room(roomcode)     #This line join the room specified in the data passed in the 'join' event
    emit('chat message', data['msg'], to=roomcode)      #This line emits a 'chat message' event to the room specified in the data passed
                                                            #in the 'join' event, with the data['msg'] as the data of the event

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(session['username'] + '.jpg')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            con = sqlite3.connect('image.db')
            cur = con.cursor()
            cur.execute("INSERT INTO IMAGES (username, image) VALUES (?,?)",(session['username'],filename))
            con.commit()
            return render_template('settings.html')

@app.route('/avatarimg', methods=['POST'])
def avatarimg():
    con = sqlite3.connect('image.db')
    cur = con.cursor()
    cur.execute("INSERT INTO AVATAR (username, avatar) VALUES (?,?)",(session['username'],request.form['avatar']))
    con.commit()
    return 'INSERT avatar'


def Order(S):
    W = S.split(" ")
    for i in range(len(W)):
        W[i] = W[i].lower()
    W.sort()

    return ' '.join(W)
