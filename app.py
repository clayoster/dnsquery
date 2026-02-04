#!/usr/bin/python3

import ipaddress
import re
import time
from flask import Flask, request, render_template
from dns import exception, resolver, reversename
import yaml

app = Flask(__name__)

# Define a Resolver instance
dnsquery_resolver = resolver.Resolver()

# Set query timeout to 2 seconds
dnsquery_resolver.timeout = 2
dnsquery_resolver.lifetime = 2

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

@app.route('/health')
def healthcheck():
    """Return the healthcheck"""
    return "healthy"

@app.route('/', methods = ['GET'])
def show_main():
    """Return the main form"""
    return show_form()

@app.route('/', methods = ['POST'])
def handle_submit():
    """ Handle submissions to the web form """
    dns_data = None
    error = None
    ttl = None
    query = None
    query_time = None

    # Validate that the domain name doesn't contain invalid characters
    query = request.form.get('query', None)
    dns_name, ip_address, query_type = validate_input(query)

    # Retrieve variables from the form and force lowercase characters for DNS name queries
    if dns_name:
        query = request.form.get('query', None).lower()
    ttl = request.form.get('ttl', 'false')
    query_time = request.form.get('query_time', 'false')

    # If the domain name passes the validation check, perform queries
    if dns_name or ip_address:
        # Prepare lists for compiling DNS data
        keys = []
        values = []
        for service,options in dns_servers['dnsquery'].items():
            ip = options.get('ip', None)
            query_data = perform_query(service, ip, query, query_type, ttl, query_time)

            # Add data from the query to the lists
            keys.append(service)
            values.append(query_data)

            # Compile DNS data into a dict
            dns_data = dict(zip(keys, values))
    else:
        error = 'Bad Query - Check for correct format and invalid characters'

    return show_form(dns_data=dns_data,query=query,error=error,ttl=ttl,query_time=query_time)

def validate_input(query):
    """ Function for validating user input and determining query type """
    # Set variable defaults
    dns_name = None
    ip_address = None
    query_type = None

    # Test if this is a valid DNS name
    if re.match(r"^([-a-z0-9]+\.)+[a-z]{2,}\.*$", query):
        dns_name = True
        query_type = 'dns_name'
    else:
        dns_name = False

    # Test if the query is a valid IP address
    try:
        ipaddress.ip_address(query)
        ip_address = True
        query_type = 'ip_address'
    except ValueError:
        ip_address = False

    return dns_name, ip_address, query_type

def perform_query(service, ip, query, query_type, ttl, query_time): # pylint: disable=too-many-arguments,too-many-positional-arguments
    """ Function for completing DNS queries """
    # Set variable defaults
    dns_time = None
    record_type = None
    query_data = {"results": [], "detail": []}
    query_final = None

    # Set Nameserver IP
    dnsquery_resolver.nameservers = [ip]

    if query_type == 'dns_name':
        record_type = 'A'
        query_final = query
    elif query_type == 'ip_address':
        record_type = 'PTR'
        # Reverse the IP for the PTR query
        query_final = reversename.from_address(query)

    try:
        # Capture query start time
        dns_start = time.time()

        # Perform query
        dnsquery_answers = dnsquery_resolver.resolve(query_final, record_type)

        # Capture query end time and determine response time
        dns_end = time.time()
        dns_time = str(round(((dns_end - dns_start) * 1000), 2))

        # Add results to query_data["results"]
        for r in dnsquery_answers:
            query_data["results"].append(r)

        # Add query details to query_data["detail"] if requested
        if ttl == 'true':
            query_data["detail"].append(f"TTL: {dnsquery_answers.rrset.ttl} sec")

        if query_time == 'true':
            query_data["detail"].append(f"Query Time: {dns_time} msec")

    except resolver.NoAnswer:
        query_data["results"].append("No answer")
    except resolver.NXDOMAIN:
        query_data["results"].append("Domain not found")
    except exception.Timeout:
        # Log the error
        print(">>> Timeout querying server (" + service + " / " + ip + ")")
        query_data["results"].append("Timeout querying server")
    except resolver.NoNameservers as e:
        # Log the error
        print(">>> Server did not respond correctly (" + service + " / " + ip + ")")
        query_data["results"].append("Server did not respond correctly: " + str(e))
    except Exception as e: # pylint: disable=broad-except
        # Log the error
        print(">>> Exception occurred: " + str(e))
        query_data["results"].append("Exception occurred: " + str(e))

    return query_data

def show_form(dns_data = None, query = None, error = None, ttl = None, query_time = None):
    """ Return the templated form (with data if provided) """
    return render_template('form.html', dns_data=dns_data, query=query, error=error, ttl=ttl, query_time=query_time)

# Run 'python app.py' from the cli to bring the app up in debugging mode on port 8080
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
