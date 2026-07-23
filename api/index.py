from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_wtf import FlaskForm 
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp
import sqlalchemy as sqla
import base64
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRITKEY")
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://root:{os.getenv("RAILWAYPASSWORD")}@{os.getenv("RAILWAYTCPIP")}:{os.getenv("RAILWAYPORT")}/socialmedia"

engine = sqla.create_engine(app.config["SQLALCHEMY_DATABASE_URI"])


"""
This is for creating forms
"""

class Login(FlaskForm):
    user_name = StringField(label="User Name", validators=[DataRequired()])
    password = PasswordField(label="PassWord", validators=[DataRequired()])
    submit = SubmitField(label="Submit")

class _SignUp(FlaskForm):

    avatar = FileField('image', validators = [FileAllowed(set(['jpeg', 'png', 'jpg']), 'Images only')], name='avatar')

    name = StringField(label= "Name", validators=[DataRequired(), Regexp(
            r'^[a-zA-Z\s]{2,50}$',
            message="Name can only contain letters and spaces (2-50 characters)."
        )])
    user_name = StringField(label="User Name", validators=[DataRequired(), Regexp(
            r'^[a-zA-Z0-9_]{3,30}$',
            message="Username must be 3-30 characters long and contain only letters, numbers, and underscores."
        )])
    password = PasswordField(label="PassWord", validators=[DataRequired(), Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            message="Password must be at least 8 characters long, contain an uppercase letter, lowercase letter, number, and a special character (@$!%*?&)."
        )])
    submit = SubmitField(label="Submit")

class _UserPost(FlaskForm):
    posttitle = StringField(label="Title", validators=[DataRequired()], description="Title of the post.")
    postcontent = TextAreaField(label="Content", default="", description="Write something about your post!!")
    postupload = SubmitField(label="Squek...")

class _UserMessage(FlaskForm):
    to = StringField(label= "recever", validators=[DataRequired()])
    message = TextAreaField(label="message", validators=[DataRequired()])
    send = SubmitField(label="Send")

"""
This is main App, i should have use blue print
"""

@app.route("/", methods=["post", "get"])
def index(limits=10):
    #get posts
    
    if request.method == "POST":
        action = request.form.get
        print(action)
            
        if action("Like"):
            _POSTID = action("Like").split("@")[0]
            _OriginalPostBy = action("Like").split("@")[1]
            _Logedinusername = session.get("Squirrel::user_name")
            _Logedinpassword = session.get("Squirrel::password")
            print(_POSTID, _Logedinusername)
            if _Logedinusername is None or _Logedinpassword is None:
                return redirect(url_for("index"))

            with engine.begin() as conn:
                #check if user name and passwords are correct
                command = sqla.text("Select count(user_name) from user where user_name= :user_name and password = :password")
                AuthenticateUser = conn.execute(command, {"user_name": _Logedinusername, "password": _Logedinpassword})
                if AuthenticateUser.rowcount == 1:
                    _check_if_like_exists = sqla.text("select  likeid from likes where postid = :post and userid = :userid and PostedUserId = :Posteduser")
                    _check_if_like_exists = conn.execute(_check_if_like_exists, {"post" : _POSTID, "userid": _Logedinusername, "Posteduser": _OriginalPostBy})
                    if _check_if_like_exists.rowcount == 0:
                        _update_likes_command = sqla.text("insert into likes (userid , postid, PostedUserId) values (:userid, :postid, :PostedUserId)")
                        
                        conn.execute(_update_likes_command, {"userid": _Logedinusername, "postid": _POSTID, "PostedUserId": _OriginalPostBy})
                        command = sqla.text("update post set likes = likes + 1 where postid = :postid")
                        conn.execute(command, {"postid": _POSTID})
                        conn.commit()

    if request.args.get("limits"):
        limits = int(request.args.get("limits"))
    
    _getpost = sqla.text("select * from post order by likes desc limit :limit")
    UserName = None
    _session_user_name = session.get("Squirrel::user_name")
    _session_password = session.get("Squirrel::password")
    if _session_user_name is not None and _session_password is not None:
        ##check for proper credentials
        _secure_check = sqla.text("select * from user where user_name = :user_name and password = :password")
        with engine.begin() as conn:
            _secure_check = conn.execute(_secure_check, {"user_name": _session_user_name, "password": _session_password})
            if _secure_check.rowcount == 1:
                _secure_check = next(_secure_check)
                user_name = _secure_check[0]
                Name = _secure_check[1]
                avatar = base64.b64encode(_secure_check[3]).decode("utf-8")
                _type = _secure_check[4]
                UserName = [Name, user_name, avatar, _type]

    with engine.begin() as conn:
        result = conn.execute(_getpost, {"limit": limits})
    return render_template("index.html", post=result, UserName= UserName)

