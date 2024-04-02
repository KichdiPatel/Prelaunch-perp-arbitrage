def alert(msg):
    import http.client, urllib

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request(
        "POST",
        "/1/messages.json",
        urllib.parse.urlencode(
            {
                "token": "aqx83gkox6u4ey6r9cmrba9xk5hn5j",
                "user": "ugp1z29bj7gr4ht5wpnym66quzhc1k",
                "message": msg,
            }
        ),
        {"Content-type": "application/x-www-form-urlencoded"},
    )
    conn.getresponse()


# alert("HELLO WORLD")
