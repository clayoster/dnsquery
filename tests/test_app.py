import re

# All tests validate that responses are HTTP 200

# Test that the initial page load is successful
def test_mainpage(app, client):
    res = client.get('/')
    assert b'type="checkbox" name="ttl" value="true" checked' not in res.data
    assert res.status_code == 200

# Test that a good query includes IP addresses in the results
def test_good_query(app, client):
    res = client.post('/', data={'domain': 'google.com.'})
    assert re.search('result-value">[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}</span>', str(res.data))
    assert b'type="checkbox" name="ttl" value="true" id="ttl" checked' not in res.data
    assert res.status_code == 200

# Test that checking the 'Show TTLs' box remains checked after load, and that TTLs are returned
def test_good_query_ttl(app, client):
    res = client.post('/', data={'domain': 'google.com.', 'ttl': 'true'})
    assert re.search('result-value">[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.*TTL:.*</span>', str(res.data))
    assert b'type="checkbox" name="ttl" value="true" id="ttl" checked' in res.data
    assert res.status_code == 200

# Test that checking the 'Show TTLs' box remains checked after load, and that TTLs are returned
def test_good_query_time(app, client):
    res = client.post('/', data={'domain': 'google.com.', 'query_time': 'true'})
    assert re.search('result-value">[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.*Query Time:.*</span>', str(res.data))
    assert b'type="checkbox" name="query_time" value="true" id="query_time" checked' in res.data
    assert res.status_code == 200

# Test that checking the 'Show TTLs' box remains checked after load, and that TTLs are returned
def test_good_query_ttl_and_time(app, client):
    res = client.post('/', data={'domain': 'google.com.', 'ttl': 'true', 'query_time': 'true'})
    assert re.search('result-value">[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.*TTL:.*Query Time:.*</span>', str(res.data))
    assert b'type="checkbox" name="ttl" value="true" id="ttl" checked' in res.data
    assert b'type="checkbox" name="query_time" value="true" id="query_time" checked' in res.data
    assert res.status_code == 200

# Test that a blank query does not return IP addresses and does contain "Bad Query"
def test_blank_query(app, client):
    res = client.post('/', data={'domain': ''})
    assert not re.search('result-value">[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}</span>', str(res.data))
    assert b'Bad Query - Check domain name' in res.data
    assert res.status_code == 200

# Test that a query with invalid characters does not return IP addreses and does contain "Bad Query"
def test_bad_query(app, client):
    res = client.post('/', data={'domain': 'g##gle.com'})
    assert not re.search('result-value">[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}</span>', str(res.data))
    assert b'Bad Query - Check domain name' in res.data
    assert res.status_code == 200

def test_healthcheck(app, client):
    res = client.get('/health')
    assert b'healthy' in res.data
    assert res.status_code == 200
