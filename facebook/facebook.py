import json, requests


class Facebook:

    ########################################################################################
    def __init__ (self, username: str, app_id: str, app_secret: str, user_token: str):
        self.APP_ID = app_id
        self.APP_SECRET = app_secret
        self.USER_TOKEN = user_token
        self.URL = "https://graph.facebook.com/v23.0"

        self.PAGE_TOKEN = ""
        self.PAGE_ID = ""
        self.PAGE_NAME = ""

        self.connected = False
        self.accounts = []

        self.USER_TOKEN = self.getUserToken()

        url = f"{self.URL}/me/accounts"
        params = {
            'access_token': self.USER_TOKEN
        }
        response = requests.get(url, params = params)
        if response.status_code // 100 == 2:
            print("Connected to Facebook")
            self.connected = True
            self.accounts = json.loads(response.text)['data']
            if not self.selectPageAccount(username):
                print ("Could not select indicated page. Aborting program.")
                exit(1)
            print ("Page information loaded.")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    #########################################################################################################################
    def getUserToken(self):
        response = requests.get(
            f"{self.URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.APP_ID,
                "client_secret": self.APP_SECRET,
                "fb_exchange_token": self.USER_TOKEN,
            }
        )
        
        if response.status_code // 100 == 2:
            print("refreshed access token.")
            # print(response.json())
            # self.FB_USER_TOKEN = json.loads(response.text)['access_token']
            return json.loads(response.text)['access_token']
        else:
            print(f"Error: {response.status_code} - {response.text}")


    #########################################################################################################################
    def selectPageAccount (self, username: str):
        if not self.connected:
            print("Not connected to Facebook")
            return False
        for account in self.accounts:
            if account['name'] == username:
                self.PAGE_ID = account['id']
                self.PAGE_NAME = account['name']
                self.PAGE_TOKEN = account['access_token']
                return True
        return False


    #########################################################################################################################
    def getPagePosts(self):
        if self.connected:
            url = f"{self.URL}/{self.PAGE_ID}/posts"
            params = {
                'access_token': self.PAGE_TOKEN
            }
        response = requests.get(url, params = params)
        if response.status_code // 100 == 2:
            print("Connected to user posts.")
            return json.loads(response.text)
        else:
            print(f"Error: {response.status_code} - {response.text}")



    #########################################################################################################################
    # Returns the id of the post just published or None if failure
    #########################################################################################################################
    def post (self, message: str, photo_ids: list = []):
        media = []
        if self.connected:
            url = f"{self.URL}/{self.PAGE_ID}/feed"
            data = {
                'access_token': self.PAGE_TOKEN,
                'message': message
            }
            if len(photo_ids) > 0:
                for photo in photo_ids:
                    media.append({'media_fbid': photo})
                data['attached_media'] = json.dumps(media)
        response = requests.post(url, data = data)
        if response.status_code // 100 == 2:
            print("Post was successful...")
            return json.loads(response.text)['id']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None



    #########################################################################################################################
    # Returns the id of the photo just published or none if failure
    #########################################################################################################################
    def postPhoto (self, url: str, caption: str = ''):
        if self.connected:
            # Downloading file from the internet
            img = requests.get(url, timeout=30)
            img.raise_for_status()
            files = {"source": ("image.jpg", img.content, "image/jpeg")}

            url = f"{self.URL}/{self.PAGE_ID}/photos"
            data = {
                'access_token': self.PAGE_TOKEN,
                'published': 'false'
            }
            if caption: data['message'] = caption
            response = requests.post (url, data = data, files = files)
            if response.status_code // 100 == 2:
                print("Photo posting was successful...")
                return json.loads(response.text)['id']
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        return None


    #########################################################################################################################
    # Returns the id of the photo just published or none if failure
    # to be further developed
    #########################################################################################################################
    def getPost (self, post_id : str):
        if self.connected:
            url = f"{self.FB_URL}/{post_id}"
            fields = "id,permalink_url,created_time,updated_time,message,message_tags,status_type,from,is_published,is_hidden,privacy,shares"
            params = {
                'access_token': self.PAGE_TOKEN,
                'fields': fields
            }
            response = requests.get (url, params = params)
            if response.status_code // 100 == 2:
                print("Post returned information")
                return json.loads(response.text)
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        return None





if __name__ == "__main__":
    print ("Cannot be executed. Import into a script.")
    exit(1)
    