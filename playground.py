import json

import requests

if __name__ == '__main__':
    res = requests.post('http://0.0.0.0:8000/sdc_api/login/', json={'username': 'Martin', 'password': '1234qweR!'})
    ers_json = res.json()
    refresh = ers_json['refresh_token']
    headers = {
        "Authorization": f"Bearer {refresh}",
    }

    res = requests.get('http://0.0.0.0:8000/sdc_api/login', headers=headers)

    token = res.json()['access_token']
    refresh = res.json()['refresh_token']
    print(token)

    headers = {
        "Authorization": f"Bearer {token}",
    }




    data = {
        "name": "Test Upload",
        "url": "http://localhost:8000/sdc_api/GitInstance",
        "branch": "XXX",
    }

    response = requests.get(
        "http://localhost:8000/sdc_api/GitInstance",
        headers=headers
    )

    data['branch'] += 'y'

    res_post = requests.post(
        f"http://localhost:8000/sdc_api/GitInstance/{response.json()['data'][-1]['pk']}",
        data={'name': 'xx'},
        headers=headers
    )

    res_put = requests.put(
        f"http://localhost:8000/sdc_api/GitInstance/{response.json()['data'][-1]['pk']}",
        data=data,
        headers=headers
    )


    res_patch = requests.patch(
        f"http://localhost:8000/sdc_api/GitInstance/{response.json()['data'][-1]['pk']}",
        data={'url': 'PATCH'},
        headers=headers
    )

    res_list = requests.get(
        f"http://localhost:8000/sdc_api/GitInstance/{response.json()['data'][-1]['pk']}",
        headers=headers
    )

    a = res_list.json()
    print(a)