@app.route("/login", methods= ["get", "post"])
def login():
    form = Login()
    if form.validate_on_submit():
        user_name = form.user_name.data
        password = form.password.data
        print("Loging in as ", user_name, " Password: ", password)
        with engine.begin() as conn:
            result = conn.execute(sqla.text(f"Select * from User where user_name = '{user_name}' and binary password= '{password}';"))
            if result.rowcount > 0:
                session["Squirrel::user_name"] = user_name
                session["Squirrel::password"] = password
                return redirect(url_for('UserProfile', name=user_name))
            else:
                flash("Invalid User Name or Password")
        

    return render_template("login.html", form= form)

@app.route("/signup", methods=['get', 'post'])
def SignUp():
    form = _SignUp()
    if form.validate_on_submit():
        user_name = form.user_name.data
        name = form.name.data
        password = form.password.data
        avatar = 'default'
        _type = 'txt'
        
        data = form.avatar.data
        
        if data.filename != "":
            avatar = data.read()
            _type = data.mimetype

        form.user_name.data = ""
        form.password.data = ""
        form.name.data = ""
        #Cheack if Username already exists?
        with engine.begin() as conn:
            result = conn.execute(sqla.text(f"Select * from User where user_name = :username;"), {'username': {user_name}})
            if result.rowcount > 0:
                flash(f"UserName {user_name} already exists")
                return UserProfile(user_name)
            else:
                query = sqla.text("insert into user (user_name, name, password, avatar, type) values (:user_name, :name, :password, :avatar, :type)")
                conn.execute(query, {"user_name": user_name, "name": name, "password": password, "avatar": avatar, "type": _type})
                #conn.execute(sqla.text(f"insert into user values ('{user_name}', '{name}', '{password}', {avatar}, '{_type}');"))
                conn.commit()
            session["Squirrel::user_name"] = user_name
            session["Squirrel::password"] = password
            return redirect(url_for('UserProfile', name=user_name))

    return render_template("signup.html", form= form)

