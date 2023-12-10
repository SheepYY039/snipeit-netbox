import logging
import math
import requests


import requests
import math


class Snipe:
    """
    A class for interacting with the Snipe-IT API.

    Args:
        url (str): The base URL of the Snipe-IT API.
        token (str): The API token for authentication.

    Attributes:
        url (str): The base URL of the Snipe-IT API.
        token (str): The API token for authentication.
        headers (dict): The headers to be used in API requests.

    Methods:
        get_locations: Retrieves all locations from the Snipe-IT API.
        get_assets_with_mac: Retrieves all assets with MAC fieldsets from the Snipe-IT API.
        get_models_and_manufacturers_with_mac: Retrieves all models and manufacturers with MAC fieldsets from the Snipe-IT API.
        get_companies: Retrieves all companies from the Snipe-IT API.
    """

    def __init__(self, url: str, token: str):
        self.url = f"{url if url[-1] != ' / ' else url[:-1]}/api/v1/"
        self.token = token
        self.headers = {
            "Authorization": "Bearer " + token,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def __get_paged_items(
        self, session: requests.Session, endpoint: str, pagesize: int = 100
    ):
        """
        Helper method to retrieve paged items from the Snipe-IT API.

        Args:
            session (requests.Session): The session object for making API requests.
            endpoint (str): The API endpoint to retrieve items from.
            pagesize (int, optional): The number of items to retrieve per page. Defaults to 100.

        Yields:
            dict: The response JSON for each page of items.
        """
        response = session.get(
            self.url + endpoint,
            params={"limit": pagesize, "offset": 0},
            headers=self.headers,
        ).json()
        yield response
        num_pages = math.ceil(response["total"] / pagesize)

        for page in range(1, num_pages):
            next_page = session.get(
                self.url + endpoint,
                params={"limit": pagesize, "offset": page * pagesize},
                headers=self.headers,
            ).json()
            yield next_page

    @staticmethod
    def __custom_fields_has_mac_type(custom_fields: dict):
        """
        Helper method to check if a dictionary of custom fields contains a field with MAC type.

        Args:
            custom_fields (dict): The dictionary of custom fields.

        Returns:
            bool: True if a field with MAC type is found, False otherwise.
        """
        for field in custom_fields.values():
            if field["field_format"].lower() == "mac":
                return True
        return False

    def get_locations(self):
        """
        Retrieves all locations from the Snipe-IT API.

        Returns:
            list: A list of location objects.
        """
        session = requests.Session()

        locations = []
        for page in self.__get_paged_items(session, "locations", pagesize=200):
            for location in page["rows"]:
                if location not in locations:
                    locations.append(location)

        locations = sorted(locations, key=lambda d: d["name"])
        return locations

    def get_assets_with_mac(self):
        """
        Retrieves all assets with MAC fieldsets from the Snipe-IT API.

        Returns:
            list: A list of asset objects.
        """
        session = requests.Session()

        # i don't know an easy way to fetch only assets with mac fieldsets, so we have to get everything and filter locally

        assets = []
        for page in self.__get_paged_items(session, "hardware", pagesize=200):
            print("Page %s", len(page["rows"]))
            for asset in page["rows"]:
                if Snipe.__custom_fields_has_mac_type(asset["custom_fields"]):
                    if asset not in assets:
                        assets.append(asset)

        # assets = sorted(assets, key=lambda d: d['asset_tag'])
        return assets

    def get_models_and_manufacturers_with_mac(self):
        """
        Retrieves all models and manufacturers with MAC fieldsets from the Snipe-IT API.

        Returns:
            tuple: A tuple containing two lists - manufacturers and models.
        """
        session = requests.Session()

        fieldsets = self.__get_fieldsets_with_mac(session)

        manufacturers = []
        models = []

        for page in self.__get_paged_items(session, "models"):
            for model in page["rows"]:
                if (
                    model["fieldset"] is not None
                    and model["fieldset"]["id"] in fieldsets
                ):
                    if model not in models:
                        models.append(model)

                    if model["manufacturer"] not in manufacturers:
                        manufacturers.append(model["manufacturer"])

        manufacturers = sorted(manufacturers, key=lambda d: d["id"])
        models = sorted(models, key=lambda d: d["id"])

        return manufacturers, models

    def __get_fieldsets_with_mac(self, session: requests.Session):
        """
        Helper method to retrieve fieldsets with MAC type from the Snipe-IT API.

        Args:
            session (requests.Session): The session object for making API requests.

        Returns:
            list: A list of fieldset IDs.
        """
        response = session.get(self.url + "fieldsets", headers=self.headers).json()
        fieldsets_with_mac = []

        for fieldset in response["rows"]:
            for fields in fieldset["fields"]["rows"]:
                if str(fields["format"]).lower() == "mac":
                    fieldsets_with_mac.append(fieldset["id"])
                    break

        return fieldsets_with_mac

    def get_companies(self):
        """
        Retrieves all companies from the Snipe-IT API.

        Returns:
            list: A list of company objects.
        """
        session = requests.Session()
        print(session)
        return session.get(self.url + "companies", headers=self.headers).json()["rows"]
