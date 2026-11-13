
from collectors.indiamart_collector import IndiaMartCollector

collector = IndiaMartCollector()

try:
    products = collector.search_products("HDPE Industrial Pipe")
    print(products)

except RuntimeError as error:
    print("Access configuration:", error)

except NotImplementedError as error:
    print("Integration status:", error)

finally:
    collector.close()
