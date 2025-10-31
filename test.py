import pyvisa

rm = pyvisa.ResourceManager()
visaList = rm.list_resources()
print(visaList)
