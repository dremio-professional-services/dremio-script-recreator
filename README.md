# Dremio Script Recreator

Dremio Script Recreator is a python-based utility for Dremio Enterprise. 
It enables an administrative user to recreate all scripts in a target environment by reading system resources and taking a file from a backup of a source environment. 

Running standalone 
python dremio-script-recreator.py --url http://<your ip>:9047/ --input-script-file INPUT_SCRIPT_FILE --input-privs-file INPUT_PRIVS_FILE --pat-token PAT_TOKEN

Where
INPUT_SCRIPT_FILE: Script_backup.json file taken from a dremio-admin backup of the source environment using the -j option, this file contains the scripts to recreate.
INPUT_PRIVS_FILE: json file of results exported from the Dremio UI from running the following query in the source Dremio environment which details which users had privileges on which scripts:

SELECT u.user_id, p.grantee_id, p.grantee_type, p.object_id, listagg(p.privilege, ',') AS privileges
FROM sys.privileges p INNER JOIN sys.users u
    ON p.grantee_id = u.user_name
WHERE p.object_type = 'SCRIPT'
GROUP BY u.user_id, p.grantee_id, p.grantee_type, p.object_id

PAT_TOKEN: PAT token from the target Dremio environment of an Admin user used to recreate the scripts and reset the privileges
