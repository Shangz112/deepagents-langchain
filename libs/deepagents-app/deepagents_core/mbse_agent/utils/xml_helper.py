from lxml import etree

NS_MAP = {
    'uml': 'http://www.eclipse.org/uml2/5.0.0/UML',
    'xmi': 'http://www.omg.org/spec/XMI/2.1',
    'sysml': 'http://www.omg.org/spec/SysML/20100301/SysML-profile'
}

def get_xpath(element, path: str):
    return element.xpath(path, namespaces=NS_MAP)
