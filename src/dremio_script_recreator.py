import requests
import argparse
import json
import time
import sys

timeout = 10

def get_auth_token():
  return 'Bearer ' + dremio_pat_token


def submit_sql(url, sql, context=None):
    auth_token = get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": auth_token}
    payload = '{ "sql":"' + sql + '"' + ("" if context is None else ',"context": ' + str(context).replace("'", '"') ) + ' }'
    print("submit_sql: sql: " + str(sql))
    print("submit_sql: payload: " + str(payload))
    response = requests.post(dremio_endpoint + url, payload, headers=headers, timeout=timeout, verify=True)
    if response and response.status_code == 200:
        return response.json()['id']
    else:
        return None


def post_script_data(url, script_item):
    auth_token = get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": auth_token}
    json = {"name": script_item["name"], "content": script_item["content"], "context": script_item["context"], "description": script_item["description"]}
    try:
        job = requests.post(dremio_endpoint + url, headers=headers,
                            verify=True, json=json)
        if job is not None and job.status_code != 200:
            print('Script creation failure, Status code : {}, Status text : {}'.format(job.status_code, job.text))
            return None
    except Exception as e:
        print(e)
        print("Error processing script creation: ".format(e))
        return None
    except:
        return None
    return job.json()


def put_script_privileges(url, grants_json):
    auth_token = get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": auth_token}
    json = grants_json
    try:
        job = requests.put(dremio_endpoint + url, headers=headers,
                            verify=True, json=json)
        if job is not None and job.status_code != 200 and job.status_code != 204:
            print('Script privilege update failure, Status code : {}, Status text : {}'.format(job.status_code, job.text))
            return False
    except Exception as e:
        print(e)
        print("Error processing script privilege updates: ".format(e))
        return False
    except:
        return False
    return True


def generate_script_privileges(privs_item):
    privs_list = []
    privs_list = privs_item["privileges"].split(',')
    grant = {"id": privs_item["user_id"], "name": privs_item["grantee_id"], "granteeType": privs_item["grantee_type"].upper(), "privileges": privs_list }
    return grant


#def assign_script_privileges(privs_item):
#    print("Assigning privileges to script ["+ privs_item['object_id'] + "] : " + privs_item['grantee_type'] + ":" +
#           privs_item['grantee_id'] + " privileges:" + privs_item['privileges'])
#    grant_sql = ('GRANT ' + privs_item['privileges'].replace('"', '\\"') + ' ON SCRIPT \\"' + privs_item['object_id'] +
#                 '\\" TO ' + privs_item['grantee_type'] + ' \\"' + privs_item['grantee_id'] + '\\"')
#    submit_sql('api/v3/sql', grant_sql)


def recreate_script(script_details):
    print("Recreating script " + script_details['name'])
    script_response = post_script_data('apiv2/scripts', script_details)
    if script_response is None:
        return None
    return script_response["id"]


def main():
    # Read file lambda
    if sys.version_info.major > 2:
        f_open = lambda filename: open(filename, "r", encoding='utf-8')
    else:
        f_open = lambda filename: open(filename, "r")

    if input_script_file and input_privs_file:
        script_file = f_open(input_script_file)
        privs_file = f_open(input_privs_file)

        try:
            script_data = [json.loads(line) for line in script_file]
            privs_data = [json.loads(line) for line in privs_file]
            for script_item in script_data:
                script_details = json.loads(script_item["value"])
                script_id = recreate_script(script_details)
                grants = []
                for privs_item in privs_data:
                    if script_details["name"] == privs_item["object_id"]:
                        grant = generate_script_privileges(privs_item)
                        grants.append(grant)
                grants_json = {"id": script_id, "grants": grants}
                grant_url = 'apiv2/scripts/' + script_id + '/grants'
                print("Updating privileges for script " + script_details['name'])
                put_script_privileges(grant_url, grants_json)
        except Exception as e:
            print(e)
        script_file.close()

    #if input_privs_file:
    #    privs_file = f_open(input_privs_file)
    #    try:
    #        privs_data = [json.loads(line) for line in privs_file]
    #        for privs_item in data:
    #            #NOTE: I TRIED USING GRANT STATEMENTS BUT THIS WAS UNRELIABLE - NEEDS INVESTIGATING
    #            #assign_script_privileges(privs_item)
    #    except Exception as e:
    #        print(e)
    #    privs_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog = 'Dremio Script Recreator',
                        description = 'The tool reads scripts exported from one Dremio environment and recreates them in a target environment. It also gives the same privileges to people who had access to the original scripts.')
    parser.add_argument('--input-script-file', type=str,
                        help='script_backup.json file taken from source environment backup, contains scripts to recreate',
                        required=True)
    parser.add_argument('--input-privs-file', type=str,
                        help="json file of results exported from the Dremio UI from running the following query in the source Dremio environment which details which users had privileges on which scripts:\nSELECT u.user_id, p.grantee_id, p.grantee_type, p.object_id, listagg(p.privilege, ',') AS privileges\nFROM sys.privileges p INNER JOIN sys.users u\nON p.grantee_id = u.user_name\nWHERE p.object_type = 'SCRIPT'\nGROUP BY u.user_id, p.grantee_id, p.grantee_type, p.object_id",
                        required=False)
    parser.add_argument('--url', type=str, help='Dremio url, example: https://localhost:9047/', required=True)
    parser.add_argument('--pat-token', type=str, help='PAT token of an admin user that will be used to recreate the scripts', required=True)
    args = parser.parse_args()

    input_script_file = args.input_script_file
    input_privs_file = args.input_privs_file
    dremio_endpoint = args.url
    dremio_pat_token = args.pat_token


    main()