@app.route("/user/<name>", methods=["post", "get"])
def UserProfile(name):

    if request.method == "POST":
        action = request.form.get
        LikedUserID = None
        PostedUserId = None
        if action("Like"):
            _POSTID = action("Like")
            _Logedinusername = session.get("Squirrel::user_name")
            _Logedinpassword = session.get("Squirrel::password")
            with engine.begin() as conn:
                command = sqla.text("Select user_name, password from user where user_name = :User_name and password = :Password")
                result = conn.execute(command, {"User_name": _Logedinusername, "Password": _Logedinpassword})
                if result.rowcount != 0:
                    LikedUserID = _Logedinusername
                    PostedUserId = name
            with engine.begin() as conn:
                _check_if_like_exists = sqla.text("select  likeid from likes where postid = :post and userid = :userid and PostedUserId = :Posteduser")
                _check_if_like_exists = conn.execute(_check_if_like_exists, {"post" : _POSTID, "userid": _Logedinusername, "Posteduser": name})
                if _check_if_like_exists.rowcount == 0:
                    _update_likes_command = sqla.text("insert into likes (userid , postid, PostedUserId) values (:userid, :postid, :PostedUserId)")
                    conn.execute(_update_likes_command, {"userid": LikedUserID, "postid": _POSTID, "PostedUserId": PostedUserId})
                    command = sqla.text("update post set likes = likes + 1 where postid = :postid")
                    command_to_update_total_likes_in_user = sqla.text("update user set total_likes = total_likes + 1 where user_name = :user_name")
                    conn.execute(command, {"postid": _POSTID})
                    conn.execute(command_to_update_total_likes_in_user, {"user_name": name})
                    conn.commit()
            
        if action("Follow"):
            _LOGIN_USER = session.get("Squirrel::user_name")
            _FOLLOW_USER = action("Follow")
            if _LOGIN_USER != _FOLLOW_USER:
                with engine.begin() as conn:
                    #check is one user already follow other user?
                    command = sqla.text("Select * from follow where UserId = :follwer_name and FollowsID = :following_name")
                    _SqlCommand = conn.execute(command, {"follwer_name": _LOGIN_USER, "following_name" : _FOLLOW_USER})
                    if _SqlCommand.rowcount == 0:
                        print(_SqlCommand.rowcount)
                        _Add_Follower_Command = sqla.text("insert into follow values (:UserId, :FollowsID)")
                        update_user_follows_for_loged_user = sqla.text("update  user set total_follow = total_follow + 1 where user_name = :user_name")
                        update_user_following_for_name_user = sqla.text("update  user set total_following = total_following + 1 where user_name = :user_name")
                        conn.execute(update_user_follows_for_loged_user, {"user_name": _LOGIN_USER})
                        conn.execute(update_user_following_for_name_user, {"user_name": name})
                        conn.execute(_Add_Follower_Command, {"FollowsID": _FOLLOW_USER, "UserId": _LOGIN_USER})
                        conn.commit()
    

    AUTHENTICATION_LEVEL = 0
    
    form = _UserPost()
    form_private_message = _UserMessage()

    #insert into post and private message
    if form.validate_on_submit():
        PostedUserId = None
        _Logedinusername = session.get("Squirrel::user_name")
        _Logedinpassword = session.get("Squirrel::password")
        with engine.begin() as conn:
            command = sqla.text("Select user_name, password from user where user_name = :User_name and password = :Password")
            result = conn.execute(command, {"User_name": _Logedinusername, "Password": _Logedinpassword})
            if result.rowcount != 0:
                PostedUserId = name
        
        if PostedUserId is not None:
            postTitle = form.posttitle.data
            postContent = form.postcontent.data

            AddPost = sqla.text("INSERT INTO post (postUserId, PostTitle, postContent) value(:PostUserId, :postTitle, :postContent)")
            try:
                with engine.begin() as conn:
                    conn.execute(AddPost, {"PostUserId": _Logedinusername, "postTitle": postTitle, "postContent": postContent})
                    conn.commit()
            except Exception as e:
                print(e)
    
    if form_private_message.validate_on_submit():
        PostedUserId = None
        _Logedinusername = session.get("Squirrel::user_name")
        _Logedinpassword = session.get("Squirrel::password")
        with engine.begin() as conn:
            command = sqla.text("Select user_name, password from user where user_name = :User_name and password = :Password")
            result = conn.execute(command, {"User_name": _Logedinusername, "Password": _Logedinpassword})
            if result.rowcount != 0:
                PostedUserId = name
        
        if PostedUserId is not None:
            _to = form_private_message.to.data
            _from = PostedUserId
            message = form_private_message.message.data
            AddPost = sqla.text("INSERT INTO messages (_TO, _FROM, message) value(:to, :from, :message)")

            try:
                with engine.begin() as conn:
                    conn.execute(AddPost, {"to": _to, "from": _from, "message": message})
                    conn.commit()
            except Exception as e:
                print(e)

    #Prepair Basic Info of User
    with engine.begin() as conn:

        Profile_Info_Sql_Command = sqla.text("SELECT * FROM USER WHERE user_name = :user_name")
        Profile_Info = conn.execute(Profile_Info_Sql_Command, {"user_name": name})

        Get_User_Posts_Sql_Command = sqla.text("SELECT * FROM post where postUserId = :user_name")   
        Get_User_Posts = conn.execute(Get_User_Posts_Sql_Command, {"user_name": name}) 

        if Profile_Info.rowcount == 0: #No user for given name exists
            return render_template('404errorpage.html')

        if Get_User_Posts.rowcount == 0:
            Get_User_Posts = None
        
        # Get_User_Posts["PostId", "postUserId", "postTitle", "postContent", "likes"]
        Profile_Info = next(Profile_Info) # ["username", "name", "password", "avatar", "type", "total_followers", "total_following", "total_likes"]

        #User Info  that is of <user_name>
        Name = Profile_Info[1]
        avatar = base64.b64encode(Profile_Info[3]).decode("utf-8")
        _type = Profile_Info[4]
        total_followers = Profile_Info[5]
        total_following = Profile_Info[6]
        total_likes = Profile_Info[7]


    #Authenticate

    _LogedIn_UserName = session.get("Squirrel::user_name")
    _LogedIn_Password = session.get("Squirrel::password")
    if _LogedIn_UserName == name and _LogedIn_Password == Profile_Info[2]:
        #A_L = 1
        #Allow Funcationality only if A_L = 1 
        #Get Private Message List
        Get_Private_Message = None
        with engine.begin() as conn:
            Get_Private_Message_Command = sqla.text("SELECT _TO, _FROM, message FROM MESSAGES  WHERE _To = :user_name OR _FROM = :user_name")
            Get_Private_Message = conn.execute(Get_Private_Message_Command, {"user_name": name})
            
            if Get_Private_Message.rowcount == 0:
                Get_Private_Message = None
            

        return render_template("dashboard.html", name=Name, user_name= name, avatar= avatar, _type = _type, post=Get_User_Posts,\
                            form=form, messagerform = form_private_message, message_list=Get_Private_Message, total_likes= total_likes,\
                                total_following=total_following, total_followers=total_followers)
    else:
        #Requests profile info for A_L = 0
        #Get info about loged in user
        Profile_Info_Of_LogedIn_User = None
        if _LogedIn_UserName is not None:
            with engine.begin() as conn:
                Profile_Info_Of_LogedIn_User_Sql_Command = sqla.text("SELECT user_name, name, avatar, type FROM USER WHERE user_name = :user_name")
                Profile_Info_Of_LogedIn_User = conn.execute(Profile_Info_Of_LogedIn_User_Sql_Command, {"user_name": _LogedIn_UserName})
            
            if Profile_Info_Of_LogedIn_User.rowcount != 0:
                Profile_Info_Of_LogedIn_User = list(next(Profile_Info_Of_LogedIn_User))
                Profile_Info_Of_LogedIn_User[2] = base64.b64encode(Profile_Info_Of_LogedIn_User[2]).decode("utf-8")
        #A_L = 0
        return render_template("notlogindashboard.html", user_name= name, avatar= avatar, _type = _type, post=Get_User_Posts,\
                            total_likes= total_likes, total_following=total_following, total_followers=total_followers, UserName=Profile_Info_Of_LogedIn_User)
    
    

