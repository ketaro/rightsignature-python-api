#!/usr/bin/env python3

from tqdm import tqdm
from api import RightSignature

API_HOST = "api.rightsignature.com"
DOCS_DIR = "docs"


if __name__ == "__main__":
    rs = RightSignature()
    
    with tqdm(unit="document") as pbar:
        rs.pbar = pbar
        rs.sync_signed_docs()
