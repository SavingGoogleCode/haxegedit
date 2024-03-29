import os
import subprocess
import re
import configuration
import string
from xml.dom.minidom import parseString

re_package = re.compile ("package (?P<packagename>(\w+.)*\w+);")

def get_packages (origdoc):
    match = re_package.search (origdoc)
    if match != None:
        return match.group ("packagename")
    else:
        return None


def make_word (abbr, type):
    word = abbr
    if type != "":
        if type.find ('->') != -1:
            # function
            args = type.replace (" ->", ",").replace (" : ", ":")  
            last = args.rfind (",")
            returntype = args[last + 2:]
            args = args[:last]
            word += " (" + args + ") : " + returntype
        else:
            word += " : " + type
    return word


def get_program_output (basedir, classname, fullpath, origdoc, offset, hxmlfile, package):
	#check for utf-8 with written BOM
    if ord(origdoc[0])>256:
        offset=offset+2
    os.rename (fullpath, fullpath + ".bak")
    file = open (fullpath, "w")
    file.write (origdoc.encode('utf-8'))
    file.close ()

    errorInfoPath=""
    
    if hxmlfile != None and hxmlfile != "":
    	cls = classname
        if package != None:
            cls = package+"."+cls
        command = ["haxe", os.path.basename(hxmlfile), cls, "--display", "%s@%d" % (fullpath[len(basedir)+1:], offset)]
        errorInfoPath = hxmlfile + "," + cls
        
    elif os.path.exists (basedir + "/build.hxml"):
        command = ["haxe", basedir + "/build.hxml", classname , "--display", "%s@%d" % (classname.replace (".", "/") + ".hx", offset)] 
        errorInfoPath = basedir + "/build.hxml, " + classname
    
    else:
        command = ["haxe", "-swf-version", "9", "-swf", "/tmp/void.swf", classname, "--display" , "%s@%d" % (classname.replace (".", "/") + ".hx", offset)]
        errorInfoPath = "-swf-version 9 + -swf /tmp/void.swf" + classname

    proc = subprocess.Popen (command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=basedir)
    out = proc.communicate ()
    
    """
    print command
    print "proc.returncode:"
    print proc.returncode
    print "-------------------"
    print "out[0]:"
    print out[0]
    print "-------------------"
    print "out[1]:"
    print out[1]
    print "-------------------"
    """
    
    str = out[1]
    begin = str.find ("<list>")
    if begin != -1:
        str = str[begin:]
    typeList = str.find ("<type>") != -1
        

    already = set () # FIXME : haxe compiler outputs two times package names.
    result = None
    try:
        if proc.returncode == 0:
            xmldom = parseString (str)
            if typeList and not configuration.getTypeOnlyHideComplete():
                list = xmldom.getElementsByTagName ('type')
                result = []
                for item in list:
                    result.append ({"word":item.childNodes[0].nodeValue, "type":item.childNodes[0].nodeValue})
            else:
                list = xmldom.getElementsByTagName ('i')
                result = []
                for item in list:
                    dict = {}
                    val = item.attributes["n"].value
                    if val in already: continue # FIXME
                    dict["abbr"] = val
                    already.add (val) # FIXME
                    dict["type"] = ""
                    try:
                        dict["type"] = item.getElementsByTagName ('t')[0].childNodes[0].nodeValue
                    except Exception, e:
                        pass
                    try:
                        dict["info"] = item.getElementsByTagName ('d')[0].childNodes[0].nodeValue
                    except Exception, e:
                        pass
                    dict["word"] = make_word (dict["abbr"], dict["type"])
                    result.append (dict)
        else:
            result = []
            errorLines = str.split("\n");
            for l in errorLines:
                if l != "":
                    result.append({"word":l, "error":l})
            #result.append({"word":"Error: "+str, "error":str})
            result.append({"word":"Using hxml: "+errorInfoPath, "hxml":errorInfoPath})
              
    except Exception, e:
        result = []
        result.append({"word":"Error: " + e.__str__()})
        result.append({"word":"Using hxml: "+errorInfoPath})

    os.rename (fullpath + ".bak", fullpath)

    return result

def haxe_complete (fileloc, origdoc, offset):
    package = get_packages (origdoc)
    complete_path = fileloc.replace ("file://", "")
    #complete_path = urllib.unquote (fileloc.replace ("file://", ""))
    dirname = os.path.dirname (complete_path)
    filename = os.path.basename (complete_path)
	
    classname = filename[:-3]
    
    hxmlfile = configuration.getHxmlFile()
    if hxmlfile != None and hxmlfile != "":
    	dirname = os.path.dirname(hxmlfile)

    basedir = dirname # by default
    if package != None:
        if dirname.endswith (package.replace (".", "/")):
            basedir = dirname[:-len(package.replace (".", "/"))] 
            classname = package + '.' + classname

    return get_program_output (basedir, classname, complete_path, origdoc, offset, hxmlfile,package)

