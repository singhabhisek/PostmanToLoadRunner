import json
from urllib.parse import urlparse
import os
import sys

def get_postman(path):
    with open(path, 'r', encoding='UTF-8') as postman_f:
        return json.load(postman_f)

# Read input parameters from command line
input_file = sys.argv[1]  # Postman JSON file
output_folder = sys.argv[2]  # Output folder where output will be saved

output_file_path = os.path.join(output_folder, os.path.splitext(os.path.basename(input_file))[0] + ".txt")

data = get_postman(input_file)

names = ""
c_web_set_user = """
    web_set_user("my_uname",
    "my_pwd",
    "my_url:my_port");
    """

c_web_header = """
    web_add_header("my_key",
    "my_value");
    """

c_get_request = """
    web_url("request_name",
            "URL=request_url",
            "Resource=0",
            "RecContentType=application/json",
            "Referer=",
            "Snapshot=snapshot_number.inf",
            "Mode=HTML",
            LAST);
    """

c_post_request = """
    web_custom_request("request_name",
        "URL=request_url",
        "Method=POST",
        "Resource=0",
        "RecContentType=request_content_type",
        "Referer=",
        "Snapshot=snapshot_number.inf",
        "Mode=HTML",
        "EncType=request_enc_type",
        "Body=request_body",
        LAST);
    """

uname = ""
pwdvalue = ""
ictr = 0
dicts = []

for x in range(len(data['item'])):
    try:
        for i in range(len(data['item'][x]['item'])):
            dicts.append(data['item'][x]['item'][i])
    except KeyError:
        dicts.append(data['item'][x])

with open(output_file_path, 'w', encoding='UTF-8') as output_file:
    for names in dicts:
        ictr += 1
        my_web_header = ""
        my_web_set_user = c_web_set_user
        my_get_request = c_get_request
        my_post_request = c_post_request

        if "auth" in names["request"]:
            parsed = urlparse(names["request"]["url"]["raw"])
            
            if names["request"]["auth"]["type"] == "basic":
                for values in names["request"]["auth"]["basic"]:
                    if values["key"] == "password":
                        pwdvalue = values["value"]
                    elif values["key"] == "username":
                        uname = values["value"]
                my_web_set_user = my_web_set_user.replace("my_uname", uname)
                my_web_set_user = my_web_set_user.replace("my_pwd", pwdvalue)
                my_web_set_user = my_web_set_user.replace("my_url", parsed.netloc)
                my_web_set_user = my_web_set_user.replace("my_port", "443" if names["request"]["url"]["protocol"] == "https" else "80")
                output_file.write(my_web_set_user + "\n")
            
            if names["request"]["auth"]["type"] == "bearer":
                my_web_header = c_web_header.replace("my_key", "Authorization").replace("my_value", "Bearer " + names["request"]["auth"]["bearer"][0]["value"])
                output_file.write(my_web_header + "\n")
            
            if names["request"]["auth"]["type"] == "apikey":
                my_web_header = c_web_header.replace("my_key", names["request"]["auth"]["apikey"][1]["value"]).replace("my_value", names["request"]["auth"]["apikey"][0]["value"])
                output_file.write(my_web_header + "\n")

        if "header" in names["request"]:
            for i in range(len(names["request"]["header"])):
                my_web_header = c_web_header.replace("my_key", names["request"]["header"][i]["key"]).replace("my_value", names["request"]["header"][i]["value"])
                output_file.write(my_web_header + "\n")

        if names["request"]["method"] == "GET":
            my_final_string = my_get_request.replace("request_name", names["name"]).replace("request_url", names["request"]["url"]["raw"]).replace("snapshot_number", "t" + str(ictr))
            output_file.write(f"   lr_start_transaction(\"{names['name']}\");\n")
            output_file.write(my_final_string + "\n")
            output_file.write(f"   lr_end_transaction(\"{names['name']}\",LR_AUTO);\n\n")
        
        if names["request"]["method"] == "POST":
            content_type = names["request"]["header"][0]["value"] if "header" in names["request"] and names["request"]["header"] else "application/json"
            enc_type = "application/json" if "json" in content_type.lower() else "text/xml"
            my_final_string = my_post_request.replace("request_name", names["name"]).replace("request_url", names["request"]["url"]["raw"]).replace("snapshot_number", "t" + str(ictr)).replace("request_content_type", content_type).replace("request_enc_type", enc_type)
            my_body_string = names["request"]["body"]["raw"].replace("\r\n", "").replace("\"", '\\\"')
            my_final_string = my_final_string.replace("request_body", my_body_string)
            output_file.write(f"   lr_start_transaction(\"{names['name']}\");\n")
            output_file.write(my_final_string + "\n")
            output_file.write(f"   lr_end_transaction(\"{names['name']}\",LR_AUTO);\n\n")
