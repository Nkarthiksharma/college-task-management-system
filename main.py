import pymysql
from flask import Flask,render_template,redirect
from flask_wtf import FlaskForm
from datetime import timedelta
from flask import send_from_directory

from wtforms.validators import DataRequired,Email,Length
from flask import session,request,jsonify
from flask_ckeditor import CKEditor,CKEditorField
from wtforms import StringField , SubmitField,EmailField,PasswordField,DateField,SelectMultipleField
from flask_wtf.file import MultipleFileField,FileAllowed
from datetime import date
import os
from werkzeug.utils import secure_filename
import time
from flask_mail import Mail,Message
app=Flask(__name__)
app.permanent_session_lifetime = timedelta(days=7)
app.config['SECRET_KEY']="My secret key"
app.config["UPLOAD_FOLDER"]="uploads"
app.config["MAIL_SERVER"]="smtp.gmail.com"
app.config["MAIL_PORT"]=587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "karthikkvk292@gmail.com"
app.config["MAIL_PASSWORD"] = "gbbcbedcioglrvbe"
app.config["MAIL_DEFAULT_SENDER"] = "karthikkvk292@gmail.com"
mail=Mail(app)

ckeditor=CKEditor(app)
conn=pymysql.connect(host="localhost",user="root",password="12345678",database="collegeproject")
cursor=conn.cursor()
class login(FlaskForm):
    email=EmailField('Email Address',validators=[DataRequired(message="Enter Email"),Email("Enter valid Email")])
    password=PasswordField('Enter Password',validators=[DataRequired(message="Enter valid Password ")])
    submit=SubmitField('Sign Up')

class createTaskForm(FlaskForm):
    taskName=StringField('Task Name',validators=[DataRequired(message="Enter Task Name")])
    details=CKEditorField('Description',validators=[DataRequired(message="Enter Description")])
    attachment = MultipleFileField(
        "Attachment",
        validators=[
            FileAllowed(
                ["pdf", "doc", "docx", "xls", "xlsx","txt"],
                "Only Text,PDF, Word, and Excel files are allowed."
            )
        ]
    )
    updateOn=DateField('Report On',validators=[DataRequired()])
    dueDate=DateField('Due Date',validators=[DataRequired()])
    faculty=SelectMultipleField("Faculty",coerce=int)

    submit=SubmitField('Add')

@app.route('/',methods=['GET','POST'])
def helloworld():
    loginform=login()
    if loginform.validate_on_submit():
        email=loginform.email.data
        password=loginform.password.data
        cursor.execute("select * from faculty where mail=%s",(email,))
        details=cursor.fetchone()
        if details==None:
            return render_template("login.html", form=loginform, password="false")
        if details:
            orginalpassword=details[5]
            if orginalpassword!=password:
                form=None
                print("orginalpassword",orginalpassword)
                print("password",password)
                return render_template("login.html", form=loginform,password="false")
            else:
                id=details[0]
                name=details[1]
                dept=details[2]
                desig=details[3]
                power=details[6]
                session["power"]=power
                session["loggedin"] = 0
                if power==2:
                    session["loggedin"]=1
                    return redirect("/Principal")
                elif power==1:
                    session["dept"]=dept
                    session["id"] = id
                    session["loggedin"] = 1
                    return redirect("/HOD")
                elif power==0:
                    session["id"] = id
                    session["loggedin"] = 1
                    return redirect("/myTasks")



    return render_template("login.html",form=loginform,password="notyet")



