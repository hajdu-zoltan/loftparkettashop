from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
import requests
import datetime
from typing import List
import time


class SzamlazzItem:
    name = None
    quantity = None
    quantity_unit = None
    unit_price_net = None
    vat_key = None
    price_net = None
    price_vat = None
    price_brut = None
    comment = None
    
    def __init__(self, name, quantity, unit_price_net, price_net, price_vat, price_brut, quantity_unit="db", vat_key=27, comment=""):
        self.name = name
        self.quantity = quantity
        self.quantity_unit = quantity_unit
        self.unit_price_net = unit_price_net
        self.vat_key = vat_key
        self.price_net = price_net
        self.price_vat = price_vat
        self.price_brut = price_brut
        self.comment = comment


class SzamlazzInfo:
    creation_date = None
    payment_type = None
    valuta = None
    order_number = None
    seller_email = None
    email_content = None
    buyer_name = None
    buyer_post_code = None
    buyer_city = None
    buyer_address = None
    buyer_email = None
    buyer_tax_number = None
    buyer_phone = None
    comment = None
    adoalany = None
    items: List[SzamlazzItem] = None
    
    def __init__(self, payment_type=None, order_number=None, seller_email=None, buyer_name=None, buyer_post_code=None, buyer_city=None, buyer_address=None,
                 buyer_email=None, buyer_tax_number=None, valuta="HUF", email_content="", buyer_phone="", comment="", adoalany=1):
        
        self.creation_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.payment_type = payment_type
        self.valuta = valuta
        self.order_number = order_number
        self.seller_email = seller_email
        self.email_content = email_content
        self.buyer_name = buyer_name
        self.buyer_post_code = buyer_post_code
        self.buyer_city = buyer_city
        self.buyer_address = buyer_address
        self.buyer_email = buyer_email
        self.buyer_tax_number = buyer_tax_number
        self.buyer_phone = buyer_phone
        self.comment = comment
        self.adoalany = adoalany
        self.items: List[SzamlazzItem] = []
        

