import typing

import js2py
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

ua = UserAgent()

PROXIES: list[dict[str, any]] = []

# Retrieve latest proxies
def update_proxies():
    """
    This function is really complex. Here's how it works:

    1. gets the proxy list from spys
    2. obtains the randomly generated variables used for the hidden port numbers
    3. goes through each proxy and gets the calculation for the port number
    4. performs the calculation
    5. saves data

    This monstrosity could have been avoided if they had just let me scrape


    This is what you get.
    :return:
    """
    proxies_doc = requests.get('https://spys.one/en/socks-proxy-list', headers={"User-Agent": ua.random, "Content-Type": "application/x-www-form-urlencoded"}).text
    soup = BeautifulSoup(proxies_doc, 'html.parser')
    tables = list(soup.find_all("table"))  # Get ALL the tables

    # Variable definitions
    variables_raw = str(soup.find_all("script")[6]).replace('<script type="text/javascript">', "").replace('</script>', '').split(';')[:-1]
    variables = {}
    for var in variables_raw:
        name = var.split('=')[0]
        value = var.split("=")[1]
        if '^' not in value:
            variables[name] = int(value)
        else:
            prev_var = variables[var.split("^")[1]]
            variables[name] = int(value.split("^")[0]) ^ int(prev_var)  # Gotta love the bit math


    trs = tables[2].find_all("tr")[2:]
    for tr in trs:
        address = tr.find("td").find("font")

        if address is None:  # Invalid rows
            continue

        raw_port = [i.replace("(", "").replace(")", "") for i in str(address.find("script")).replace("</script>", '').split("+")[1:]]

        port = ""
        for partial_port in raw_port:
            first_variable = variables[partial_port.split("^")[0]]
            second_variable = variables[partial_port.split("^")[1]]
            port += "("+str(first_variable) + "^" + str(second_variable) + ")+"
        port = js2py.eval_js('function f() {return "" + ' + port[:-1] + '}')()
        PROXIES.append({"ip": address.get_text(), "port": port, "parsed": f"socks5h://{address.get_text()}:{port}"})
    return PROXIES


def get_proxy_sessions(headers: typing.Any | None = None) -> list[requests.Session]:
    sessions = []
    for proxy in PROXIES:
        s = requests.session()
        s.headers = headers
        s.proxies = {"https": proxy['parsed']}
        s.verify = False
        sessions.append(s)
    return sessions