@app.route('/seggregate',methods=['GET','POST'])
def seggregate():
    if session.get("loggedin")==0 or session.get("power")==0 or session.get("loggedin") == None or session.get("power")==None:
        return redirect("/")
    data=request.get_json()
    dept=data["dept"].lower()
    status = int(data["status"])
    tasks = []
    nooftasks=()
    if dept!="all":
        cursor.execute("select * from taskmanagements tm join faculty f on f.id=tm.facultyid  where f.dept=%s", (dept,))
        total_no_of_tasks = cursor.fetchall()
        number_of_tasks_assigned = len(total_no_of_tasks)
        cursor.execute("select * from taskmanagements tm join faculty f on f.id=tm.facultyid   where tm.status=%s and f.dept=%s", (0, dept))
        ongoing_tasks = cursor.fetchall()
        no_of_assigned_ongoing_tasks = len(ongoing_tasks)
        no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
        nooftasks = (number_of_tasks_assigned, no_of_assigned_ongoing_tasks, no_of_assigned_completed_tasks)
    if dept=="all":
        cursor.execute("select * from taskmanagements " )
        total_no_of_tasks = cursor.fetchall()
        number_of_tasks_assigned = len(total_no_of_tasks)
        cursor.execute("select * from taskmanagements where status=%s ", (0, ))
        ongoing_tasks = cursor.fetchall()
        no_of_assigned_ongoing_tasks = len(ongoing_tasks)
        no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
        nooftasks=(number_of_tasks_assigned, no_of_assigned_ongoing_tasks, no_of_assigned_completed_tasks)
        if status==2:
            cursor.execute("""SELECT t.id,
                                     t.name,
                                     f.id
                                         AS
                                         faculty_id,
                                     f.name
                                         AS
                                         faculty_name,
                                     f.dept,
                                     t.createdon,
                                     t.updateon,
                                     tm.status,
                             t.duedate,
                             t.createdby,
                             tm.textinfo
  

                              FROM tasks t
                                       JOIN
                                   taskmanagements tm
                                   ON
                                       t.id = tm.taskid
                                       JOIN
                                   faculty f
                                   ON
                                       tm.facultyid = f.id
                              
                           """)
            tasks = cursor.fetchall()
        else:
          cursor.execute("""SELECT t.id,
                                 t.name,
                                 f.id
                                     AS
                                     faculty_id,
                                 f.name
                                     AS
                                     faculty_name,
                                 f.dept,
                                 t.createdon,
                                 t.updateon,
                                 tm.status,
                             t.duedate,
                             t.createdby,
                             tm.textinfo


                          FROM tasks t
                                   JOIN
                               taskmanagements tm
                               ON
                                   t.id = tm.taskid
                                   JOIN
                               faculty f
                               ON
                                   tm.facultyid = f.id
                              where tm.status = %s
                       """, (status,))
          tasks = cursor.fetchall()

    elif(status==1 or status==0):

     cursor.execute("""SELECT t.id,
                             t.name,
                             f.id
                                 AS
                                 faculty_id,
                             f.name
                                 AS
                                 faculty_name,
                             f.dept,
                             t.createdon,
                             t.updateon,
                             tm.status,
                             t.duedate,
                             t.createdby,
                             tm.textinfo


                      FROM tasks t
                               JOIN
                           taskmanagements tm
                           ON
                               t.id = tm.taskid
                               JOIN
                           faculty f
                           ON
                               tm.facultyid = f.id
                        where tm.status = %s and f.dept = %s
                   """, (status, dept))
     tasks = cursor.fetchall()
    elif status==2:
        cursor.execute("""SELECT t.id,
                                 t.name,
                                 f.id
                                     AS
                                     faculty_id,
                                 f.name
                                     AS
                                     faculty_name,
                                 f.dept,
                                 t.createdon,
                                 t.updateon,
                                 tm.status,
                             t.duedate,
                             t.createdby,
                             tm.textinfo
                        


                          FROM tasks t
                                   JOIN
                               taskmanagements tm
                               ON
                                   t.id = tm.taskid
                                   JOIN
                               faculty f
                               ON
                                   tm.facultyid = f.id
                          where f.dept = %s
                       """, (dept,))
        tasks = cursor.fetchall()

    for task in tasks:
        print(task[0],task[1],task[2],task[3],task[4],task[5],task[6],task[7],task[8],task[9],task[10])
    return jsonify({"tasks":tasks,"count":nooftasks})


@app.route('/Principal')
def Principal():
    if session.get("loggedin") == 0 or session.get("power") !=2 or session.get("loggedin") == None or session.get("power")==0:
        return redirect("/")
    session["created"]="False"
    print(session.get("created"))
    cursor.execute("select * from taskmanagements")
    total_no_of_tasks=cursor.fetchall()
    number_of_tasks_assigned=len( total_no_of_tasks)
    cursor.execute("select * from taskmanagements where status=%s",(0,))
    ongoing_tasks=cursor.fetchall()
    no_of_assigned_ongoing_tasks=len(ongoing_tasks)
    no_of_assigned_completed_tasks=number_of_tasks_assigned-no_of_assigned_ongoing_tasks
    cursor.execute("""SELECT
    t.id,
    t.name,
    f.id
    AS
    faculty_id,
    f.name
    AS
    faculty_name,
    f.dept,
        t.createdon,
    t.updateon,
    tm.status,
    t.duedate,
    t.createdby,
    tm.textinfo

FROM
tasks
t
JOIN
taskmanagements
tm
ON
t.id = tm.taskid
JOIN
faculty
f
ON
tm.facultyid = f.id 
                   """)
    tasks=cursor.fetchall()
    return render_template("Principal.html",power=2,total_tasks=tasks,assigned=number_of_tasks_assigned,ongoing=no_of_assigned_ongoing_tasks,completed=no_of_assigned_completed_tasks)
