#################################
##### Name: Chengcheng Wang
##### Uniqname: chchwang@umich.edu
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_FILENAME = "proj2_nps.json"
CACHE_DICT = {}
BASIC_URL="https://www.nps.gov"

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings=[]
    connector = '_'
    for k in params.keys():
        param_strings.append(f"{k}_{params[k]}")
    param_strings.sort()
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key

def make_request_with_cache(baseurl):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    CACHE_DICT = open_cache()
    if baseurl in CACHE_DICT.keys():
        print("Using CACHE")
        return CACHE_DICT[baseurl]
    else:
        print("Fetching")
        CACHE_DICT[baseurl]=requests.get(baseurl).text
        save_cache(CACHE_DICT)
        return CACHE_DICT[baseurl]

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category=category
        self.name=name
        self.address=address
        self.zipcode=zipcode
        self.phone=phone

    def info(self):
        return self.name+ " (" + self.category +")" + ": " + self.address + " " + self.zipcode



def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    BASIC_URL="https://www.nps.gov"
    response=make_request_with_cache(BASIC_URL)
    soup=BeautifulSoup(response, 'html.parser')

    state_listing_parent=soup.find(class_='dropdown-menu SearchBar-keywordSearch')
    state_listing=state_listing_parent.find_all('a')
    state_url_dict={}
    for i in state_listing:
        state_name=i.text.lower().strip()
        state_url=BASIC_URL+i['href']
        state_url_dict[state_name]=state_url
    return state_url_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response1=make_request_with_cache(site_url)
    soup=BeautifulSoup(response1, 'html.parser')
    instance_listing_parent=soup.find(class_="Hero-titleContainer clearfix")
    instance_name=instance_listing_parent.find('a').text.strip()
    instance_category=instance_listing_parent.find('span').text.strip()
    footer_parent=soup.find(class_='ParkFooter-contact')
    instance_address=footer_parent.find(itemprop='addressLocality').text.strip()+", "+footer_parent.find(itemprop='addressRegion').text.strip()
    instance_ZIP_code=footer_parent.find(itemprop='postalCode').text.strip()
    instance_phone=footer_parent.find(itemprop='telephone').text.strip()

    National_Site=NationalSite(name=instance_name,category=instance_category,address=instance_address,zipcode=instance_ZIP_code, phone=instance_phone)
    return National_Site


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    response2=make_request_with_cache(state_url)
    soup=BeautifulSoup(response2, 'html.parser')
    park_listing_parent=soup.find_all('div', class_="col-md-9 col-sm-9 col-xs-12 table-cell list_left")
    park_list=[]
    for i in park_listing_parent:
        park_listing=i.find_all('a')
        park_url=BASIC_URL+park_listing[0]['href']+"index.htm"
        park_list.append(get_site_instance(park_url))
    return park_list
    

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    BASE_URL="http://www.mapquestapi.com/search/v2/radius"
    params = {"key": secrets.API_KEY, "origin": site_object.zipcode, "radius": 10,
              "maxMatches": 10, "ambiguities": "ignore", "outFormat": "json"}

    CACHE_DICT=open_cache()
    if site_object.zipcode in CACHE_DICT.keys():
        print("Using Cache")
        response3 = CACHE_DICT[site_object.zipcode]
    else:
        print("Fetching")
        response3=requests.get(BASE_URL,params=params).json()
        CACHE_DICT[site_object.zipcode]=response3
    return response3


if __name__ == "__main__":
    states_dict=build_state_url_dict()
    while True:
        State=input('Enter a state name (e.g. Michigan, michigan) or "exit":').lower()
        if State=='exit':
            break
        else:
            if State.lower() in states_dict.keys():
                state_url = states_dict[State]
                sites_list = get_sites_for_state(state_url)
                print('-'*34)
                print("List of national sites in "+State.lower())
                print('-'*34)
                for i in range(len(sites_list)):
                    print('[', i+1, ']',sites_list[i].info())            
            else:
                print("[Error]: Enter proper state name")
                continue

            temp=0
            while True:
                input_number = input('Choose the number for detail search or "exit" or "back"\n:').lower()
                if input_number == 'exit':
                    temp=1
                    break
                elif input_number == 'back':
                    break
                elif input_number.isnumeric():
                    if 0 < int(input_number) <= len(sites_list):
                        instance = sites_list[int(input_number)-1]
                        nearbyplaces=get_nearby_places(instance)["searchResults"]
                        print('-'*34)
                        print(f'Places near {instance.name}')
                        print('-'*34)

                        for nearbyplaces in nearbyplaces:
                            name = nearbyplaces['name']
                            if nearbyplaces['fields']['address']=='':
                                address='no address'
                            else:
                                address=nearbyplaces['fields']['address']
                            if nearbyplaces['fields']['city']=='':
                                city='no city'
                            else:
                                city=nearbyplaces['fields']['address']
                            if nearbyplaces['fields']['group_sic_code_name']=='':
                                category = 'no category'
                            else:
                                category=nearbyplaces['fields']['group_sic_code_name']
                            print(f"- {name} ({category}): {address}, {city}")
                    else:
                        print('[Error] Invalid input')
                else:
                    print('[Error] Enter proper state name \n')

                