import base64
import requests
import logging
from typing import List, Dict, Optional, Any

class OpenProjectClient:
    """Client for interacting with OpenProject API v3"""
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        auth_string = f"apikey:{api_key}"
        encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        logging.info(f"Initialized OpenProject client for {self.base_url}")

    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v3{endpoint}"
        response = self.session.request(method=method, url=url, params=params, json=data)
        response.raise_for_status()
        return response.json()

    def get_projects(self, limit: int = 1000) -> List[Dict[str, Any]]:
        all_projects = []
        offset = 1
        page_size = 100
        while True:
            params = {'pageSize': page_size, 'offset': offset}
            response = self._make_request('/projects', params=params)
            elements = response.get('_embedded', {}).get('elements', [])
            if not elements:
                break
            all_projects.extend(elements)
            total = response.get('total', 0)
            if len(all_projects) >= total or len(all_projects) >= limit:
                break
            offset += page_size
        return all_projects

    def get_project(self, project_id: int) -> Dict[str, Any]:
        return self._make_request(f'/projects/{project_id}')

    def get_work_packages(self, project_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
        all_work_packages = []
        offset = 1
        page_size = 100
        while True:
            params = {
                'pageSize': page_size,
                'offset': offset,
                'filters': '[{"project_id": {"operator": "=", "values": ["%s"]}}]' % str(project_id)
            }
            response = self._make_request('/work_packages', params=params)
            elements = response.get('_embedded', {}).get('elements', [])
            if not elements:
                break
            all_work_packages.extend(elements)
            total = response.get('total', 0)
            if len(all_work_packages) >= total or len(all_work_packages) >= limit:
                break
            offset += page_size
        return all_work_packages

    def get_work_package_relations(self, work_package_id: int) -> List[Dict[str, Any]]:
        try:
            response = self._make_request(f'/work_packages/{work_package_id}/relations')
            return response.get('_embedded', {}).get('elements', [])
        except requests.exceptions.RequestException:
            logging.warning(f"Could not fetch relations for work package {work_package_id}")
            return []