@app.route('/HOD',methods=['GET','POST'])
def hod():
    if session.get("loggedin") == 0 or session.get("power") !=1 or session.get("loggedin") == None or session.get("power")==0:
        return redirect("/")
    session["created"]="False"
    dept=session.get("dept").upper()
    cursor.execute("select * from taskmanagements t join faculty f on t.facultyid=f.id where f.dept= %s",(dept,))
    total_no_of_tasks = cursor.fetchall()
    number_of_tasks_assigned = len(total_no_of_tasks)
    cursor.execute("select * from taskmanagements t join faculty f on t.facultyid=f.id where f.dept=%s and status=%s", (dept,0,))
    ongoing_tasks = cursor.fetchall()
    no_of_assigned_ongoing_tasks = len(ongoing_tasks)
    no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
    cursor.execute("""SELECT t.id,
                             t.name,
                             f.id
                                 AS
                                 faculty_id,
                             f.name
                                 AS
                                 faculty_name,
                             f.dept,
                             t.createdon,
                             t.updateon,
                             tm.status,
                             t.duedate,
                             t.createdby,
                            
                             
                              tm.textinfo
                              

                      FROM tasks t
                               JOIN
                           taskmanagements tm
                           ON
                               t.id = tm.taskid
                               JOIN
                           faculty f
                           ON
                               tm.facultyid = f.id  where  f.dept=%s
                   """, (dept,))
    tasks = cursor.fetchall()
    for task in tasks:
        print(task[0],task[1],task[2],task[3],task[4],task[5],task[6],task[7],task[8],task[9],)
    return render_template("Principal.html", power=1,dept=dept.lower(), total_tasks=tasks, assigned=number_of_tasks_assigned,
                           ongoing=no_of_assigned_ongoing_tasks, completed=no_of_assigned_completed_tasks)

@app.route("/createtask",methods=['GET','POST'])
def createTask():
    if session.get("loggedin") == 0 or session.get("power") ==0 or session.get("loggedin") == None or session.get("power")==0:
        return redirect("/")
    if session.get("created") == "True":
        taskForm = createTaskForm()

        return render_template("Create.html", form=taskForm, created=True, name=session.get("taskName"))
    taskForm=createTaskForm()
    if session.get("power")==2:
     cursor.execute("select id,name,desig,dept,mail from faculty where power!=%s",(2,))
    elif session.get("power")==1:
        cursor.execute("select id,name,desig,dept,mail from faculty where dept=%s and power=%s",(session.get("dept"),0))
    rows=cursor.fetchall()
    taskForm.faculty.choices=[
        (row[0], f"ID: {row[0]} {row[1]}  {row[2]}  {row[3]}") for row in rows
    ]

    if taskForm.validate_on_submit():

        taskName=taskForm.taskName.data
        attachments=taskForm.attachment.data


        details = taskForm.details.data
        updateOn = taskForm.updateOn.data
        dueDate = taskForm.dueDate.data
        facultyIdList = taskForm.faculty.data
        createdBy=None
        if(session.get("power")==1):
            if session.get("dept")=="CSE":
             createdBy="CSEHOD"
            elif session.get("dept") == "CSM":
                createdBy = "CSMHOD"
            elif session.get("dept") == "ECE":
                createdBy = "ECEHOD"
            elif session.get("dept") == "EEE":
                createdBy = "EEEHOD"
        elif (session.get("power")==2):
            createdBy="Principal"
        print(taskName,details,updateOn, dueDate ,facultyIdList[0],createdBy)


        today=date.today()
        cursor.execute("insert into tasks( name, details ,updateon,duedate, createdby,createdon) values(%s,%s,%s,%s,%s,%s)",
                       (taskName, details, updateOn, dueDate, createdBy, today))
        taskId = cursor.lastrowid
        if attachments:
          for file in attachments:
            if file.filename!=None:
                original_name=secure_filename(file.filename)
                stored_name = str(int(time.time() * 1000)) + "_" + original_name
                file.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        stored_name
                    )
                )
                cursor.execute(
          """
                INSERT INTO attachments(taskid, orginalname, storedname)
                VALUES (%s, %s, %s)
                """,
           (
                taskId,
                original_name,
                stored_name
                )
                )
        mailrows=[]
        for id in facultyIdList:
               cursor.execute("insert into taskmanagements(taskid,facultyid,status,textinfo) values (%s,%s,%s,%s)",
                              (taskId,id,0,""))
               cursor.execute("select mail from faculty where id=%s",(id,))
               rows=cursor.fetchone()
               mailrows.append(rows[0])



        session["created"]="True"
        session["taskName"]=taskName
        for mails in mailrows:
           msg=Message(
               subject="A New Task Created",
               recipients=[mails]
           )
           if session.get("power")==2:
             msg.body=f"Complete the Task {taskName} ASAP\nRegards Principal"
           elif session.get("power")==1:
               msg.body = f"Complete the Task {taskName} ASAP\nRegards Head Of the Department"
           try:
             mail.send(msg)
             print("Email sent")
           except Exception as e:
               print("Error")
        conn.commit()
        return render_template("Create.html", form=taskForm,created=True,name=taskName)

    return render_template("Create.html",form=taskForm,created=False,name="")