class SzamlazzhuModule:
    agent_key = None
    e_invoice = True
    
    def __init__(self, agent_key, e_invoice=True):
        self.agent_key = agent_key
        self.e_invoice = e_invoice
        
    def create_invoice(self, szamlazz_info: SzamlazzInfo):
        invoice_dict = self.generate_invoice_dict(szamlazz_info)
        invoice_xml = self.generate_xml(invoice_dict)

        files = {'action-xmlagentxmlfile': invoice_xml}
        response = requests.post('https://www.szamlazz.hu/szamla/', files=files)
        
        response_result = self.process_invoice_response(response)
        
        return response_result
        
    def generate_invoice_dict(self, szamlazz_info: SzamlazzInfo):
        invoice_dict = dict()
        invoice_dict['beallitasok'] = {'szamlaagentkulcs': self.agent_key,
                                       'eszamla': 'true' if self.e_invoice else 'false',
                                       'szamlaLetoltes': 'false',
                                       'valaszVerzio': 2}
        
        invoice_dict['fejlec'] = {'keltDatum': szamlazz_info.creation_date,
                                  'teljesitesDatum': szamlazz_info.creation_date,
                                  'fizetesiHataridoDatum': szamlazz_info.creation_date,
                                  'fizmod': szamlazz_info.payment_type,
                                  'penznem': szamlazz_info.valuta,
                                  'szamlaNyelve': 'hu',
                                  'rendelesSzam': szamlazz_info.order_number,
                                  'fizetve': 1}
                        
        invoice_dict['elado'] = {'emailReplyto': szamlazz_info.seller_email,
                                 'emailTargy': 'Számla a vásárlásáról',
                                 'emailSzoveg': szamlazz_info.email_content}
                        
        invoice_dict['vevo'] = {'nev': szamlazz_info.buyer_name,
                                'irsz': szamlazz_info.buyer_post_code,
                                'telepules': szamlazz_info.buyer_city,
                                'cim': szamlazz_info.buyer_address,
                                'email': szamlazz_info.buyer_email,
                                'sendEmail': 'true' if szamlazz_info.buyer_email is not None and szamlazz_info.buyer_email != "" else 'false'}

        # Ha nem magánszemélyről van szó, akkor hozzáfűzi az adószámot
        if szamlazz_info.adoalany != -1:
            invoice_dict['vevo'].update({
                                'adoszam': szamlazz_info.buyer_tax_number,
                                'telefonszam': szamlazz_info.buyer_phone,
                                'megjegyzes': szamlazz_info.comment
                                })
        # Ha magánszemélyről van szó, akkor hozzáfűzi, hogy nincs adószáma a vevőnek
        else:
            invoice_dict['vevo'].update({
                'adoalany': szamlazz_info.adoalany,
                'telefonszam': szamlazz_info.buyer_phone,
                'megjegyzes': szamlazz_info.comment
            })
        
        items = list()
        for item in szamlazz_info.items:
            items.append({'megnevezes': item.name,
                          'mennyiseg': item.quantity,
                          'mennyisegiEgyseg': item.quantity_unit,
                          'nettoEgysegar': item.unit_price_net,
                          'afakulcs': item.vat_key,
                          'nettoErtek': item.price_net,
                          'afaErtek': item.price_vat,
                          'bruttoErtek': item.price_brut,
                          'megjegyzes': item.comment})
        invoice_dict['tetelek'] = items
        
        invoice_tree = self.dict_to_xml('xmlszamla', invoice_dict)
        invoice_tree.set('xmlns', 'http://www.szamlazz.hu/xmlszamla')
        invoice_tree.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        invoice_tree.set('xsi:schemaLocation', 'http://www.szamlazz.hu/xmlszamla https://www.szamlazz.hu/szamla/docs/xsds/agent/xmlszamla.xsd')

        return invoice_tree

    def generate_xml(self, to_xml):
        xml = (ET.tostring(to_xml, encoding='UTF-8', method='xml')).decode("utf-8")
        return xml

    def process_invoice_response(self, response):
        root = ET.fromstring(response.text)
    
        if root.find('{http://www.szamlazz.hu/xmlszamlavalasz}sikeres').text == 'true':
            invoice_creation_succeeded = True
        else:
            invoice_creation_succeeded = False
    
        if invoice_creation_succeeded is True:
            invoice_number = root.find('{http://www.szamlazz.hu/xmlszamlavalasz}szamlaszam').text
            invoice_url = root.find('{http://www.szamlazz.hu/xmlszamlavalasz}vevoifiokurl').text
        
            print(f"Számla készítés sikeres: {invoice_creation_succeeded}")
            print(f"Számla szám: {invoice_number}")
            print(f"Számla elérési URL: {invoice_url}")
            return [invoice_creation_succeeded, invoice_number, invoice_url]
        else:
            invoice_error_message = root.find('{http://www.szamlazz.hu/xmlszamlavalasz}hibauzenet').text
            print(f"Valami hiba történt a számla készítésekor! ({invoice_error_message})")
            return [invoice_creation_succeeded, invoice_error_message]

    def create_receipt(self, szamlazz_info: SzamlazzInfo):
        receipt_dict = self.generate_receipt_dict(szamlazz_info)
        receipt_xml = self.generate_xml(receipt_dict)
        
        files = {'action-szamla_agent_nyugta_create': receipt_xml}
        response = requests.post('https://www.szamlazz.hu/szamla/', files=files)
        
        response_result = self.process_receipt_response(response)
        
        return response_result
    
    def generate_receipt_dict(self, szamlazz_info: SzamlazzInfo):
        receipt_dict = dict()
        receipt_dict['beallitasok'] = {'szamlaagentkulcs': self.agent_key,
                                       'pdfLetoltes': 'false'}

        receipt_dict['fejlec'] = {'elotag': 'NYGTA',
                                  'fizmod': szamlazz_info.payment_type,
                                  'penznem': szamlazz_info.valuta
                                  }

        items = list()
        for item in szamlazz_info.items:
            items.append({'megnevezes': item.name,
                          'mennyiseg': item.quantity,
                          'mennyisegiEgyseg': item.quantity_unit,
                          'nettoEgysegar': item.unit_price_net,
                          'netto': item.price_net,
                          'afakulcs': item.vat_key,
                          'afa': item.price_vat,
                          'brutto': item.price_brut})
        receipt_dict['tetelek'] = items

        receipt_tree = self.dict_to_xml('xmlnyugtacreate', receipt_dict)
        receipt_tree.set('xmlns', 'http://www.szamlazz.hu/xmlnyugtacreate')
        receipt_tree.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        receipt_tree.set('xsi:schemaLocation',
                         'http://www.szamlazz.hu/xmlnyugtacreate https://www.szamlazz.hu/szamla/docs/xsds/agent/xmlnyugtacreate.xsd')

        return receipt_tree

    def process_receipt_response(self, response):
        root = ET.fromstring(response.text)
    
        if root.find('{http://www.szamlazz.hu/xmlnyugtavalasz}sikeres').text == 'true':
            receipt_creation_succeeded = True
        else:
            receipt_creation_succeeded = False
    
        if receipt_creation_succeeded is True:
            receipt_number = root.find('{http://www.szamlazz.hu/xmlnyugtavalasz}nyugta')\
                .find('{http://www.szamlazz.hu/xmlnyugtavalasz}alap')\
                .find('{http://www.szamlazz.hu/xmlnyugtavalasz}nyugtaszam').text
        
            print(f"Nyugta készítés sikeres: {receipt_creation_succeeded}")
            print(f"Nyugta szám: {receipt_number}")
            return [receipt_creation_succeeded, receipt_number]
        else:
            receipt_error_message = root.find('{http://www.szamlazz.hu/xmlnyugtavalasz}hibauzenet').text
            print(f"Valami hiba történt a nyugta készítésekor! ({receipt_error_message})")
            return [receipt_creation_succeeded, receipt_error_message]
        
    def send_receipt_to_customer(self, customer_email, receipt_number, email_subject, email_reply_to, email_text):
        receipt_send = dict()
        receipt_send['beallitasok'] = {'szamlaagentkulcs': self.agent_key}
        receipt_send['fejlec'] = {'nyugtaszam': receipt_number}
        receipt_send['emailKuldes'] = {
            "email": customer_email,
            "emailReplyto": email_reply_to,
            "emailTargy": email_subject,
            "emailSzoveg": email_text
        }

        receipt_send_tree = self.dict_to_xml('xmlnyugtasend', receipt_send)
        receipt_send_tree.set('xmlns', 'http://www.szamlazz.hu/xmlnyugtasend')
        receipt_send_tree.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        receipt_send_tree.set('xsi:schemaLocation', 'http://www.szamlazz.hu/xmlnyugtasend https://www.szamlazz.hu/docs/xsds/nyugtasend/xmlnyugtasend.xsd')

        receipt_send_xml = self.generate_xml(receipt_send_tree)

        files = {'action-szamla_agent_nyugta_send': receipt_send_xml}
        response = requests.post('https://www.szamlazz.hu/szamla/', files=files)

        return response

    def get_tax_payer_information(self, tax_number):
        tax_payer_dict = dict()
        tax_payer_dict['beallitasok'] = {'szamlaagentkulcs': self.agent_key}
        tax_payer_dict['torzsszam'] = tax_number

        tax_payer = self.dict_to_xml('xmltaxpayer', tax_payer_dict)
        tax_payer.set('xmlns', 'http://www.szamlazz.hu/xmltaxpayer')
        tax_payer.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        tax_payer.set('xsi:schemaLocation', 'http://www.szamlazz.hu/xmltaxpayer https://www.szamlazz.hu/szamla/docs/xsds/agent/xmltaxpayer.xsd')

        tax_xml = self.generate_xml(tax_payer)

        files = {'action-szamla_agent_taxpayer': tax_xml}
        
        result = {}
        while len(result) == 0:
            response = requests.post('https://www.szamlazz.hu/szamla/', files=files)
            result = self.process_tax_information(response)
            if len(result) == 0:
                print("Érvénytelen válasz érkezett a NAV Onlinetól!")
                time.sleep(5)
        return result
        
    def process_tax_information(self, response):
        root = ET.fromstring(response.text)

        tax_data = dict()

        for item in root.iter():
            if item.tag == "{http://schemas.nav.gov.hu/OSA/2.0/api}taxpayerValidity" or item.tag == "{http://schemas.nav.gov.hu/OSA/3.0/api}taxpayerValidity":
                if item.text == 'true':
                    tax_data["valid"] = True
                elif item.text == 'false':
                    tax_data["valid"] = False
                    return tax_data
    
            if item.tag == "{http://schemas.nav.gov.hu/OSA/2.0/api}taxpayerName" or item.tag == "{http://schemas.nav.gov.hu/OSA/3.0/api}taxpayerName":
                tax_data["name"] = item.text
            
            if item.tag == "{http://schemas.nav.gov.hu/OSA/3.0/api}taxpayerAddressList":
                # Megkeressük a székhelyet a címlistában
                hq_found = False
                for address in item:
                    for address_item in address:
                        if address_item.tag == "{http://schemas.nav.gov.hu/OSA/3.0/api}taxpayerAddressType" and address_item.text == 'HQ':
                            hq_found = True
                        if hq_found is True and address_item.tag == "{http://schemas.nav.gov.hu/OSA/3.0/api}taxpayerAddress":
                            for address_details in address_item:
                                if address_details.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}postalCode" or address_details.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}postalCode":
                                    tax_data["post_code"] = address_details.text
                                if address_details.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}city" or address_details.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}city":
                                    tax_data["city"] = address_details.text
                                if address_details.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}streetName" or address_details.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}streetName":
                                    tax_data["address"] = address_details.text
                                if address_details.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}publicPlaceCategory" or address_details.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}publicPlaceCategory":
                                    tax_data["address"] += " " + address_details.text
                                if address_details.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}number" or address_details.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}number":
                                    tax_data["address"] += " " + address_details.text
                                if (address_details.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}building" or address_details.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}building")\
                                        and address_details.text is not None:
                                    tax_data["address"] += "/" + address_details.text
                    if hq_found is True:
                        break
            
            if item.tag == "{http://schemas.nav.gov.hu/OSA/2.0/data}taxpayerId" or item.tag == "{http://schemas.nav.gov.hu/OSA/3.0/base}taxpayerId":
                tax_data["tax_number"] = item.text

        return tax_data


    def dict_to_xml(self, tag, d):
        elem = Element(tag)
        for key, val in d.items():
            # create an Element
            # class object
            if isinstance(val, dict):
                # dict_to_xml(key, val)
                elem.append(self.dict_to_xml(key, val))
            elif isinstance(val, list):
                if key == "tetelek":
                    tetelek = Element("tetelek")
                    for item in val:
                        tetelek.append(self.dict_to_xml("tetel", item))
                    elem.append(tetelek)
            else:
                child = Element(key)
                child.text = str(val)
                elem.append(child)
    
        return elem
