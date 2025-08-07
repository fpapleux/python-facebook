import os
import copy
import json
import requests
import time
from urllib.parse import urlparse
from .signatures import Signatures
from .chatgpt import Gpt

DEBUG = False

 
class StrapiCollection:

    #################################################################################
    def __init__(self, 
                 url : str, 
                 token : str, 
                 collection_name : str,
                 multimedia : list = None,
                 singlemedia : list = None,
                 singlerelations : list = None,
                 multirelations : list = None,
                 localizedFields : list = None,
                 default_locale : str = "en",
                 other_locales : list = None,
                 singleType : bool = False
                 ):

        self.serverUrl = url
        self.url = f"{url}/api"
        self.token = token
        self.singleType = singleType
        self.collectionType = not self.singleType

        self.collection_name = collection_name
        self.multimedia = multimedia
        self.singlemedia = singlemedia
        self.singlerelations = singlerelations
        self.multirelations = multirelations
        self.localizedFields = localizedFields
        self.default_locale = default_locale
        self.other_locales = other_locales

        self.medias = (self.multimedia if self.multimedia else []) + (self.singlemedia if self.singlemedia else [])
        self.relations = (self.multirelations if self.multirelations else []) + (self.singlerelations if self.singlerelations else [])

        self.documents = []
        self.isSingle = False
        self.isList = True
        self.index = 0
        self.headers = { "Authorization": f"Bearer {self.token}" }
        self.signatures_filename = f"{urlparse(self.url).netloc}-signatures.json"
        self.signatures = Signatures(file_path=self.signatures_filename)
        self.load_all()



    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    ### Loads all documents in the collection into the object
    #################################################################################
    def load_all (self):
        url = f"{self.url}/{self.collection_name}?"
        params = f"locale={self.default_locale}&populate=localizations"
        for field in self.medias:
            params += f"&populate={field}"
        for field in self.relations:
            params += f"&populate={field}"
        url += params

        response = requests.get(url, headers=self.headers)
        if response.status_code == 404:
            print ("-----------------------------------------------------------------")
            print (f"Could not retrieve collection [{self.collection_name}]")
            print (f"Status Code: {response.status_code}")
            print (f"Reason: {response.reason}")
            print (f"Moving on with an empty collection...")
        else:
            if response.status_code > 299:
                print ("-----------------------------------------------------------------")
                print (f"Could not retrieve collection [{self.collection_name}]")
                print (f"Tried to use url: {url}")
                print (f"Status Code: {response.status_code}")
                print (f"Reason: {response.reason}") 
                print (f"{json.dumps(response.json(), indent=2)}")
                print (f"With parameters: \n{json.dumps(params, indent = 2)}")
                exit(1)

        self.documents = []
        results = json.loads(response.content)['data']
        if DEBUG: print (f"CONTENT OF THE LOAD ALL CALL:\n {json.dumps(results, indent = 2)}")
        if isinstance(results, list): 
            if DEBUG: print ("It's a list")
            self.singleType = False
            self.collectionType = True
            self.isSingle = False
            self.isList = True
            self.documents.extend(results)
        else:
            if DEBUG: print ("It's a single")
            self.singleType = True
            self.collectionType = False
            self.isSingle = True
            self.isList = False
            self.documents.append(results)
        if DEBUG: print (f"SELF.COLLECTION IS...\n {json.dumps(self.documents, indent = 2)}")




    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    ### creates a localization document for locale "locale" in the document at index
    ### "index" in the current collection. Deletes any existing localization from
    ### memory and from the Strapi instance if necessary; otherwise creates a new one
    ### and saves it to both.
    #################################################################################
    def localizeByIndex (self, index : int, locale : str):

        newDoc = copy.deepcopy (self.documents[index])

        ## **** IN CASE OF SINGLE TYPE COLLECTION, docId MUST BE EMPTY!!
        if self.singleType:
            docId = ""
        else:
            docId = self.documents[index]['documentId']


        # MODEL FOR A SINGLE MEDIA TYPE
        if self.singlemedia is not None and len(self.singlemedia) > 0:
            for field in self.singlemedia:
                if (field in newDoc) and (newDoc[field] is not None):
                    if 'id' in newDoc[field]:
                        id = newDoc[field]['id']
                        newDoc.pop (field, None)
                        newDoc[field] = { 'id': id }

        # MODEL FOR A MULTI MEDIA TYPE
        if self.multimedia is not None and len(self.multimedia) > 0:
            for field in self.multimedia:
                if (field in newDoc) and (newDoc[field] is not None):
                    ids = []
                    for media in newDoc[field]:
                        ids.append({ "id": media['id'] })
                    newDoc.pop (field, None)
                    newDoc[field] = ids

        # MODEL FOR A MULTI RELATIONSHIP TYPE
        if self.multirelations is not None and len(self.multirelations) > 0:
            for field in self.multirelations:
                if field in newDoc and newDoc[field] is not None and len(newDoc[field]) > 0:
                    newlist = []
                    for item in newDoc[field]:
                        if 'documentId' in item:
                            newlist.append(item['documentId'])
                    newDoc.pop(field, None)
                    newDoc[field] = newlist

        # MODEL FOR A SINGLE RELATIONSHIP TYPE

        if self.singlerelations is not None and len(self.singlerelations) > 0:
            for field in self.singlerelations:
                if (field in newDoc) and (newDoc[field] is not None):
                    id = newDoc[field]['documentId']
                    newDoc.pop (field)
                    newDoc[field] = [id]
        
        # Removing other unwanted fields
        for field in ["documentId", "locale", "id", "createdAt", "updatedAt", "publishedAt", "localizations"]:
            newDoc.pop(field, None)
        

        # Translate the document
        gpt = Gpt('translator-single-value')

        request = json.dumps ({
            "locale": locale,
            "text": self.stringify(newDoc)
        }, indent = 2)

        attempt = 1
        successful = False
        while not successful and attempt <= 5:
            response = gpt.request (request)
            try:
                st = json.loads(response)["text"]
                successful = True
            except ValueError:
                attempt += 1
                print (f"Conversion to JSON of ChatGPT's response failed. Attempt {attempt} / 5")

        if successful:
            self.destringify (st, newDoc)

            # removing fields with no value
            for field in list(newDoc):
                if (newDoc[field] is None) or (isinstance(newDoc[field], list) and len(newDoc[field]) == 0):
                    newDoc.pop(field, None)
                    continue

            # Removing fields that are not targeted for localization
            #for field in list(newDoc):
            #    if field not in self.localizedFields:
            #        newDoc.pop(field, None)
            #        continue

            self.saveLocalization(document = newDoc, parentId = docId, locale = locale)
            self.load_all()
        return


    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    ### Creates a single string containing all fields to translate using ' ### ' as
    ### separator.
    #################################################################################
    def stringify (self, col: dict):
        st = ""
        for field in self.localizedFields:
            st += f"{col[field] or ''} ### "
        if len(st) > 5:
            st = st[:-5] # removing last 5 characters which should be ###
        return st


    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    ### Splits the string back into its fields in the given document
    #################################################################################
    def destringify (self, st : str, doc: dict):
        lis = st.split (" ### ")
        if len(lis) < 1:
            print ("*********************************************")
            print ("Error trying to destringify")
            print (f"Document Type: {self.collection_name}")
            print (f"Received string: [[{st}]]")
            exit(1)
        else:
            index = 0
            for field in self.localizedFields:
                print (f"----------------------------------------------------")
                print (f"processing field: {field}")
                if 'docname' in doc: print (f"from doc {doc['docname']}")
                print (f"** ORIGINAL VALUE:\n {doc[field]}")
                if index < len(lis): print (f"** TRANSLATED VALUE:\n {lis[index]}")
                print (f"----------------------------------------------------\n\n")
                if index < len(lis): doc[field] = lis[index]
                index += 1
        return


    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    ### Translates the document at index 'index'
    #################################################################################
    def translate (self, index: int):
        docId = self.documents[index]['documentId']
        for locale in self.other_locales:
            if DEBUG: print (f"translating into {locale}")
            self.localizeByIndex (index, locale)
        self.signatures.update (docId)


    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    #################################################################################
    ############################################################################""
    ### saves a new localization document for a given document.
    ############################################################################""
    def saveLocalization (self, document: dict, parentId: str, locale: str,
                          relationships: list = []):
        target_url = f"{self.url}/{self.collection_name}"
        headers = self.headers
        if parentId: 
            docId = f"/{parentId}"
        else:
            docId = ""
        target_url = f"{target_url}{docId}?locale={locale}"
        # print (f"Target URL: {target_url}")
        clean_item = copy.deepcopy(document)
        for field in ["locale", "documentId", "id", "createdAt", "updatedAt", "publishedAt", "localizations"]:
            clean_item.pop(field, None)
        if DEBUG: print (json.dumps(clean_item, indent = 2))
        
        data = { "data": clean_item }
        print (f"_____________SAVING___to___{target_url}_______________________________________")
        print ('\n', json.dumps(data, indent=2, ensure_ascii=False))
        print (f"________________________________________________________________")

        attempt = 1
        successful = False
        while not successful and attempt <= 5:
            time.sleep(1)
            response = requests.put (
                url = target_url,
                headers = headers,
                json = data
            )
            if response.status_code >= 200 and response.status_code <= 299:
                successful = True
                item = json.loads(response.text)['data']
                updated_at = item["updatedAt"]
                if parentId:
                    self.load_all()
                    for record in self.documents:
                        if record['documentId'] == parentId:
                            print ("Found master document")
                            updated_at = record["updatedAt"]
                            break
                self.signatures.update(item['documentId'], updated_at)
                print (f"Localization saved successfully")
            else:
                print (f"Attempt: {attempt} / 5")
                print (f"{response.status_code} - {response.reason}")
                print (f"{response.text}")
                print ("Localization save was unsuccessful\n\n")
                attempt += 1
                

        return json.loads(response.text)

