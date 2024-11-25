#!/usr/bin/python3

import re
import time
from flask import Flask, request, render_template
import dns.resolver
import yaml

app = Flask(__name__)

my_resolver = dns.resolver.Resolver()

# Default set of DNS servers to query. These will be used if the
# servers.yml file does not exist.
DNS_SERVERS_EXAMPLE = """
dnsquery:
  Example - CloudFlare - 1.1.1.1:
    ip: 1.1.1.1
  Example - Google - 8.8.8.8:
    ip: 8.8.8.8
"""

# Attempt to load servers.yml. If that fails, use DNS_SERVERS_EXAMPLE
# that is set above
try:
    with open('servers.yml', 'r', encoding='utf-8') as file:
        dns_servers = yaml.safe_load(file)
except IOError:
    print('servers.yml file is missing, using default nameserver list')
    dns_servers = yaml.safe_load(DNS_SERVERS_EXAMPLE)

@app.route('/', methods = ['GET'])
def show_main():
    """Return the main form"""
    return show_form()

@app.route('/', methods = ['POST'])
def handle_submit():
    """ Handle submissions to the web form """
    dns_data = None
    domain= None
    error = None
    ttl = None
    query_time = None

    # Retrieve variables from the form and force lowercase characters
    domain = request.form.get('domain', None).lower()
    ttl = request.form.get('ttl', 'false')
    query_time = request.form.get('query_time', 'false')

    # Validate that the domain name doesn't contain invalid characters
    validate_input = re.match(r"^([-a-z0-9]+\.)+[a-z]{2,}\.*$", domain)

    # If the domain name passes the validation check, perform queries
    if validate_input:
        keys = []
        values = []
        for service,options in dns_servers['dnsquery'].items():
            ip = options.get('ip', None)
            query_data = perform_query(service, ip, domain, ttl, query_time)

            keys.append(service)
            values.append(query_data)

            # Compile DNS data into a dict
            dns_data = dict(zip(keys, values))
            #print(dns_data)
    else:
        error = 'Bad Query - Check domain name for correct format and invalid characters'

    return show_form(dns_data=dns_data,domain=domain,error=error,ttl=ttl,query_time=query_time)

def perform_query(service, ip, domain, ttl, query_time):
    """ Function for completing DNS queries """
    # Set variable defaults
    dns_time = None
    query_data = None

    # Set Nameserver IP
    my_resolver.nameservers = [ip]

    # Setting query timeout to 2 seconds
    my_resolver.timeout = 2
    my_resolver.lifetime = 2

    try:
        # Capture query start time
        dns_start = time.time()

        # Perform query
        my_answers = my_resolver.resolve(domain)

        # Capture query end time and determine response time
        dns_end = time.time()
        dns_time = str(round(((dns_end - dns_start) * 1000), 2))

        for rdata in my_answers:
            query_data = rdata.address
            if ttl == 'true':
                query_data += " -- TTL: " + str(my_answers.rrset.ttl) + " sec"
            if query_time == 'true':
                query_data += " -- Query Time: " + dns_time + " msec"
            #print(rdata.address)
            #print(str(my_answers.rrset.ttl)
    except dns.resolver.NoAnswer:
        query_data = "No answer"
    except dns.resolver.NXDOMAIN:
        query_data = "Domain not found"
    except dns.exception.Timeout:
        # Log the error
        print(">>> Timeout querying server (" + service + " / " + ip + ")")
        query_data = "Timeout querying server"
    except dns.resolver.NoNameservers as e:
        # Log the error
        print(">>> Server did not respond correctly (" + service + " / " + ip + ")")
        query_data = "Server did not respond correctly: " + str(e)
    except Exception as e: # pylint: disable=broad-except
        # Log the error
        print(">>> Exception occurred: " + str(e))
        query_data = "Exception occurred: " + str(e)

    return query_data

def show_form(dns_data = None, domain = None, error = None, ttl = None, query_time = None):
    """ Return the templated form (with data if provided) """
    return render_template('form.html', dns_data=dns_data, domain=domain, error=error, ttl=ttl, query_time=query_time)

# Run 'python app.py' from the cli to bring the app up in debugging mode on port 8080
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
