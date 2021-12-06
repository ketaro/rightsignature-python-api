#!/usr/bin/env python3

import base64
import os
from re import A
import requests
import urllib

from tqdm import tqdm


API_HOST = "api.rightsignature.com"
DOCS_DIR = "docs"

class RightSignature():
    pbar = None
    
    def __init__(self, token=None):
        self.token = token or os.environ.get("PRIVATE_API_TOKEN", None)
        
        if not self.token:
            print("Please set the PRIVATE_API_TOKEN!")
            exit()
        
        self.token_encoded = base64.b64encode(self.token.encode("ascii")).decode()
    
    def request(self, uri, payload={}):
        """Make a request to the RightSignature API

        Args:
            uri (string): API request path (e.g. "documents").
              Do not prefix with "/"
            payload (Dict): Parameters

        Returns:
            list: list of documents
        """
        url = "https://{}/public/v1/{}".format(API_HOST, uri)
        headers = {
            "Authorization": "Basic {}".format(self.token_encoded)
        }
        
        req = requests.get(url, headers=headers, params=payload)
        
        return req.json()
    
    def console(self, msg):
        """Output to tqdm console if it's setup

        Args:
            msg (str): Message string
        """
        if self.pbar is not None:
            self.pbar.write(msg)

    def documents(self):
        """Return list of documents

        Returns:
            list: list of documents
        """
        if self.pbar is not None:
            self.pbar.set_description("Loading Documents")
        
        documents = []
        page = 1
        total = 1
        
        while (page <= total):
            data = self.request("documents", {
                "per_page": 100,
                "page": page
            })
        
            total = data['meta']['total_pages']
            
            self.console("Loaded API Page {} of {}".format(page, total))
       
            documents += data['documents']
            page += 1
        
        return documents
    
    def document(self, document_id):
        """Returns more detailed data for an individual document

        Args:
            document_id (string): Document UUID

        Returns:
            Dict: Document data dictionary
        """
        data = self.request("documents/{}".format(document_id))
    
        return data.get("document", {})
   
    def filename(self, docdata):
        """Generate a filename based on document data.
        We're assuming name + timestamp will be unqiue enough.

        Args:
            docdata (dict): Document data
        
        Returns:
            str: Filename
        """
        filename = "{}/{}-{}.pdf".format(
            DOCS_DIR,
            docdata['name'],
            docdata['executed_at']
        )
        
        # Make filename "safe"
        filename = filename.replace(":", "-")
        
        return filename
        
        
    def sync_signed_docs(self):
        """Downloads all available documents and syncs them
           to the DOC_DIR folder if they do not already exist.
        """
        
        docs = self.documents()
    
        if self.pbar is not None:
            self.pbar.total = len(docs)
            self.pbar.set_description("Syncing")
        
        self.console("Syncing Documents to: {}".format(DOCS_DIR))
    
        for doc in docs:
            if self.pbar is not None:
                self.pbar.update(1)
            
            # We're only interested in executed documents
            if doc['state'] != "executed":
                self.console("skipping non-executed document")
                continue
            
            # Check if we've already downloaded this file
            filename = self.filename(doc)
            if os.path.exists(filename):
                self.console("Already exists: {}".format(filename))
                continue
            
            # Get more info about this document
            docinfo = self.document(doc['id'])
            
            try:
                pdf_url = docinfo['signed_pdf_url']
                self.console("Saving: {}".format(filename))
                urllib.request.urlretrieve(pdf_url, filename=filename)
            except KeyError:
                self.console("[{}] Missing PDF URL: {} {}".format(
                    doc['id'],
                    doc['name'],
                    doc['executed_at']
                ))
