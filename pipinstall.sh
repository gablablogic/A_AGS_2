export HTTP_PROXY=http://10.146.229.176:80
export HTTPS_PROXY=http://10.146.229.176:80
python.exe -m pip install --upgrade pip --no-warn-script-location --trusted-host pypi.org --trusted-host files.pythonhosted.org
python.exe -m pip install --upgrade -r mypythonpackages.txt --no-warn-script-location --trusted-host pypi.org --trusted-host files.pythonhosted.org
#python.exe -m pip uninstall pyautogen --trusted-host pypi.org --trusted-host files.pythonhosted.org
