import base64
import urllib.request
from asn1crypto.cms import ContentInfo
from OpenSSL.crypto import load_certificate, FILETYPE_ASN1, X509Store, X509StoreContext, X509StoreContextError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import load_der_x509_certificate

def handler(event, context):
    # Load the contents of the receipt file
    receipt_file = open('./sandboxReceipt', 'rb').read()

    # Use asn1crypto's cms definitions to parse the PKCS#7 format
    pkcs_container = ContentInfo.load(base64.b64decode(receipt_file))

    # Extract the certificates, signature, and receipt_data
    certificates = pkcs_container['content']['certificates']
    signer_info = pkcs_container['content']['signer_infos'][0]
    receipt_data = pkcs_container['content']['encap_content_info']['content']

    # Pull out and parse the X.509 certificates included in the receipt
    itunes_cert_data = certificates[0].chosen.dump()
    itunes_cert = load_certificate(FILETYPE_ASN1, itunes_cert_data)

    wwdr_cert_data = certificates[1].chosen.dump()
    wwdr_cert = load_certificate(FILETYPE_ASN1, wwdr_cert_data)

    trusted_root_data = urllib.request.urlopen("https://www.apple.com/appleca/AppleIncRootCertificate.cer").read()
    trusted_root = load_certificate(FILETYPE_ASN1, trusted_root_data)

    trusted_store = X509Store()
    trusted_store.add_cert(trusted_root)

    try:
      X509StoreContext(trusted_store, wwdr_cert).verify_certificate()
      trusted_store.add_cert(wwdr_cert)
    except X509StoreContextError as e:
      print("WWDR certificate invalid")
      exit()

    try:
      X509StoreContext(trusted_store, itunes_cert).verify_certificate()
    except X509StoreContextError as e:
      print("iTunes certificate invalid")
      exit()

    try:
        cert = load_der_x509_certificate(itunes_cert_data, default_backend())
        public_key = cert.public_key()
        public_key.verify(
            signer_info['signature'].native,
            receipt_data.native,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        print("The receipt data signature is valid")
    except Exception as e:
        print("The receipt data is invalid: %s" % e)
