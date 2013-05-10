"""This file allows to process the uploading of mantid scripts inside 
the ScriptRepository system. In order to submit a file, it is necessary
to fill up a form with the following fields:
  - author: Name of the author of the file. 
  - email: Email of the author.
  - comment: a description of the file or updates it is being done. 
  - file: The file itself. 
  - path: The folder where the file must be inserted. 

The upload_mantid_scripts will receive the file and the information given
and will insert the file inside the repository and will commit it and them 
push it to the central repository: 
  - git add <file>
  - git commit -m "<comment>" --author "<author> <<email>>" 
  - git push

You can try it through the upload_form.html inside this folder.

It will return a dictionary with the following keys: 
  - message: report on the status of the action
  - detail: details on failures [optional]

"""
from mod_python import psp, apache
import re
import commands
import sys
import json
import os
import time

class GitExceptions(Exception):
  def __init__(self, value, cmd):
    self.value = value
    self.cmd = cmd
  def __str__(self):
    return repr(self.value)

def __shell_execute(cmd ):
   output = commands.getstatusoutput(cmd)
   if (output[0]!=0):
     raise GitExceptions(str(output[1]),cmd)

def publish_debug(req, author="", mail="", comment="", path="", file=""):
  return publish(req, author=author, mail=mail, comment=comment, path=path, file=file, repo="sandbox")

def publish(req, author="", mail="", comment="", path="", file="", repo = ""):
  info = dict()
  current_dir = os.getcwd()
  try:
    os.environ["GIT_COMMITTER_NAME"] = "mantid-publisher"

    if repo == "sandbox":
      REPOSITORYPATH = req.subprocess_env['SANDBOXREPOSITORYPATH']
    else:
      REPOSITORYPATH = req.subprocess_env['SCRIPTREPOSITORYPATH']    

    #process author    
    if not author: raise RuntimeError("Invalid author: "+ author)
    
    #process email
    if not re.match(r'[^@]+@[^@]+\.[^@]+',mail): raise RuntimeError("Invalid email: "+mail)
    
    #process comment
    if not comment: raise RuntimeError("Invalid comment: " + comment)

    #process hidden path
    folder = path
    if './' not in folder : 
      raise RuntimeError("You have not provided a valid folder. You must always start with a './' as the folder")
    if '../' in folder:
      raise RuntimeError("Warning we do not allow ../ at the folder definition. And it must always begin with ./")

    fileitem = file
    
    #check that file is not bigger than 1MB
    if len(fileitem.value)>1048576:
        raise RuntimeError("""Files larger than 1MB cannot be published through this interface. This is to prevent the repository from growing too fast. If you require this file to be published please contact the development team at mantid-help@mantidproject.org""")

    try: # Windows needs stdio set for binary mode.
      import msvcrt
      msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
      msvcrt.setmode (1, os.O_BINARY) # stdout = 1
    except ImportError:
      pass
  
    # strip leading path from file name to avoid directory traversal attacks
    fname = os.path.basename(fileitem.filename)

    # build absolute path to files directory  
    dir_path = os.path.join(REPOSITORYPATH,folder)
    file_path = os.path.join(dir_path,fname)

    try:
      if not os.path.isdir(dir_path):
        if (os.path.exists(dir_path)):# you can not transform a file in a folder
          raise apache.SERVER_RETURN, apache.HTTP_UNAUTHORIZED
        os.makedirs(dir_path)
      
      open(file_path, 'wb').write(fileitem.file.read())
    except: # failed to create the file
      raise RuntimeError('Failed to create the file path : '+ file_path)

    # prepare the git command
    # change the current directory to REPOSITORYPATH
    os.chdir(REPOSITORYPATH)
    relative_path = os.path.relpath(file_path, REPOSITORYPATH)
    
    __shell_execute("""git add "%s" """ %(relative_path))

    __shell_execute("""git commit -m '%s' --author "%s" """%(comment, author + " <" + mail+">"))

    __shell_execute("""git pull --rebase""")

    __shell_execute("git push")
    timeformat="%Y-%b-%d %H:%M:%S"
    stat = os.stat(relative_path)
    pub_date = time.strftime(timeformat,time.gmtime(int(stat.st_mtime + 120)))#add 2minutes
    info['pub_date'] = pub_date
    info['message'] = 'success'
    req.status = apache.OK
  except RuntimeError, ex:
    info['message'] = str(ex)
    req.status = apache.HTTP_BAD_REQUEST
  except KeyError, ex:
    info['message'] = """Internal Error: the repository path is not configured. Variable %s not found!""" %(str(ex))
    req.status = apache.HTTP_INTERNAL_SERVER_ERROR
  except GitExceptions, ex:
    info['shell'] = ex.cmd
    info['detail'] = str(ex)
    if ('nothing added to commit' in str(ex) or
       'nothing to commit' in str(ex)):
      info['message'] = "success"
    else:
      info['message'] = "Failed to Upload.\n You may turn on the information level of logging and try again to see why it failed." 
    #recover the status
    __shell_execute("git reset --hard origin/master")
  except :
    info['message'] = str(sys.exc_info())
    req.status = apache.HTTP_INTERNAL_SERVER_ERROR
  os.chdir(current_dir)
  message = json.dumps(info, sort_keys=True, indent=2, separators=(',', ': '))
  req.content_type = 'application/json'
  req.write(message)
