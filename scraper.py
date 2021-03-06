# Parsing HTML
from bs4 import BeautifulSoup
# Submitting forms
from selenium import webdriver
# To format date in the required format
import datetime
# To parse a string into a date
import dateutil.parser
# To convert relative URLs into absolute URLs
from urlparse import urljoin
# To write to SQLite database
import scraperwiki
# To sleep
import time

# Consts
url = "http://datracker.portstephens.nsw.gov.au/"

driver = webdriver.Firefox()

# Get the first page with agreement.
driver.get(url)

# Set the cookie to skip the agreement.
driver.add_cookie({"name": "User", "value": "accessAllowed-MasterView=True"})

# Refresh the page.
driver.refresh()

# Find the first "This Week" link. That is "Applications Submitted".
this_week_link = driver.find_elements_by_link_text("This Week")[0]
this_week_link.click()

# Wait 5 seconds to ensure all is loaded.
time.sleep(5)

# Find the "Records per page" selector and select the last value (100).
records_per_page = driver.find_elements_by_name("applicationsTable_length")[0]
records_per_page.find_elements_by_tag_name("option")[-1].click()

# Wait 5 seconds to ensure all is loaded.
time.sleep(5)

bsd = BeautifulSoup(driver.page_source)

# Get results list
result = bsd.find_all(id="applicationsTable")[0]
children = result.findChildren("tr", {'role': 'row'})

for child in children[1:]:

    da = {}

    # Required fields

    """
    The ID that the council has given the planning application.
    This also must be the unique key for this data set.
    """
    council_reference = ""

    a = child.findChildren("a")[0]
    relative_link = a.get("href")
    council_reference = relative_link.split("/")[1]

    da["council_reference"] = council_reference

    """
    The physical address that this application relates to. This will be
    geocoded so doesn't need to be a specific format but obviously the more
    explicit it is the more likely it will be successfully geo-coded. If the
    original address did not include the state (e.g. "QLD") at the end, then
    add it.
    """
    address = ""

    elems = child.findChildren("td")

    # The 4th element has the address and the description split by a line break.
    content = list(elems[4].children)

    address = content[0]

    da["address"] = address.strip()

    """
    A text description of what the planning application seeks to carry out.
    """

    description = content[-1]

    da["description"] = description.text

    """
    URL that provides more information about the planning application.
    This should be a persistent URL that preferably is specific to this
    particular application. In many cases councils force users to click
    through a license to access planning application. In this case be
    careful about what URL you provide. Test clicking the link in a browser
    that hasn't established a session with the council's site to ensure users
    of PlanningAlerts will be able to click the link and not be presented with
    an error.
    """

    info_url = urljoin(url, "Application/" + relative_link)

    da["info_url"] = info_url

    """
    A URL where users can provide a response to council about this particular
    application.
    As in info_url this needs to be a persistent URL and should be specific
    to this particular application if possible. Email mailto links are also
    valid in this field.
    """

    da["comment_url"] = info_url

    """
    The date that your scraper is collecting this data (i.e. now). Should
    be in ISO 8601 format.
    Use the following Ruby code: Date.today.to_s
    """
    date_scraped = datetime.date.today().isoformat()
    da["date_scraped"] = date_scraped

    # Optional fields

    """
    The date this application was received by council. Should be in ISO 8601
    format.
    """
    date_received = ""

    lodged_date = dateutil.parser.parse(
        elems[3].text, default=datetime.date.today(), dayfirst=True)
    date_received = lodged_date.isoformat()

    da["date_received"] = date_received

    """
    The date from when public submissions can be made about this application.
    Should be in ISO 8601 format.
    """
    on_notice_from = ""

    """
    The date until when public submissions can be made about this application.
    Should be in ISO 8601 format.
    """
    on_notice_to = ""

    print da
    scraperwiki.sqlite.save(unique_keys=['council_reference'], data=da)
