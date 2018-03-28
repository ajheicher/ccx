import argparse
import xml.etree.ElementTree as ET
import requests
from contextlib import contextmanager
import sys
import time

@contextmanager
#this is the exception handling for all web requests made out of this application
def requestHandler():
    try:
        yield
    except requests.exceptions.HTTPError as eh:
        print(eh)
        print("The error above should give you a good idea what happened")
        
    except requests.exceptions.Timeout as et:
        print(et)
        print("Probably check your internet connection")
       
    except requests.exceptions.TooManyRedirects as er:
        print(er)
        print("Check the URL, it probably has a weird typo or is pointing to the wrong place")
        
    except requests.exceptions.RequestException as e:
        print(e)
        print("This is real bad, I don't know what happened here")
        
    #finally:
        #common exception handling here (probably make a logger?)
        
        
    
parser = argparse.ArgumentParser(description='Script to log agents out of Finesse')
parser.add_argument('-m','--mode',type=str,choices=['user','dialog','queue','team','clientlog','digest'],default='digest',help="Program Run Mode")
parser.add_argument('-u','--username', type=str, nargs='+', help="Optional. Include this arguement to force log out a user or list of users")
parser.add_argument('-f','--fqdn', type=str, default="https://uccxpub01.philorch.org:8445", help="Fully Qualified Domain Name of Finesse Instance")
parser.add_argument('-c','--credentials', type=str, nargs=2, help="Login credentials (username password) for a CCX Administrator Account")

args = parser.parse_args()

fqdn = args.fqdn
adminUsername = args.credentials[0]
adminPassword = args.credentials[1]
mode = args.mode
#desktopActionTypes = ['user','dialog','queue','team','clientlog']
#configActionTypes = ['system','cluster','entData','layout','reasonCode','wrapUp','mediaProp','phoneBook','contact','workflow','team']
#servActionTypes = ['system','diag',]

usernames = args.username
loggedInUsers = []


def getAllLoggedInUsers():
    
    #context managers are my shit
    with requestHandler():
        r = requests.get(fqdn + "/finesse/api/Users", auth=(adminUsername,adminPassword))
        #raises an exception if we get an errant HTTP error code
        r.raise_for_status()
    
    #create XML tree
    tree = ET.fromstring(r.content)
    
    #create a parent mapping dictionary
    parent_map = dict((c, p) for p in tree.getiterator() for c in p)
    
    talkingCount = 0
    userCount = 0
    #iterate through the tree and look for all the logged in users
    for child in tree:
        for subchild in [x for x in child if x.tag=="state" and x.text!="LOGOUT"]:
            parent = parent_map[subchild]
            userCount += 1
            if(parent.find('state').text == "TALKING"):
                talkingCount+=1
            print(parent.find('firstName').text, parent.find('lastName').text, parent.find('state').text)
            loggedInUsers.append(parent.find('loginId').text)
    
    
    print("Talking: {} ({}%)".format(talkingCount, round(talkingCount/userCount*100,2)))
    
    print("Total: ",userCount)
    #return a list of logged in users for other processing
    return loggedInUsers

def getSkills(user):


    with requestHandler():
        r = requests.get(fqdn + "/finesse/api/User/" + user,auth=(adminUsername,adminPassword))
        r.raise_for_status()

        r2 = requests.get(fqdn + "/finesse/api/User/" + user + "/Queues",auth=(adminUsername,adminPassword))
        r2.raise_for_status()
    
    userTree = ET.fromstring(r.content)
    queueTree = ET.fromstring(r2.content)

    print("{} {}".format(userTree.find('firstName').text, userTree.find('lastName').text))
    print("\nSkills:")
    for skill in queueTree:
        print(" {}".format(skill.find("name").text))


def logOutUsers(userList):
    headers = {'content-type': 'application/xml'}
    for user in userList:
        with requestHandler():
            r = requests.put(fqdn + "/finesse/api/User/" + user, data="<User><state>LOGOUT</state></User>", auth=(adminUsername,adminPassword), headers=headers)
            r.raise_for_status()
        
def main():  
    if(mode=='digest'):
        start_time=time.time()
        print(getAllLoggedInUsers())
        #getSkills("aheicher")
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        print("Not built yet")

#look, were all pythonic(tm)
if __name__ == "__main__":
    main()
        





