import base64
import urllib.request
import json
from asn1crypto.cms import ContentInfo
from OpenSSL.crypto import load_certificate, FILETYPE_ASN1, X509Store, X509StoreContext, X509StoreContextError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import load_der_x509_certificate
from asn1crypto.core import Any, Integer, ObjectIdentifier, OctetString, Sequence, SetOf, UTF8String, IA5String

def lambda_handler(event, context):
    payload = event.get('payload')
    if payload is None:
        return {
            "message": "payload is none",
            "result": False
        }
    receipt_file = payload

    try:
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
    except Exception as e:
        error_message = str(e)
        print(f"receipt data is invalid 1: {error_message}")
        return {
            "message": "receipt data is invalid type",
            "result":False
        }

    try:
        trusted_root_data = urllib.request.urlopen("https://www.apple.com/appleca/AppleIncRootCertificate.cer").read()
        trusted_root = load_certificate(FILETYPE_ASN1, trusted_root_data)
        trusted_store = X509Store()
        trusted_store.add_cert(trusted_root)
    except Exeption as e:
        error_message = str(e)
        print(f"failed to load root certificate: {error_message}")
        return {
            "message": "failed to load root certificate",
            "result":False
        }

    try:
        X509StoreContext(trusted_store, wwdr_cert).verify_certificate()
        trusted_store.add_cert(wwdr_cert)
    except X509StoreContextError as e:
        error_message = str(e)
        print(f"WWDR certificate invalid: {error_message}")
        return {
            "message": "WWDR certificate invalid",
            "result":False
        }

    try:
        X509StoreContext(trusted_store, itunes_cert).verify_certificate()
    except X509StoreContextError as e:
        error_message = str(e)
        print(f"iTunes certificate invalid: {error_message}")
        return {
            "message": "iTunes certificate invalid",
            "result":False
        }

    try:
        cert = load_der_x509_certificate(itunes_cert_data, default_backend())
        public_key = cert.public_key()
        public_key.verify(
            signer_info['signature'].native,
            receipt_data.native,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
    except Exception as e:
        error_message = str(e)
        print(f"receipt data is invalid 2: {error_message}")
        return {
            "message": "receipt data is invalid",
            "result":False
        }

    # parse receipt data
    attribute_types = [
        (2, 'bundle_id', UTF8String),
        (3, 'application_version', UTF8String) ,
        (4, 'opaque_value', None),
        (5, 'sha1_hash', None),
        (12, 'creation_date', IA5String),
        (17, 'in_app', OctetString),
        (19, 'original_application_version', UTF8String),
        (21, 'expiration_date', IA5String)
    ]

    class ReceiptAttributeType(Integer):
        _map = {type_code: name for type_code, name, _ in attribute_types}

    class ReceiptAttribute(Sequence):
        _fields = [
            ('type', ReceiptAttributeType),
            ('version', Integer),
            ('value', OctetString)
        ]

    class Receipt(SetOf):
        _child_spec = ReceiptAttribute

    receipt = Receipt.load(receipt_data.native)
    receipt_attributes = {}
    attribute_types_to_class = {name: type_class for _, name, type_class in attribute_types}

    in_apps = []
    for attr in receipt:
      attr_type = attr['type'].native
      if attr_type == 'in_app':
        in_apps.append(attr['value'])
        continue
      if attr_type in attribute_types_to_class:
        if attribute_types_to_class[attr_type] is not None:
          receipt_attributes[attr_type] = attribute_types_to_class[attr_type].load(attr['value'].native).native
        else:
          receipt_attributes[attr_type] = attr['value'].native

    in_app_attribute_types = {
        (1701, 'quantity', Integer),
        (1702, 'product_id', UTF8String),
        (1703, 'transaction_id', UTF8String),
        (1705, 'original_transaction_id', UTF8String),
        (1704, 'purchase_date', IA5String),
        (1706, 'original_purchase_date', IA5String),
        (1708, 'expires_date', IA5String),
        (1719, 'is_in_intro_offer_period', Integer),
        (1712, 'cancellation_date', IA5String),
        (1711, 'web_order_line_item_id', Integer)
    }

    class InAppAttributeType(Integer):
        _map = {type_code: name for (type_code, name, _) in in_app_attribute_types}

    class InAppAttribute(Sequence):
        _fields = [
            ('type', InAppAttributeType),
            ('version', Integer),
            ('value', OctetString)
        ]

    class InAppPayload(SetOf):
        _child_spec = InAppAttribute

    in_app_attribute_types_to_class = {name: type_class for _, name, type_class in in_app_attribute_types}
    in_apps_parsed = []

    for in_app_data in in_apps:
      in_app = {}
      for attr in InAppPayload.load(in_app_data.native):
        attr_type = attr['type'].native
        if attr_type in in_app_attribute_types_to_class:
          in_app[attr_type] = in_app_attribute_types_to_class[attr_type].load(attr['value'].native).native
      in_apps_parsed.append(in_app)

    print(in_apps_parsed)

    return {
        "result":True,
        "receipt":in_apps_parsed
    }
