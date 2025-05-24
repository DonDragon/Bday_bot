import vobject

def parse_vcf(file_path):
    birthdays = []
    with open(file_path, 'r', encoding='utf-8') as f:
        vcard_data = f.read()
        for vcard in vobject.readComponents(vcard_data):
            name = vcard.fn.value
            if hasattr(vcard, 'bday'):
                date = vcard.bday.value.strftime('%d.%m')
                birthdays.append((name, date))
    return birthdays
