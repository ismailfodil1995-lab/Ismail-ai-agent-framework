import requests


class APIManager:
    """
    مسؤول عن إرسال واستقبال طلبات REST APIs.
    """

    def get(self, url, headers=None, params=None, timeout=30):

        response = requests.get(
            url=url,
            headers=headers,
            params=params,
            timeout=timeout
        )

        return response

    def post(self, url, json=None, data=None, headers=None, timeout=30):

        response = requests.post(
            url=url,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout
        )

        return response

    def put(self, url, json=None, headers=None, timeout=30):

        response = requests.put(
            url=url,
            json=json,
            headers=headers,
            timeout=timeout
        )

        return response

    def delete(self, url, headers=None, timeout=30):

        response = requests.delete(
            url=url,
            headers=headers,
            timeout=timeout
        )

        return response