@app.route("/myTasks",methods=["GET","POST"])
def myTasks():
    if session.get("loggedin") == 0 or session.get("loggedin") == None :
        return redirect("/")
    name=None
    dept=None
    id=None
    cursor.execute("select id,name,dept from faculty where id =%s",(session.get("id"),))
    facultyrow=cursor.fetchone()

    name=facultyrow[1]
    dept=facultyrow[2]
    id=facultyrow[0]
    cursor.execute("select taskid from taskmanagements where facultyid=%s",(session.get("id"),))
    taskidlist=cursor.fetchall()
    taskList=[]
    for row in taskidlist:
        taskid=row[0]
        t=[]
        cursor.execute("select * from tasks where id=%s",(taskid,))
        onetask=cursor.fetchone()
        if not onetask:
            continue
        t.append(onetask[0])
        t.append(onetask[1])
        t.append(onetask[2])
        t.append(onetask[6])
        t.append(onetask[3])
        t.append(onetask[4])
        t.append(onetask[5])
        cursor.execute("select status,textinfo from taskmanagements where taskid=%s and facultyid=%s",(taskid,id))
        status_textinfo=cursor.fetchone()
        status=status_textinfo[0]
        textinfo=status_textinfo[1]
        t.append(status)
        t.append(textinfo)
        cursor.execute(
            "SELECT orginalname, storedname FROM attachments WHERE taskid=%s",
            (taskid,)
        )
        attachments = cursor.fetchall()

        t.append(attachments)
        taskList.append(t)
    return render_template("myTasks.html",taskList=taskList,myid=id,myname=name,mydept=dept)
@app.route("/updateTask",methods=["GET","POST"])
def updateTask():
    if session.get("loggedin") == 0 :
        return redirect("/")
    facultyId=int(session.get("id"))
    taskid=int(request.form.get("taskid"))
    status=int(request.form.get("status"))
    textinfo=request.form.get("textinfo")
    cursor.execute("update taskmanagements set status=%s ,textinfo=%s  where taskid =%s and facultyid=%s",(status,textinfo,taskid,facultyId))

    conn.commit()

    return redirect("/myTasks")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/createdTasks",methods=["GET","POST"])
def createdTasks():
    if session.get("loggedin") == 0 or session.get("power") ==0 or session.get("loggedin") == None or session.get("power")==0:
        return redirect("/")
    if session.get("power")==2:
      session["taskId"]=None
      cursor.execute("select * from tasks where createdby=%s",("Principal",))
      rows=cursor.fetchall()
      return render_template("createdTasks.html",rows=rows)
    elif session.get("power")==1:
        session["taskId"] = None
        if session.get("dept")=="CSE":
         cursor.execute("select * from tasks where createdby=%s  ", ("CSEHOD",))
        elif session.get("dept")=="CSM":
         cursor.execute("select * from tasks where createdby=%s  ", ("CSMHOD",))
        elif session.get("dept")=="ECE":
         cursor.execute("select * from tasks where createdby=%s  ", ("ECEHOD",))
        elif session.get("dept")=="EEE":
         cursor.execute("select * from tasks where createdby=%s  ", ("EEEHOD",))
        rows = cursor.fetchall()
        return render_template("createdTasks.html", rows=rows)