@app.route("/user/<user_name>/post/<postID>", methods=["Post", "get"])
def Post(user_name, postID):
    if request.method == "POST":
        action = request.form.get
        if action('CommentContents'):
            _user_ID = user_name
            _post_ID = postID
            _commented_by = session.get("Squirrel::user_name")
            if _commented_by is not None:
                with engine.begin() as conn:
                    insertintocomments = sqla.text("Insert into comments (userId, postId, commentedBy, commentcontent) values (:userid, :postid, :commentedby, :commentcontent)")
                    conn.execute(insertintocomments, {"userid": _user_ID, "postid": _post_ID, "commentedby": _commented_by, "commentcontent": action('CommentContents')})
                    conn.commit()
        if action("Like"):
            _POSTID = action("Like").split("@")[0]
            _OriginalPostBy = action("Like").split("@")[1]
            _Logedinusername = session.get("Squirrel::user_name")
            _Logedinpassword = session.get("Squirrel::password")
            print(_POSTID, _Logedinusername)
            if _Logedinusername is None or _Logedinpassword is None:
                return redirect(url_for("index"))

            with engine.begin() as conn:
                #check if user name and passwords are correct
                command = sqla.text("Select count(user_name) from user where user_name= :user_name and password = :password")
                AuthenticateUser = conn.execute(command, {"user_name": _Logedinusername, "password": _Logedinpassword})
                if AuthenticateUser.rowcount == 1:
                    _check_if_like_exists = sqla.text("select  likeid from likes where postid = :post and userid = :userid and PostedUserId = :Posteduser")
                    _check_if_like_exists = conn.execute(_check_if_like_exists, {"post" : _POSTID, "userid": _Logedinusername, "Posteduser": _OriginalPostBy})
                    if _check_if_like_exists.rowcount == 0:
                        _update_likes_command = sqla.text("insert into likes (userid , postid, PostedUserId) values (:userid, :postid, :PostedUserId)")
                        
                        conn.execute(_update_likes_command, {"userid": _Logedinusername, "postid": _POSTID, "PostedUserId": _OriginalPostBy})
                        command = sqla.text("update post set likes = likes + 1 where postid = :postid")
                        conn.execute(command, {"postid": _POSTID})
                        conn.commit()

    #At A_L = 0 Post and comments should be visible
    with engine.begin() as conn:
        Post_Command = sqla.text("Select * from post where postid= :postid") 
        comment_Commands = sqla.text("Select * from comments where postid= :postid") 
        Post = conn.execute(Post_Command, {"postid": postID})
        Commetns = conn.execute(comment_Commands, {"postid": postID})
    # Check if username and postID exists
    if Post.rowcount == 0:
        return render_template('404errorpage.html')
    #check if post exists or not
    else:
        UserName = None
        _Logedinusername = session.get("Squirrel::user_name")
        _Logedinpassword = session.get("Squirrel::password")
        if _Logedinusername is not None:
            #check if user exists
            with engine.begin() as conn:
                get_user = conn.execute(sqla.text("Select user_name, avatar, type from user where user_name = :username and password = :password"), {"username": _Logedinusername, "password": _Logedinpassword})
                if get_user.rowcount != 0:
                    UserName = next(get_user)
            
        user_name = UserName[0] if user_name is not None else None
        UserAvatar = base64.b64encode(UserName[1]).decode("utf-8") if user_name is not None else "default" 
        UserAvatarType = UserName[2] if user_name is not None else "txt"
        POST = next(Post)
        post_title = POST[2]
        post_content = POST[3]
        likes = POST[4]
        return render_template("posts.html", postid = postID,user_name=user_name,post_title=post_title, post_content= post_content,\
                                       likes= likes, comments= Commetns, UserName = UserName, avatar= UserAvatar, UserAvatarType=UserAvatarType)
    



if __name__ == "__main__":
    app.run(debug=True)
