# Configuration 
#
PYVENV = /usr/bin/env pyvenv-3.4  # This is the version in ix.cs.uoregon.edu

##
## Install in a new environment:
##     We need to rebuild the Python environment to match
##     
install:
	# pyvenv-3.4 env ### BUGGY on ix
	echo "pyvenv without PIP to work around ubuntu bug"
	$(PYVENV) --without-pip env
	echo ""
	(.  env/bin/activate; curl https://bootstrap.pypa.io/get-pip.py | python)
	(.  env/bin/activate; pip install -r requirements.txt)

dist:
	#virtualenv env
	#source env/bin/activate
	pip install -r requirements.txt
	python -m pip install pymongo
	#pip freeze >requirements.txt