@app.route("/updateTaskByAuthor",methods=["GET","POST"])
def updateTaskByAuthor():
    if session.get("loggedin") == 0 or session.get("power") ==0 or session.get("loggedin") == None or session.get("power")==0:
        return redirect("/")
    if request.method=="POST":
       id=int(request.form.get("id"))
       session["taskId"]=id
    id=session.get("taskId")
    cursor.execute("select id,name,details,createdon,updateon,duedate from tasks where id=%s",(id,))
    taskDetails=cursor.fetchall()


    cursor.execute("select f.id,f.name,f.dept,t.status,t.textinfo,t.id from taskmanagements t join faculty f on f.id=t.facultyid where t.taskid=%s",(id,))
    facultyDetails=cursor.fetchall()
    for faculty in facultyDetails:
        print(faculty[0],faculty[1],faculty[2],faculty[3],faculty[4])
    cursor.execute(
        "SELECT orginalname,storedname,id FROM attachments WHERE taskid=%s",
        (id,)
    )
    attachments = cursor.fetchall()
    if session.get("power")==2:
     cursor.execute("select id,name,desig,dept,mail from faculty where power!=%s",(2,))
    elif session.get("power")==1:
        cursor.execute("select id,name,desig,dept,mail from faculty where dept=%s and power=%s",(session.get("dept"),0))
    rows=cursor.fetchall()
    faculty_choices=[
        (row[0], f"ID: {row[0]} {row[1]}  {row[2]}  {row[3]}") for row in rows
    ]
    return render_template("updateTaskByAuthor.html",taskDetails=taskDetails,facultyDetails=facultyDetails,attachments=attachments,faculty_choices=faculty_choices)
@app.route("/updateCreatedTask",methods=["GET","POST"])
def updateCreatedTasks():
    itis=request.form.get("itis")
    if itis =="TextArea":

           details=request.form.get("otherinfo")

           taskId=int(request.form.get("id"))
           cursor.execute("update tasks set details = %s where id=%s",(details,taskId))
           cursor.execute("select details from tasks where id=%s",(taskId,))
           taskDetails=cursor.fetchone()
           print(taskDetails[0])
    elif itis == "ReportDate":
              reportDate=request.form.get("reportDate")
              taskId = int(request.form.get("id"))
              cursor.execute("update tasks set updateon = %s where id=%s", (reportDate, taskId))

              cursor.execute("select updateon from tasks where id=%s", (taskId,))
              taskDetails = cursor.fetchone()
              print(taskDetails[0])
    elif itis == "DueDate":
        dueDate = request.form.get("dueDate")
        taskId = int(request.form.get("id"))
        cursor.execute("update tasks set duedate = %s where id=%s", (dueDate, taskId))

        cursor.execute("select duedate from tasks where id=%s", (taskId,))
        taskDetails = cursor.fetchone()
        print(taskDetails[0])
    elif itis == "SubmitFiles":
        files = request.files.getlist("files")
        taskId =session.get("taskId")
        for file in files:
            if file.filename != None:
                original_name = secure_filename(file.filename)
                stored_name = str(int(time.time() * 1000)) + "_" + original_name
                file.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        stored_name
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO attachments(taskid, orginalname, storedname)
                    VALUES (%s, %s, %s)
                    """,
                    (
                         taskId,
                        original_name,
                        stored_name
                    )
                 )
                print("HI")
    elif itis == "RemoveFaculty":
        removeId=int(request.form.get("taskmanagementsId"))
        print("Faculty deleted")
        cursor.execute("delete from taskmanagements where id=%s", (removeId,))
        print("Faculty deleted")
    elif itis == "addFaculties":
        print("Adding Faculty")
        taskId = session.get("taskId")
        facultyIdList=request.form.getlist("faculty")
        cursor.execute("select name from tasks where id=%s",(taskId,))
        row=cursor.fetchone()
        mailrows = []
        for id in facultyIdList:
            print(id)
            cursor.execute("insert into taskmanagements(taskid,facultyid,status,textinfo) values (%s,%s,%s,%s)",
                           (taskId, id, 0, ""))
            cursor.execute("select mail from faculty where id=%s", (id,))
            rows = cursor.fetchone()
            mailrows.append(rows[0])

        taskName=row[0]
        for mails in mailrows:
            msg = Message(
                subject="A New Task Created",
                recipients=[mails]
            )
            if session.get("power") == 2:
                msg.body = f"Complete the Task {taskName} ASAP\nRegards Principal"
            elif session.get("power") == 1:
                msg.body = f"Complete the Task {taskName} ASAP\nRegards Head Of the Department"
            try:
                mail.send(msg)
                print("Email sent")
            except Exception as e:
                print("Error")
                conn.rollback()
                return "Error"
    conn.commit()
    return redirect("/updateTaskByAuthor")
@app.route("/deleteFile")
def deleteFile():

    fileid = request.args.get("fileid")


    print(fileid)

    # Delete the file using fileid
    cursor.execute("DELETE FROM attachments WHERE id=%s", (fileid,))
    conn.commit()

    # Redirect back to the task details page
    return redirect("/updateTaskByAuthor")




if __name__=='__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)
