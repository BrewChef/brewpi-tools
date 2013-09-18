#!/usr/bin/python
# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi. If not, see <http://www.gnu.org/licenses/>.

### Geo Van O, v0.9, Sep 2013

from subprocess import *
from git import *
from time import strptime

### fixPermissions.sh, Pythonized
def fixPermissions():
	check_call(["sudo", "chown", "-R", "brewpi:brewpi", "/home/brewpi"])
	check_call(["sudo", "find", "/home/brewpi", "-type", "f", "-exec", "chmod",  "g+rwx", "{}", ";"])
	check_call(["sudo", "find", "/home/brewpi", "-type", "d", "-exec", "chmod",  "g+rwxs", "{}", ";"])
	check_call(["sudo", "find", "/var/www", "-type", "f", "-exec", "chmod",  "g+rwx", "{}", ";"])
	check_call(["sudo", "find", "/var/www", "-type", "f", "-exec", "chmod",  "g+rwxs", "{}", ";"])

### Function used if requested branch has not been checked out
def checkout_repo(repo, branch):
	print "Attempting to checkout "+branch
	try:
		repo.git.checkout(branch)
	except GitCommandError, e: 
		print e
		print "Failed. Ack! Quitting"
		sys.exit()
	print "Success!"

### Stash any local repo changes
def stashChanges(repo):
	stashed = False
        print "Attempting to stash any changes..."
        try:
                resp = repo.git.stash()
                print resp
		stashed = True
        except GitCommandError, e:
                print e
                print "Unable to stash, don't want to overwrite your stuff, aborting this branch update"
		sys.exit()
	return stashed

### Function used to stash local changes and update a branch passed to it
def update_repo(repo, branch):
	stashed = False
	repo.git.fetch('origin', branch)
	try:
		print repo.git.merge('origin/'+branch)
	except GitCommandError,e: 
		print e
		if "Your local changes to the following files would be overwritten by merge" in str(e):
			stashed = stashChanges(repo)			
		print "Trying to merge again..."
		try:
			print repo.git.merge('origin/'+branch)
		except GitCommandError,e:
			print e
			print "Sorry, local changes made are too complex. Aborting this branch update"
			return	
	
	if stashed:
		print "##################################################################"
		print "#Your local changes are in conflict with the last update of code.#"
		print "##################################################################"
		print "The conflict is:\n"
		print "-------------------------------------------------------"
		print  repo.git.stash("show", "--full-diff", "stash@{0}")
		print "-------------------------------------------------------"
		print ""
		print  "Your changes are stashed for the moment, but if you don't care about them, I can discard them now. If I don't, you need to resolve this on your own, or you'll have issues updating BrewPi in the future."
		choice = raw_input("Would you like me to discard your local changes causing this conflict? [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			for filename in repo.git.stash("show", "stash@{0}").split("\n")[:-1]:
				repo.git.checkout("--theirs", filename.split("|")[0].strip())
				repo.git.add(filename.split("|")[0].strip())
				print "Discarded changes, merging again, just to be sure..."
				print repo.git.merge('origin/'+branch)
	print branch + " updated!"

### Funtion to be used to check most recent commit date on the repo passed to it
def check_repo(repo):
	changed = False
        branches = repo.git.branch('-r').split('\n')
	branches.remove("  origin/HEAD -> origin/master")
        branches = [x.lstrip(" ").strip("* ").replace("origin/","") for x in branches]
        print "\nAvailable branches in "+str(repo).split("\"")[1]+":"
	for i in enumerate(branches):
		print "[%d] %s" % i
	print "["+str(len(branches))+"] Skip"
	while (1):
		try:
			selection = int(raw_input("Enter the number of the branch you wish to update: "))
		except ValueError:
	    		print "Use the number!"
			continue
		if selection == len(branches):
			return
		try:
			branch = branches[selection]
		except:
			print "Not a valid selection. Try again"
			continue
		break


	### Check if branch is currently active, if not, prompt to check it out
	branches = repo.git.branch()
        for i in branches.split("\n"):
                if "*" in i:
                        curBranch = i
                        break
        if curBranch.strip("* ") != branch:
                choice = raw_input("You chose "+branch+" but it is not your current active branch- would you like me to check it out for you now? (Required to continue) [Y/n]: ")
                if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
                        try:
                                print repo.git.checkout(branch)
                                print "Successfully switched to "+branch
                        except GitCommandError, e:
				if "Your local changes to the following files would be overwritten by checkout" in str(e):
					print "Local changes exist in your current files that need to be stashed" 
					stashed = stashChanges(repo)
                			print "Trying to checkout again..."
                		try:
                        		print repo.git.checkout(branch)
				except GitCommandError, e:
					print e
                                	print "I was unable to checkout. Please try it manually from the command line and re-run this tool"
					return
		else:
			print "Skipping this branch"
			return

	local = repo.git.show(branch).split("\n")[2]
	if ("Date" not in local):
		local = repo.git.show(branch).split("\n")[3]
	remote = repo.git.show('origin/'+branch).split("\n")[2]
	if ("Date" not in remote):
		remote = repo.git.show('origin/'+branch).split("\n")[3]
	reponame = repo.git.remote('-v').split(":")[1].split()[0]
	localdate = strptime(local[8:-6],"%a %b %d %H:%M:%S %Y")
	remotedate = strptime(remote[8:-6],"%a %b %d %H:%M:%S %Y")

	print "\nChecking for updates on "+reponame+", branch "+branch
	print "Your local copy of "+reponame+" is current as of: "+local
	print "The most current version of BrewPi for this branch is "+remote
	if localdate < remotedate:
		print "*** Your local version of "+reponame+" is out of date."
		choice = raw_input("Would you like to update this branch? [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			update_repo(repo, branch)
			changed = True
	else:
		print "Your local version of "+reponame+" is good to go!"
	return changed

print "####################################################"
print "####                                            ####"
print "####      Welcome to the BrewPi Updater!        ####"
print "####                                            ####"
print "####################################################"
print ""
print "Most users will want to select the 'master' choice at each of the following menus."
branch = raw_input("Press enter to continue: ")

changed = False
try:
	changed = check_repo( Repo('/home/brewpi') )
except:
	print "I don't see BrewPi installed to the default path of /home/brewpi "
	choice = raw_input("What path did you install BrewPi to? ")
	try:
		check_repo(Repo(choice))
	except:
		print "I don't see BrewPi there either. Aborting"
		sys.exit()
if changed: 
	mod = True
try:
	check_repo( Repo('/var/www') )
except:
        print "I don't see BrewPi web files installed to the default path of /var/www "
        choice = raw_input("What path did you install BrewPi web settigs to? ")
        try:
                changed = check_repo(Repo(choice))
        except:
                print "I don't see BrewPi there either. Aborting"
                sys.exit()
if changed: 
	mod = True
if mod:
	try:
		print "Fixing permissions..." 
		fixPermissions()
	except:
		print "I tried to fix permissions, but it failed. Try running it from the command line in your brewpi-script dir"
